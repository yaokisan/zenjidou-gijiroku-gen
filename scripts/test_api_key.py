import os
from dotenv import load_dotenv
from notion_client import Client

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からNotion APIキーを取得
notion_api_key = os.environ.get("NOTION_API_KEY")

# APIキーを部分的に表示（セキュリティのため）
if notion_api_key:
    masked_key = "********" + notion_api_key[-4:] if len(notion_api_key) > 4 else "****"
    print(f"Notion API Key: {masked_key}")
    print(f"Key length: {len(notion_api_key)} characters")
else:
    print("NOTION_API_KEY not found in environment variables")
    exit(1)

# 簡単なAPIテスト
try:
    print("\n=== API接続テスト ===")
    notion = Client(auth=notion_api_key)
    response = notion.users.me()
    print("✅ APIキーは有効です！")
    print(f"ログイン中のユーザー: {response.get('name', '不明なユーザー')}")
    
    # 使用可能なページを取得してみる
    print("\n=== アクセス可能なページのテスト ===")
    # テスト用のページID (settings.notion_parent_page_id)
    test_page_id = os.environ.get("NOTION_DATABASE_ID")
    if test_page_id:
        try:
            # ハイフンが含まれていない場合は追加
            if '-' not in test_page_id and len(test_page_id) == 32:
                formatted_id = f"{test_page_id[0:8]}-{test_page_id[8:12]}-{test_page_id[12:16]}-{test_page_id[16:20]}-{test_page_id[20:32]}"
                test_page_id = formatted_id
            
            print(f"テスト対象のページID: {test_page_id}")
            page_info = notion.pages.retrieve(page_id=test_page_id)
            print(f"✅ ページアクセス成功！ URL: {page_info.get('url', 'URLなし')}")
            
            # ページのアクセス権を確認
            print("\n=== ページのアクセス権テスト ===")
            try:
                # テスト用の子ページを作成してみる
                new_page = notion.pages.create(
                    parent={"page_id": test_page_id},
                    properties={
                        "title": {
                            "title": [{"text": {"content": "APIテスト - 権限確認用"}}]
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
                                        "text": {"content": "これはAPIキーとページ権限のテストです。"}
                                    }
                                ]
                            }
                        }
                    ]
                )
                print(f"✅ 子ページ作成成功！ URL: {new_page.get('url', 'URLなし')}")
                print("✅ ページへの書き込み権限があります。")
            except Exception as page_create_error:
                print(f"❌ 子ページ作成失敗: {str(page_create_error)}")
                print("❌ ページへの書き込み権限がないか、共有設定に問題があります。")
        except Exception as page_error:
            print(f"❌ ページアクセス失敗: {str(page_error)}")
            print("👉 インテグレーションとページが共有されているか確認してください。")
    else:
        print("❌ テスト用のページIDが設定されていません。")
    
except Exception as e:
    print(f"❌ APIキーテスト失敗: {str(e)}")
    print("👉 Notionインテグレーション設定でAPIキーを確認してください。") 