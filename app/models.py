#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from datetime import datetime
from app import db

class Settings(db.Model):
    """アプリケーション設定を保存するモデル"""
    
    id = db.Column(db.Integer, primary_key=True)
    
    # AIモデル設定
    ai_provider = db.Column(db.String(50), nullable=False, default="google_gemini")  # google_gemini, anthropic_claude, openai_chatgpt
    google_gemini_model = db.Column(db.String(50), nullable=False, default="gemini-2.5-pro-exp-03-25")
    anthropic_claude_model = db.Column(db.String(50), nullable=False, default="claude-3.7-sonnet")
    anthropic_thinking_mode = db.Column(db.Boolean, default=True)
    openai_chatgpt_model = db.Column(db.String(50), nullable=False, default="gpt-4o")
    
    # Notion設定
    notion_parent_page_id = db.Column(db.String(50), nullable=True)
    
    # 最終更新日時
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Settings {self.id}>'
    
    def to_dict(self):
        """設定をディクショナリに変換"""
        return {
            'id': self.id,
            'ai_provider': self.ai_provider,
            'google_gemini_model': self.google_gemini_model,
            'anthropic_claude_model': self.anthropic_claude_model,
            'anthropic_thinking_mode': self.anthropic_thinking_mode,
            'openai_chatgpt_model': self.openai_chatgpt_model,
            'notion_parent_page_id': self.notion_parent_page_id,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MinutesHistory(db.Model):
    """生成された議事録履歴を保存するモデル"""
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Notta情報
    notta_title = db.Column(db.String(255), nullable=False)
    notta_creation_time = db.Column(db.DateTime, nullable=True)
    
    # 処理情報
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    ai_provider = db.Column(db.String(50), nullable=True)
    ai_model = db.Column(db.String(50), nullable=True)
    
    # 生成された議事録
    generated_title = db.Column(db.String(255), nullable=True)
    notion_page_url = db.Column(db.String(255), nullable=True)
    
    # 元データ（Webhookで受け取ったデータを保存）
    raw_data = db.Column(db.Text, nullable=True)
    
    # 処理状態
    status = db.Column(db.String(20), default="pending")  # pending, processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)  # エラーが発生した場合のメッセージ
    
    def __repr__(self):
        return f'<MinutesHistory {self.id}>'
    
    def to_dict(self):
        """履歴をディクショナリに変換"""
        return {
            'id': self.id,
            'notta_title': self.notta_title,
            'notta_creation_time': self.notta_creation_time.isoformat() if self.notta_creation_time else None,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'generated_title': self.generated_title,
            'notion_page_url': self.notion_page_url,
            'status': self.status,
            'error_message': self.error_message
        }
    
    def get_raw_data_dict(self):
        """保存されたJSONデータをディクショナリに変換"""
        if self.raw_data:
            try:
                return json.loads(self.raw_data)
            except json.JSONDecodeError:
                return {}
        return {}


def initialize_default_settings():
    """デフォルト設定の初期化（存在しない場合）"""
    if not Settings.query.first():
        default_settings = Settings()
        db.session.add(default_settings)
        db.session.commit()
        print("デフォルト設定を初期化しました。") 