#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app import db
from app.models import Settings

# Blueprintの作成
bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/', methods=['GET'])
def index():
    """設定ページの表示"""
    # 設定を取得 (なければ作成)
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    
    # テンプレートにデータを渡す
    return render_template('settings.html', settings=settings)

@bp.route('/update', methods=['POST'])
def update():
    """設定の更新"""
    try:
        # 設定を取得
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
        
        # POSTデータから設定を更新
        settings.ai_provider = request.form.get('ai_provider', 'google_gemini')
        settings.google_gemini_model = request.form.get('google_gemini_model', 'gemini-2.5-pro-exp-03-25')
        settings.anthropic_claude_model = request.form.get('anthropic_claude_model', 'claude-3.7-sonnet')
        settings.anthropic_thinking_mode = bool(request.form.get('anthropic_thinking_mode', False))
        settings.openai_chatgpt_model = request.form.get('openai_chatgpt_model', 'gpt-4o')
        settings.notion_parent_page_id = request.form.get('notion_parent_page_id')
        
        # データベースに保存
        db.session.commit()
        
        # 保存成功のメッセージ
        flash('設定が正常に保存されました', 'success')
        
        # 設定ページにリダイレクト
        return redirect(url_for('settings.index'))
    
    except Exception as e:
        # エラーメッセージの表示
        flash(f'設定の保存中にエラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('settings.index'))

@bp.route('/webhook-url', methods=['GET'])
def webhook_url():
    """Webhook URLの取得 (フロントエンドからのAjaxリクエスト用)"""
    # 本番環境のURLまたはローカル開発用のURL
    base_url = request.host_url.rstrip('/')
    webhook_url = f"{base_url}/webhook/notta"
    
    return jsonify({
        "webhook_url": webhook_url,
        "message": "このURLをZapierのWebhooks by Zapierアクションに設定してください。"
    }) 