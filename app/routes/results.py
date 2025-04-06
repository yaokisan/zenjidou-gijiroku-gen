#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, jsonify, request
from app.models import MinutesHistory

# Blueprintの作成
bp = Blueprint('results', __name__)

@bp.route('/', methods=['GET'])
def index():
    """ホームページ (議事録一覧)の表示"""
    # 議事録履歴の取得（最新順）
    histories = MinutesHistory.query.order_by(MinutesHistory.received_at.desc()).all()
    
    # テンプレートにデータを渡す
    return render_template('results.html', histories=histories)

@bp.route('/api/histories', methods=['GET'])
def get_histories():
    """議事録履歴をJSON形式で取得するAPI (フロントエンドからのAjaxリクエスト用)"""
    # クエリパラメータの取得
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    # クエリの作成
    query = MinutesHistory.query.order_by(MinutesHistory.received_at.desc())
    
    # ステータスでフィルタリング（指定がある場合）
    if status:
        query = query.filter(MinutesHistory.status == status)
    
    # ページネーション
    total = query.count()
    histories = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # 結果をJSON形式で返す
    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "data": [history.to_dict() for history in histories]
    })

@bp.route('/api/history/<int:history_id>', methods=['GET'])
def get_history(history_id):
    """特定の議事録履歴の詳細をJSON形式で取得するAPI"""
    history = MinutesHistory.query.get_or_404(history_id)
    return jsonify(history.to_dict())

@bp.route('/api/status/<int:history_id>')
def get_status(history_id):
    """履歴ステータスを取得するAPIエンドポイント"""
    history = MinutesHistory.query.get(history_id)
    if not history:
        return jsonify({
            "status": "error",
            "message": f"History with ID {history_id} not found"
        }), 404
    
    # 履歴情報をJSON形式で返す
    return jsonify({
        "id": history.id,
        "status": history.status,
        "notta_title": history.notta_title,
        "generated_title": history.generated_title,
        "processed_at": history.processed_at.isoformat() if history.processed_at else None,
        "notion_page_url": history.notion_page_url,
        "error_message": history.error_message
    }) 