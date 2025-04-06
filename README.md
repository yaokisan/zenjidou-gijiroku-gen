# 全自動議事録生成アプリ

Notta連携による議事録生成の自動化と一元管理を行うWebアプリケーションです。
**現在はデバッグが完了し、正常に動作しています。**

## 概要

このアプリはZapier経由でNottaの文字起こしデータを受け取り、AIを使用して議事録を自動生成し、Notionに保存します。
生成AIとしてGoogle Gemini、Anthropic Claude、OpenAI ChatGPTから選択可能です。

## 特徴

- Zapier WebhookによるNotta連携
- 複数の生成AIモデルの選択機能
- 議事録生成履歴の管理・閲覧
- AIモデル設定のカスタマイズ
- Notionとの連携

## 最近の主な変更 (2025-04-06)

- **Notion連携の安定化:** Notionサービス層を経由せずに直接APIを呼び出すように `app/routes/webhook.py` を修正し、ページIDに関する問題を解決しました。
- **ステータス確認API追加:** 処理状況を確認するためのAPIエンドポイント (`/api/status/<history_id>`) を `app/routes/results.py` に追加しました。
- **テストスクリプトの追加:** Notion API接続テスト (`tests/test_notion.py`) とWebhookエンドポイントテスト (`tests/test_webhook.py`) を追加しました。

## 必要条件

- Python 3.8以上
- 各AIサービスのAPIキー（使用するモデルに応じて）
  - Google API Key (Gemini用)
  - Anthropic API Key (Claude用)
  - OpenAI API Key (ChatGPT用)
- Notion API Key（Notionに保存する場合）
- Zapierアカウント（Notta連携用）

## インストール方法

1. リポジトリをクローンまたはダウンロードします
   ```bash
   git clone <repository-url>
   cd 議事録自動生成アプリ # プロジェクトのディレクトリ名に合わせてください
   ```

2. 仮想環境を作成し、アクティベートします
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
   ```

3. 依存パッケージをインストールします
   ```bash
   pip install -r requirements.txt
   ```

4. `.env`ファイルを作成し、必要な環境変数を設定します
   ```bash
   # .envファイルを作成し、以下のキーなどを設定します
   # GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
   # ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY
   # OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   # NOTION_API_KEY=YOUR_NOTION_API_KEY
   # NOTION_PARENT_PAGE_ID=YOUR_NOTION_PARENT_PAGE_ID # Notion連携に必須
   # SECRET_KEY=YOUR_SECRET_KEY
   # DATABASE_URL=sqlite:///../instance/app.db
   # ZAPIER_WEBHOOK_URL=YOUR_ZAPIER_WEBHOOK_URL # Zapierからの通知用 (任意)
   # ... 他にも必要な設定があれば追記 ...
   ```
   **重要:** Notionに保存する場合、`NOTION_API_KEY` と `NOTION_PARENT_PAGE_ID` の設定は必須です。

## 使い方

1. アプリケーションを起動します
   ```bash
   python run.py
   ```
   デフォルトでは `http://localhost:5002` で起動します。

2. Webブラウザで `http://localhost:5002` にアクセスします

3. 設定ページ (`/settings`) で以下を行います:
   - 使用するAIモデルを選択
   - **Notion親ページIDを設定:** Notion連携には必須です。指定したページの配下に議事録が作成されます。
     - **注意:** Notionインテグレーションを対象の親ページと共有する必要があります。（Notionページの右上「...」→「接続を追加」→インテグレーション選択）
   - Webhook URL (`/api/webhook`) をコピーしてZapierに設定

4. Zapierで以下の設定を行います:
   - トリガー: Notta新規文字起こし完了時など
   - アクション: Webhooks by Zapier (POST)
   - URL: アプリの設定ページでコピーしたWebhook URL (`http://<あなたのアプリの公開URL>/api/webhook`)
   - Payload Type: Json
   - Data: Nottaから受け取りたいデータを設定 (例: `transcript`, `summary` など)

5. 設定完了後、Zapierのトリガーが発火すると、自動的に処理が開始されます。

6. 処理状況と結果は議事録一覧ページ (`/results`) で確認できます。

## フォルダ構成

```
./
├── app/                    # Flaskアプリケーションのコア
│   ├── __init__.py         # アプリケーションファクトリ
│   ├── models.py           # SQLAlchemyモデル
│   ├── routes/             # APIルート定義 (webhook.py, results.py など)
│   ├── services/           # 外部サービス連携 (ai_service.py, notion_service.py など)
│   ├── static/             # CSS, JSなどの静的ファイル
│   └── templates/          # Jinja2 HTMLテンプレート
├── docs/                   # ドキュメント類
├── instance/               # インスタンス固有ファイル (例: app.db)
├── scripts/                # 補助スクリプト (app_debug.py, check_api_key.py など)
├── tests/                  # テストスクリプト (test_notion.py, test_webhook.py)
├── venv/                   # Python仮想環境 (通常Git管理外)
├── .env                    # 環境変数ファイル (Git管理外)
├── .gitignore              # Git無視リスト
├── app_debug.py            # アプリケーション設定診断スクリプト (scripts/にも同じものあり)
├── README.md               # このファイル
├── requirements.txt        # Python依存パッケージリスト
└── run.py                  # アプリケーション起動スクリプト
```

## デバッグツール

以下のスクリプトがデバッグに役立ちます。

- **`tests/test_notion.py`**: Notion APIキーとページIDの有効性、ページアクセスや子ページ作成をテストします。
  ```bash
  python tests/test_notion.py
  ```
- **`tests/test_webhook.py`**: `/api/webhook` エンドポイントにテストデータをPOSTし、議事録生成プロセス全体の動作を確認します。ポート番号が `5002` 以外の場合はスクリプト内のURLを修正してください。
  ```bash
  python tests/test_webhook.py
  ```
- **`app_debug.py`** (または **`scripts/app_debug.py`**): アプリケーションの設定（環境変数、APIキーの読み込みなど）を診断します。
  ```bash
  python app_debug.py
  ```

## デプロイ

本アプリケーションはRenderなどのPaaSサービスにデプロイできます。

Renderの場合:
1. Renderアカウントにサインアップし、新しいWeb Serviceを作成
2. リポジトリを接続し、以下の設定を行う:
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`
3. Environment設定で環境変数を追加（`.env`ファイルの内容を登録）

## ライセンス

[MITライセンス](LICENSE) (LICENSEファイルが存在する場合)

## 開発者

(ここに開発者情報を記載) 