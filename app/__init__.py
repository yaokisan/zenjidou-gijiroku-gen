#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# データベースの初期化
db = SQLAlchemy()

def create_app(test_config=None):
    """Flaskアプリケーションを作成して設定する"""
    
    # Flaskアプリケーションの作成
    app = Flask(__name__, instance_relative_config=True)
    
    # アプリケーション設定
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'app.db')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # テスト設定がある場合はそれを使用
    if test_config is not None:
        app.config.from_mapping(test_config)

    # インスタンスフォルダの作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # データベースの初期化
    db.init_app(app)

    # ルート定義のインポートと登録
    from app.routes import webhook, settings, results
    app.register_blueprint(webhook.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(results.bp)

    # アプリケーションのコンテキストでデータベースを初期化
    with app.app_context():
        from app.models import Settings, MinutesHistory
        db.create_all()
        
        # デフォルト設定がなければ作成
        from app.models import initialize_default_settings
        initialize_default_settings()

    return app 