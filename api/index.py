# api/index.py
from app import create_app

# Vercelがこの 'app' 変数を探して実行します
app = create_app()

# 開発環境でのローカル実行用（Vercelでは不要だが、ローカルテスト用に残しておいても良い）
if __name__ == '__main__':
    app.run(debug=True) 