#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
アプリケーション診断ツール：
実際のアプリケーションで使用される設定と環境変数を表示します
"""

import os
import sys
from dotenv import load_dotenv
from flask import Flask
from app import create_app, db
from app.models import Settings, MinutesHistory

# .envファイルから環境変数を読み込む
load_dotenv()

# Flaskアプリケーションを作成
app = create_app()

# 環境変数の確認
print("=== 環境変数の確認 ===")
notion_api_key = os.environ.get("NOTION_API_KEY")
notion_db_id = os.environ.get("NOTION_DATABASE_ID")

if notion_api_key:
    masked_key = "********" + notion_api_key[-4:] if len(notion_api_key) > 4 else "****"
    print(f"NOTION_API_KEY (.env): {masked_key}")
    print(f"NOTION_API_KEY 長さ: {len(notion_api_key)}")
else:
    print("❌ NOTION_API_KEY が設定されていません")

if notion_db_id:
    print(f"NOTION_DATABASE_ID (.env): {notion_db_id}")
else:
    print("❌ NOTION_DATABASE_ID が設定されていません")

# アプリケーションコンテキストで実行
with app.app_context():
    print("\n=== データベース設定の確認 ===")
    # 設定の確認
    settings = Settings.query.first()
    if settings:
        print(f"設定ID: {settings.id}")
        print(f"AI Provider: {settings.ai_provider}")
        print(f"Notion Parent Page ID (DB): {settings.notion_parent_page_id}")
        
        # 追加の整合性チェック
        stored_id = settings.notion_parent_page_id
        if stored_id:
            if '-' in stored_id:
                print(f"警告: 保存されているIDにハイフンが含まれています: {stored_id}")
            else:
                print(f"保存されているIDのフォーマット (ハイフンなし): {stored_id}")
                
            # ID長の確認
            if len(stored_id) == 32:
                print("IDの長さは正常 (32文字)")
                # 正しいフォーマットに変換
                formatted_id = f"{stored_id[0:8]}-{stored_id[8:12]}-{stored_id[12:16]}-{stored_id[16:20]}-{stored_id[20:32]}"
                print(f"変換後のID: {formatted_id}")
            else:
                print(f"❌ IDの長さが異常です: {len(stored_id)}文字")
    else:
        print("❌ 設定が存在しません")
    
    # Notion Service テスト
    print("\n=== Notion Service モックテスト ===")
    try:
        from app.services.notion_service import create_notion_page
        
        # create_notion_pageの呼び出し方法をログに出力
        import inspect
        sig = inspect.signature(create_notion_page)
        print(f"create_notion_page関数シグネチャ: {sig}")
        
        # settings.notion_parent_page_idが実際にどのように渡されるかシミュレーション
        print("\n実際の呼び出しシミュレーション:")
        parent_id = settings.notion_parent_page_id if settings else None
        print(f"parent_page_id = {parent_id}")
        
        if parent_id:
            # ページIDの処理: ハイフンが含まれていない場合は追加する（32文字の場合）
            if '-' not in parent_id and len(parent_id) == 32:
                page_id = f"{parent_id[0:8]}-{parent_id[8:12]}-{parent_id[12:16]}-{parent_id[16:20]}-{parent_id[20:32]}"
            else:
                page_id = parent_id
                
            print(f"処理後のページID: {page_id}")
            print(f"parentパラメータ: {{'page_id': '{page_id}'}}")
        
    except Exception as e:
        print(f"❌ Notion Service テストでエラー: {str(e)}")
    
    print("\n=== 最近の処理履歴 ===")
    try:
        # 最近の履歴を確認
        recent_history = MinutesHistory.query.order_by(MinutesHistory.id.desc()).limit(3).all()
        for history in recent_history:
            print(f"履歴ID: {history.id}")
            print(f"タイトル: {history.notta_title}")
            print(f"ステータス: {history.status}")
            print(f"エラーメッセージ: {history.error_message}")
            print("---")
    except Exception as e:
        print(f"❌ 履歴の取得でエラー: {str(e)}")
        
    print("\n=== 実際のルートにアクセスするコード ===")
    print("以下のコードを使ってwebhookルートをPythonから直接呼び出すことも可能です：")
    print("""
import requests
import json

# アプリのURL
url = "http://localhost:5002/webhook/notta"  # ポートは環境に合わせて変更

# テストデータ
data = {
    "content": "これはテスト用の文字起こしです。",
    "title": "テスト会議",
    "creation_time": "2023-04-05 12:00:00",
    "speakers": ["テスト話者1", "テスト話者2"]
}

# POSTリクエスト送信
response = requests.post(url, json=data)

# 結果の確認
print(f"ステータスコード: {response.status_code}")
print(f"レスポンス: {response.json()}")
""") 