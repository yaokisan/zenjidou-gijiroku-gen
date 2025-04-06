# api/index.py
import logging
import sys

# ★★★ 超初期ログ ★★★
print("--- API Index Start ---", file=sys.stderr)
logging.warning("--- API Index Logging Start ---")

from app import create_app

# ★★★ アプリ作成前ログ ★★★
print("--- Before create_app() call ---", file=sys.stderr)
logging.warning("--- Before create_app() call ---")

# Vercelがこの 'app' 変数を探して実行します
app = create_app()

# ★★★ アプリ作成後ログ ★★★
print("--- After create_app() call ---", file=sys.stderr)
logging.warning("--- After create_app() call ---")

# 開発環境でのローカル実行用（Vercelでは不要だが、ローカルテスト用に残しておいても良い）
if __name__ == '__main__':
    app.run(debug=True) 