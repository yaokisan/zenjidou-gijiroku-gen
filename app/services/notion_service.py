#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from notion_client import Client

# 環境変数からNotion APIキーを取得
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")

# ロガーの設定
logger = logging.getLogger(__name__)

def create_notion_page(title, content, notta_title, notta_creation_time, parent_page_id=None):
    """Notionページを作成して議事録を保存する
    
    Args:
        title (str): 生成された議事録のタイトル
        content (str): 生成された議事録の内容
        notta_title (str): 元のNottaタイトル
        notta_creation_time (datetime): 元のNotta作成時間
        parent_page_id (str, optional): 親ページID (指定がない場合はワークスペースのトップレベルに作成)
        
    Returns:
        dict: 作成されたNotionページの情報
            - id: ページID
            - url: ページURL
    """
    try:
        # Notion APIキーが設定されているか確認
        if not NOTION_API_KEY:
            logger.error("NOTION_API_KEYが設定されていません")
            raise ValueError("Notion APIキーが設定されていません")
        
        # Notionクライアントの初期化
        notion = Client(auth=NOTION_API_KEY)
        
        # 作成日時の整形
        formatted_date = ""
        if notta_creation_time:
            if isinstance(notta_creation_time, datetime):
                formatted_date = notta_creation_time.strftime("%Y年%m月%d日")
            else:
                formatted_date = str(notta_creation_time)
        
        # ページタイトルの整形（日付を追加）
        page_title = f"{title} - {formatted_date}" if formatted_date else title
        
        # 親ページの設定
        parent = {}
        if parent_page_id:
            # ページIDの処理: ハイフンが含まれていない場合は追加する（32文字の場合）
            if '-' not in parent_page_id and len(parent_page_id) == 32:
                page_id = f"{parent_page_id[0:8]}-{parent_page_id[8:12]}-{parent_page_id[12:16]}-{parent_page_id[16:20]}-{parent_page_id[20:32]}"
            else:
                page_id = parent_page_id
            
            logger.info(f"Notion親ページID: {page_id}")
            
            # ページIDとして設定
            parent = {"page_id": page_id}
            logger.info(f"使用するNotionページID: {page_id}")
        else:
            # 親ページが指定されていない場合はワークスペースのトップレベルに作成
            parent = {"type": "workspace", "workspace": True}
            logger.info("親ページIDが指定されていないため、ワークスペーストップレベルに作成します")
        
        # ページプロパティの設定
        properties = {
            "title": {
                "title": [{"text": {"content": page_title}}]
            }
        }
        
        # 最初のメタデータブロックを定義
        initial_blocks = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "元の録音タイトル: " + notta_title
                            },
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
                            "text": {
                                "content": "生成日時: " + datetime.now().strftime("%Y年%m月%d日 %H:%M")
                            }
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
        
        # === ステップ1: Notionページの初期作成 (本文ブロックなし) ===
        logger.info(f"Notionページの初期作成を開始... (parent: {parent})")
        try:
            create_response = notion.pages.create(
                parent=parent,
                properties=properties,
                children=initial_blocks # メタデータブロックのみ含める
            )
            
            page_id = create_response["id"]
            page_url = create_response.get("url", "")
            logger.info(f"Notionページを初期作成しました (ID: {page_id}): {page_url}")
        except Exception as e:
            logger.error(f"Notionページの初期作成に失敗しました: {str(e)}")
            # エラーの詳細を記録
            logger.error(f"エラーの詳細: {type(e).__name__}, {str(e)}")
            logger.error(f"使用したページID: {page_id if 'page_id' in locals() else parent_page_id}")
            logger.error(f"使用した親設定: {parent}")
            
            # 再試行せずにエラーを伝播
            raise
        
        # === ステップ2: 議事録本文をブロックリストに変換 ===
        content_blocks = []
        for line in content.split("\n"):
            if line.strip():  # 空行は無視しない（空のパラグラフにする）
                content_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line
                                }
                            }
                        ]
                    }
                })
            else:
                # 空行の場合は空のパラグラフを追加
                content_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": []
                    }
                })
        
        # === ステップ3: 本文ブロックを100個ずつのチャンクで追加 ===
        chunk_size = 100  # Notion APIの制限
        logger.info(f"本文ブロック ({len(content_blocks)}個) の追加を開始...")
        for i in range(0, len(content_blocks), chunk_size):
            chunk = content_blocks[i:i + chunk_size]
            logger.info(f"  ブロック {i+1} から {i+len(chunk)} を追加中...")
            try:
                append_response = notion.blocks.children.append(
                    block_id=page_id,
                    children=chunk
                )
                logger.info(f"  ブロック追加成功: {i+1} から {i+len(chunk)}")
            except Exception as append_error:
                logger.error(f"Notionページへのブロック追加中にエラーが発生しました: {append_error}")
                # エラーが発生した場合でも、ページの作成自体は成功している可能性があるため、
                # ページ情報は返しつつ、エラーを再raiseする
                raise append_error
        
        logger.info(f"全ての本文ブロックの追加が完了しました。")

        return {
            "id": page_id,
            "url": page_url
        }
    
    except Exception as e:
        logger.error(f"Notionページの作成・更新処理全体でエラーが発生しました: {str(e)}")
        raise 