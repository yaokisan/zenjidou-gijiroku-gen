#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import logging
import sys

# .envファイルから環境変数を読み込む
load_dotenv()

# データベースの初期化
db = SQLAlchemy()

def create_app(test_config=None):
    """Flaskアプリケーションを作成して設定する"""
    
    # ★★★ create_app 開始ログ ★★★
    print("--- create_app START ---", file=sys.stderr)
    logging.warning("--- create_app START ---")

    # Flaskアプリケーションの作成
    app = Flask(__name__, instance_relative_config=True)
    print("--- Flask app created ---", file=sys.stderr)
    logging.warning("--- Flask app created ---")
    
    # アプリケーション設定
    try:
        print("--- Configuring app settings START ---", file=sys.stderr)
        logging.warning("--- Configuring app settings START ---")
        db_url = os.environ.get('DATABASE_URL')
        print(f"--- DATABASE_URL from env: {db_url} ---", file=sys.stderr) # ★ DATABASE_URL をログ出力
        logging.warning(f"--- DATABASE_URL from env: {db_url} ---")
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            SQLALCHEMY_DATABASE_URI=db_url, # 環境変数から取得
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        print("--- Configuring app settings END ---", file=sys.stderr)
        logging.warning("--- Configuring app settings END ---")
    except Exception as config_e:
        print(f"--- ERROR during app config: {config_e} ---", file=sys.stderr)
        logging.error(f"--- ERROR during app config: {config_e} ---", exc_info=True)
        raise # 設定でエラーが出たら起動できないので再raise

    # テスト設定がある場合はそれを使用
    if test_config is not None:
        app.config.from_mapping(test_config)

    # SQLiteを使用しないため、インスタンスフォルダ作成は必須ではない (残してもOK)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # データベースの初期化
    try:
        print("--- Initializing DB (db.init_app) START ---", file=sys.stderr)
        logging.warning("--- Initializing DB (db.init_app) START ---")
        db.init_app(app)
        print("--- Initializing DB (db.init_app) END ---", file=sys.stderr)
        logging.warning("--- Initializing DB (db.init_app) END ---")
    except Exception as db_init_e:
        print(f"--- ERROR during db.init_app: {db_init_e} ---", file=sys.stderr)
        logging.error(f"--- ERROR during db.init_app: {db_init_e} ---", exc_info=True)
        raise # DB初期化エラーも起動不可なので再raise

    # ルート定義のインポートと登録
    from app.routes import webhook, settings, results
    app.register_blueprint(webhook.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(results.bp)
    print("--- Blueprints registered ---", file=sys.stderr)
    logging.warning("--- Blueprints registered ---")

    # アプリケーションのコンテキストでデータベースを初期化
    try:
        with app.app_context():
            print("--- App context entered ---", file=sys.stderr)
            logging.warning("--- App context entered ---")
            from app.models import Settings, MinutesHistory
            print("--- Models imported within context ---", file=sys.stderr)
            logging.warning("--- Models imported within context ---")
            print("--- Attempting db.create_all() START ---", file=sys.stderr)
            logging.warning("--- Attempting db.create_all() START ---")
            db.create_all()
            print("--- Attempting db.create_all() END ---", file=sys.stderr)
            logging.warning("--- Attempting db.create_all() END ---")

            # デフォルト設定がなければ作成
            from app.models import initialize_default_settings
            initialize_default_settings()
            print("--- Default settings initialized (if needed) ---", file=sys.stderr)
            logging.warning("--- Default settings initialized (if needed) ---")
    except Exception as context_e:
        print(f"--- ERROR within app_context (likely db.create_all): {context_e} ---", file=sys.stderr)
        logging.error(f"--- ERROR within app_context (likely db.create_all): {context_e} ---", exc_info=True)
        # ここでraiseするかどうかは状況による (起動はするがDB操作でエラーになる)

    print("--- create_app END ---", file=sys.stderr)
    logging.warning("--- create_app END ---")
    return app 