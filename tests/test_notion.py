#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from notion_client import Client
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からNotionの認証情報を取得
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_PAGE_ID = os.environ.get("NOTION_DATABASE_ID")  # 変数名は元のまま使用

def test_notion_page_access():
    """NotionページIDの検証"""
    if not NOTION_API_KEY:
        logger.error("NOTION_API_KEYが設定されていません。")
        return False
    
    if not NOTION_PAGE_ID:
        logger.error("NOTION_PAGE_IDが設定されていません。")
        return False
    
    # Notionクライアントの初期化
    notion = Client(auth=NOTION_API_KEY)
    
    # テスト1: 元のページID（ハイフン付き/なし）でクエリを試みる
    page_id = NOTION_PAGE_ID
    logger.info(f"テスト対象のページID: {page_id}")
    
    # ハイフンなしの場合はハイフン付きに変換してみる（32文字の場合）
    if '-' not in page_id and len(page_id) == 32:
        formatted_id = f"{page_id[0:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:32]}"
        logger.info(f"ハイフン付き形式のページID: {formatted_id}")
        
        try:
            # ハイフン付きIDでの取得を試みる
            page_info = notion.pages.retrieve(page_id=formatted_id)
            logger.info(f"✅ ページへのアクセス成功（ハイフン付き）: {page_info.get('url', 'No URL')}")
            return True
        except Exception as e:
            logger.error(f"ページへのアクセス失敗（ハイフン付き）: {str(e)}")
    
    # 元のIDでの取得を試みる
    try:
        page_info = notion.pages.retrieve(page_id=page_id)
        logger.info(f"✅ ページへのアクセス成功（元のID）: {page_info.get('url', 'No URL')}")
        return True
    except Exception as e:
        logger.error(f"ページへのアクセス失敗（元のID）: {str(e)}")
        
    # ハイフンがある場合は除去してみる
    if '-' in page_id:
        clean_id = page_id.replace('-', '')
        logger.info(f"ハイフンなし形式のページID: {clean_id}")
        
        try:
            page_info = notion.pages.retrieve(page_id=clean_id)
            logger.info(f"✅ ページへのアクセス成功（ハイフンなし）: {page_info.get('url', 'No URL')}")
            return True
        except Exception as e:
            logger.error(f"ページへのアクセス失敗（ハイフンなし）: {str(e)}")
    
    return False

def test_create_child_page():
    """親ページの下に子ページを作成するテスト"""
    if not NOTION_API_KEY or not NOTION_PAGE_ID:
        logger.error("NOTION_API_KEYまたはNOTION_PAGE_IDが設定されていません。")
        return False
    
    notion = Client(auth=NOTION_API_KEY)
    page_id = NOTION_PAGE_ID
    
    # ハイフンなしの場合はハイフン付きに変換してみる（32文字の場合）
    if '-' not in page_id and len(page_id) == 32:
        formatted_id = f"{page_id[0:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:32]}"
        try_ids = [formatted_id, page_id]
    elif '-' in page_id:
        clean_id = page_id.replace('-', '')
        try_ids = [page_id, clean_id]
    else:
        try_ids = [page_id]
    
    # 各IDフォーマットで試す
    for try_id in try_ids:
        logger.info(f"ページID {try_id} で子ページ作成を試みます...")
        try:
            # テストページの作成
            new_page = notion.pages.create(
                parent={"page_id": try_id},
                properties={
                    "title": {
                        "title": [{"text": {"content": "テスト - 親ページテスト用"}}]
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
                                    "text": {"content": "これはテスト用のページです。"}
                                }
                            ]
                        }
                    }
                ]
            )
            logger.info(f"✅ 子ページ作成成功: {new_page.get('url', 'No URL')}")
            return True
        except Exception as e:
            logger.error(f"子ページ作成失敗 (ID: {try_id}): {str(e)}")
    
    return False

if __name__ == "__main__":
    print("=== Notion API ページアクセステスト ===")
    
    # 設定値の表示
    masked_api_key = "********" + NOTION_API_KEY[-4:] if NOTION_API_KEY else "未設定"
    print(f"NOTION_API_KEY: {masked_api_key}")
    print(f"NOTION_PAGE_ID: {NOTION_PAGE_ID}")
    
    # ページアクセステスト
    print("\n1. ページアクセステスト")
    if test_notion_page_access():
        print("✅ ページへのアクセステスト: 成功")
    else:
        print("❌ ページへのアクセステスト: 失敗")
    
    # 子ページ作成テスト
    print("\n2. 子ページ作成テスト")
    if test_create_child_page():
        print("✅ 子ページ作成テスト: 成功")
    else:
        print("❌ 子ページ作成テスト: 失敗")
    
    print("\n※ 問題が発生した場合は以下を確認してください：")
    print("1. Notionインテグレーションとページが共有されているか")
    print("2. APIキーが正しいか")
    print("3. ページIDの形式が正しいか（ハイフンあり/なしは自動的に対応します）") 