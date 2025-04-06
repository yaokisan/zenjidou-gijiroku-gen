import os
from dotenv import load_dotenv

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
