#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import MinutesHistory, Settings
from app.services.ai_service import generate_minutes
from app.services.notion_service import create_notion_page
import os
from notion_client import Client

# Blueprintの作成
bp = Blueprint('webhook', __name__, url_prefix='/webhook')

@bp.route('/notta', methods=['POST'])
def notta_webhook():
    """Zapier経由でNottaからのWebhookを受け取るエンドポイント"""
    try:
        # リクエストデータのログ記録
        current_app.logger.info(f"Webhook received: {request.data}")
        
        # リクエストデータのJSONパース
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        # 必須フィールドの確認
        required_fields = ["content", "title"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error", 
                    "message": f"Missing required field: {field}"
                }), 400
        
        # 受信データの確認とログ記録（デバッグ用）
        current_app.logger.info(f"Received content length: {len(data.get('content', ''))}")
        current_app.logger.info(f"Received title: {data.get('title', '')}")
        current_app.logger.info(f"Received creation_time: {data.get('creation_time', 'Not provided')}")
        current_app.logger.info(f"Received speakers: {data.get('speakers', 'Not provided (will be extracted from content if available)')}")
        
        # Notta作成時間のパース (存在する場合、formatは "YYYY-MM-DD HH:MM:SS" を想定)
        notta_creation_time = None
        if "creation_time" in data and data["creation_time"]:
            try:
                notta_creation_time = datetime.strptime(data["creation_time"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                current_app.logger.warning(f"Invalid creation_time format: {data['creation_time']}")
        
        # 履歴レコードの作成
        history = MinutesHistory(
            notta_title=data["title"],
            notta_creation_time=notta_creation_time,
            raw_data=json.dumps(data),
            status="pending"
        )
        
        # データベースに保存
        db.session.add(history)
        db.session.commit()
        
        # 非同期で議事録生成処理を開始（本来はCeleryなどのタスクキューを使うべき）
        # ここでは簡易的に同期処理として実装
        process_minutes_generation(history.id)
        
        return jsonify({
            "status": "success", 
            "message": "Webhook received successfully",
            "history_id": history.id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


def process_minutes_generation(history_id):
    """議事録生成処理を実行する
    
    Args:
        history_id (int): 処理する履歴レコードのID
    """
    try:
        # 履歴レコードの取得
        history = MinutesHistory.query.get(history_id)
        if not history:
            current_app.logger.error(f"History record not found: {history_id}")
            return
        
        # 処理中に更新
        history.status = "processing"
        db.session.commit()
        
        # 設定の取得
        settings = Settings.query.first()
        if not settings:
            current_app.logger.error("Settings not found")
            history.status = "failed"
            history.error_message = "設定が見つかりません"
            db.session.commit()
            return
        
        # 保存されたデータの取得
        raw_data = history.get_raw_data_dict()
        
        # AIプロバイダーと使用モデルの設定
        ai_provider = settings.ai_provider
        ai_model = None
        
        if ai_provider == "google_gemini":
            ai_model = settings.google_gemini_model
        elif ai_provider == "anthropic_claude":
            ai_model = settings.anthropic_claude_model
        elif ai_provider == "openai_chatgpt":
            ai_model = settings.openai_chatgpt_model
        
        # AI設定をログに記録
        current_app.logger.info(f"Using AI provider: {ai_provider}, model: {ai_model}")
        
        # AIを使って議事録を生成
        ai_response = generate_minutes(
            raw_data.get("content", ""),
            raw_data.get("title", ""),
            raw_data.get("creation_time", ""),
            raw_data.get("speakers", []),  # speakersがない場合は空リストを渡す
            ai_provider,
            ai_model,
            anthropic_thinking_mode=settings.anthropic_thinking_mode if ai_provider == "anthropic_claude" else False
        )
        
        if not ai_response or not ai_response.get("minutes_content"):
            raise Exception("議事録生成に失敗しました")
        
        # 生成された議事録の内容とタイトルを取得
        minutes_content = ai_response.get("minutes_content", "")
        generated_title = ai_response.get("generated_title", history.notta_title)
        
        # Notionページの作成（テストで成功した処理方法を直接使用）
        current_app.logger.info(f"Notion連携を開始します:")
        current_app.logger.info(f"  タイトル: {generated_title}")
        current_app.logger.info(f"  親ページID: {settings.notion_parent_page_id}")
        
        # テストで成功したコードをそのまま使用
        try:
            # Notionクライアントの初期化（直接APIキーを使用）
            notion_api_key = os.environ.get("NOTION_API_KEY")
            notion = Client(auth=notion_api_key)
            current_app.logger.info(f"Notionクライアントを初期化しました")
            
            # 親ページIDの処理
            parent_id = settings.notion_parent_page_id
            if parent_id:
                # IDの処理: テストスクリプトと同じ方法
                if '-' not in parent_id and len(parent_id) == 32:
                    formatted_id = f"{parent_id[0:8]}-{parent_id[8:12]}-{parent_id[12:16]}-{parent_id[16:20]}-{parent_id[20:32]}"
                    page_id = formatted_id
                else:
                    page_id = parent_id
                
                current_app.logger.info(f"使用するページID: {page_id}")
                
                # ページのプロパティ定義
                new_page = notion.pages.create(
                    parent={"page_id": page_id},
                    properties={
                        "title": {
                            "title": [{"text": {"content": generated_title}}]
                        }
                    },
                    children=[
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": f"元の録音タイトル: {history.notta_title}"},
                                        "annotations": {"bold": True}
                                    }
                                ]
                            }
                        },
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}"}
                                    }
                                ]
                            }
                        },
                        {
                            "object": "block",
                            "type": "divider",
                            "divider": {}
                        }
                    ]
                )
                
                # ページIDとURLを取得
                page_id = new_page["id"]
                page_url = new_page.get("url", "")
                current_app.logger.info(f"Notionページを初期作成しました: {page_url}")
                
                # 議事録本文を追加
                chunks = []
                current_chunk = []
                for line in minutes_content.split("\n"):
                    block = {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": []
                        }
                    }
                    
                    if line.strip():
                        block["paragraph"]["rich_text"] = [
                            {
                                "type": "text",
                                "text": {"content": line}
                            }
                        ]
                    
                    current_chunk.append(block)
                    
                    # 100ブロックごとにチャンクを区切る
                    if len(current_chunk) >= 100:
                        chunks.append(current_chunk)
                        current_chunk = []
                
                # 最後のチャンクがあれば追加
                if current_chunk:
                    chunks.append(current_chunk)
                
                # チャンクごとにページに本文を追加
                for i, chunk in enumerate(chunks):
                    current_app.logger.info(f"本文ブロック {i+1}/{len(chunks)} を追加中...")
                    notion.blocks.children.append(
                        block_id=page_id,
                        children=chunk
                    )
                
                # 結果を返す
                notion_response = {
                    "id": page_id,
                    "url": page_url
                }
                notion_url = page_url
                current_app.logger.info(f"Notionページの作成が完了しました: {notion_url}")
            else:
                # 親ページIDがない場合
                current_app.logger.warning("親ページIDが設定されていません。Notionページの作成をスキップします。")
                notion_response = None
                notion_url = None
                
        except Exception as notion_error:
            current_app.logger.error(f"Notionページ作成中にエラーが発生しました: {str(notion_error)}")
            current_app.logger.error(f"エラーの種類: {type(notion_error).__name__}")
            
            # エラー情報を履歴に記録して再スロー
            history.status = "failed"
            history.error_message = f"Notion連携エラー: {str(notion_error)}"
            db.session.commit()
            raise notion_error
        
        # 履歴の更新
        history.processed_at = datetime.utcnow()
        history.ai_provider = ai_provider
        history.ai_model = ai_model
        history.generated_title = generated_title
        history.notion_page_url = notion_url
        history.status = "completed"
        db.session.commit()
        
        current_app.logger.info(f"Minutes generation completed for history_id: {history_id}")
        
    except Exception as e:
        current_app.logger.error(f"Error in minutes generation: {str(e)}")
        
        # エラー情報を保存
        try:
            history = MinutesHistory.query.get(history_id)
            if history:
                history.status = "failed"
                history.error_message = str(e)
                db.session.commit()
        except Exception as db_error:
            current_app.logger.error(f"Error updating history record: {str(db_error)}") 