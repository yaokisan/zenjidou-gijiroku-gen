#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ウェブフックを直接呼び出すテストスクリプト
アプリケーションが起動中であることを確認して実行してください
"""

import requests
import json
import sys
import time

# アプリのURL (アプリのURLに合わせて変更)
url = "http://localhost:5002/webhook/notta"

# テストデータ
data = {
    "content": "これはテスト用の文字起こしです。AI議事録生成のテストを行っています。",
    "title": "テスト会議",
    "creation_time": "2023-04-05 12:00:00",
    "speakers": ["テスト話者1", "テスト話者2"]
}

def test_webhook():
    print("=== ウェブフックテスト ===")
    print(f"送信先URL: {url}")
    print(f"送信データ: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        # POSTリクエスト送信
        response = requests.post(url, json=data)
        
        # 結果の確認
        print(f"\nステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"レスポンス: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            print(f"\n✅ ウェブフック呼び出し成功！")
            print(f"履歴ID: {response_data.get('history_id')}")
            return response_data.get('history_id')
        else:
            print(f"❌ エラーレスポンス: {response.text}")
            return None
    except Exception as e:
        print(f"❌ リクエスト送信中にエラー発生: {str(e)}")
        print("アプリケーションが起動中であることを確認してください。")
        return None

def check_processing_status(history_id, max_attempts=10):
    """処理状態をチェックする（実際のアプリでは非同期処理のため）"""
    if not history_id:
        return
    
    # 結果確認用の簡易的なエンドポイント
    status_url = f"http://localhost:5002/results/api/status/{history_id}"
    
    print(f"\n=== 処理状態の確認 (履歴ID: {history_id}) ===")
    print("非同期処理の完了を待機中...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(status_url)
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                print(f"試行 {attempt}/{max_attempts}: ステータス = {status}")
                
                if status == 'completed':
                    print(f"✅ 処理完了！")
                    print(f"生成されたタイトル: {status_data.get('generated_title')}")
                    print(f"Notion URL: {status_data.get('notion_page_url')}")
                    return True
                elif status == 'failed':
                    print(f"❌ 処理失敗: {status_data.get('error_message')}")
                    return False
                
                # まだ処理中の場合は少し待機
                time.sleep(2)
            else:
                print(f"❌ ステータス取得エラー: {response.text}")
                time.sleep(1)
        except Exception as e:
            print(f"❌ ステータス確認中にエラー: {str(e)}")
            time.sleep(1)
    
    print("⚠️ 最大試行回数に達しました。処理が完了していない可能性があります。")
    return False

if __name__ == "__main__":
    # ウェブフックテスト実行
    history_id = test_webhook()
    
    if history_id:
        # 処理状態の確認
        print("\nNote: ステータス確認のためには、Flask側に /results/api/status/<history_id> エンドポイントが必要です")
        print("このエンドポイントが実装されていない場合は、手動でアプリの履歴ページを確認してください。") 