#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
import google.generativeai as genai
import anthropic
import openai

# 環境変数から各APIキーを取得
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Google Geminiの初期化
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# OpenAIの初期化
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# ロガーの設定
logger = logging.getLogger(__name__)

# 議事録生成用のシステムプロンプト
MINUTES_SYSTEM_PROMPT = """
# 目的
添付された会議の文字起こし全文を元に議事録をつくってください。
# 注意点
・最初に日時と参加者を明記、次に会議の目的や主題についての簡単な要約を記載し、その次に数字箇条書きで最低限のアジェンダを記載してください。
・ネクストアクションは末尾に記載し、人物と期限を必ず明確にしてください。ただし、内容は会議での事実ベースで記載し、結論付けられていないことは勝手に予測して作成しないようにしてください。（記載例：GOさん記事LPのCTA文言修正案作成【小林 〜1/15】）
・議事録は会話内のニュアンスが失われないように丁寧に構造的に整理してください。ただし、会話調ではなく事実ベースで記載する形式にしてください。
・文量はコピペしたときにGoogleドキュメント5ページ分程度になるようにまとめ、コピペしてそのまま視覚的に見やすくなるような体裁で出力してください。
"""

def generate_minutes(content, title, creation_time, speakers, ai_provider, ai_model, anthropic_thinking_mode=False):
    """AIを使用して議事録を生成する
    
    Args:
        content (str): 文字起こしの内容
        title (str): 元のタイトル
        creation_time (str): 作成時間
        speakers (list): 話者情報
        ai_provider (str): 使用するAIプロバイダー (google_gemini, anthropic_claude, openai_chatgpt)
        ai_model (str): 使用するAIモデル名
        anthropic_thinking_mode (bool): Anthropic Claudeで思考モードを使用するかどうか
        
    Returns:
        dict: 生成結果を含むディクショナリ
            - minutes_content: 生成された議事録内容
            - generated_title: 生成されたタイトル
    """
    # 入力データのログ記録
    logger.info(f"Generating minutes with {ai_provider}, model={ai_model}")
    logger.info(f"Input title: {title}")
    logger.info(f"Creation time: {creation_time}")
    logger.info(f"Content length: {len(content)} chars")
    logger.info(f"Number of speakers: {len(speakers)}")
    
    try:
        # 対象の日時情報を整形
        formatted_date = ""
        if creation_time:
            try:
                # 日時文字列をパース (フォーマットは状況に応じて調整)
                if isinstance(creation_time, datetime):
                    dt = creation_time
                else:
                    dt = datetime.strptime(creation_time, "%Y-%m-%d %H:%M:%S")
                formatted_date = dt.strftime("%Y年%m月%d日 %H:%M")
            except (ValueError, TypeError) as e:
                logger.warning(f"日時のパースに失敗しました: {str(e)}")
                formatted_date = str(creation_time)
        
        # AIプロバイダー別の処理
        if ai_provider == "google_gemini":
            return _generate_with_gemini(content, title, formatted_date, speakers, ai_model)
        elif ai_provider == "anthropic_claude":
            return _generate_with_claude(content, title, formatted_date, speakers, ai_model, anthropic_thinking_mode)
        elif ai_provider == "openai_chatgpt":
            return _generate_with_openai(content, title, formatted_date, speakers, ai_model)
        else:
            raise ValueError(f"不明なAIプロバイダー: {ai_provider}")
    
    except Exception as e:
        logger.error(f"議事録生成中にエラーが発生しました: {str(e)}")
        raise


def _generate_with_gemini(content, title, formatted_date, speakers, model_name):
    """Google Geminiを使用して議事録を生成する"""
    try:
        # Geminiモデルの取得
        model = genai.GenerativeModel(model_name)
        
        # 話者情報の整形
        speakers_text = ", ".join([speaker for speaker in speakers if speaker]) if speakers else "不明"
        
        # ユーザープロンプトの構築
        user_prompt = f"""
# 会議情報
- タイトル: {title}
- 日時: {formatted_date}
- 参加者: {speakers_text}

# 文字起こし内容
{content}
"""
        
        # 修正: システムプロンプトとユーザープロンプトを結合して渡す
        full_prompt = f"{MINUTES_SYSTEM_PROMPT}\\n\\n{user_prompt}"
        response = model.generate_content(full_prompt)
        
        # 応答の処理
        minutes_content = response.text if hasattr(response, 'text') else str(response)
        
        # タイトルの生成
        title_prompt = f"""
以下は会議の文字起こしから生成した議事録です。この議事録に適切なタイトルを30文字以内で考えてください。
日本語で、会議の内容を端的に表すタイトルにしてください。タイトルのみを出力してください。

# 会議情報
- 元のタイトル: {title}
- 日時: {formatted_date}

# 議事録
{minutes_content[:500]}...
"""
        title_response = model.generate_content(title_prompt)
        generated_title = title_response.text.strip() if hasattr(title_response, 'text') else str(title_response).strip()
        
        # 文字数制限（30文字）
        if len(generated_title) > 30:
            generated_title = generated_title[:30]
        
        return {
            "minutes_content": minutes_content,
            "generated_title": generated_title
        }
    
    except Exception as e:
        logger.error(f"Geminiでの議事録生成中にエラーが発生しました: {str(e)}")
        raise


def _generate_with_claude(content, title, formatted_date, speakers, model_name, thinking_mode=False):
    """Anthropic Claudeを使用して議事録を生成する"""
    try:
        # Anthropicクライアントの初期化
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # 話者情報の整形
        speakers_text = ", ".join([speaker for speaker in speakers if speaker]) if speakers else "不明"
        
        # ユーザープロンプトの構築
        user_prompt = f"""
# 会議情報
- タイトル: {title}
- 日時: {formatted_date}
- 参加者: {speakers_text}

# 文字起こし内容
{content}
"""
        
        # システムプロンプトの拡張（思考モードの場合）
        system_prompt = MINUTES_SYSTEM_PROMPT
        if thinking_mode:
            system_prompt += "\n\n思考プロセスを示すために、まず文字起こしを分析し、重要なポイントを抽出し、それから最終的な議事録を作成してください。"
        
        # Claudeに送信
        response = client.messages.create(
            model=model_name,
            system=system_prompt,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # 応答の処理
        minutes_content = response.content[0].text if hasattr(response, 'content') and response.content else ""
        
        # タイトルの生成
        title_prompt = f"""
以下は会議の文字起こしから生成した議事録です。この議事録に適切なタイトルを30文字以内で考えてください。
日本語で、会議の内容を端的に表すタイトルにしてください。タイトルのみを出力してください。

# 会議情報
- 元のタイトル: {title}
- 日時: {formatted_date}

# 議事録
{minutes_content[:500]}...
"""
        title_response = client.messages.create(
            model=model_name,
            max_tokens=50,
            messages=[
                {"role": "user", "content": title_prompt}
            ]
        )
        
        generated_title = title_response.content[0].text.strip() if hasattr(title_response, 'content') and title_response.content else ""
        
        # 文字数制限（30文字）
        if len(generated_title) > 30:
            generated_title = generated_title[:30]
        
        return {
            "minutes_content": minutes_content,
            "generated_title": generated_title
        }
    
    except Exception as e:
        logger.error(f"Claudeでの議事録生成中にエラーが発生しました: {str(e)}")
        raise


def _generate_with_openai(content, title, formatted_date, speakers, model_name):
    """OpenAI GPTを使用して議事録を生成する"""
    try:
        # 話者情報の整形
        speakers_text = ", ".join([speaker for speaker in speakers if speaker]) if speakers else "不明"
        
        # ユーザープロンプトの構築
        user_prompt = f"""
# 会議情報
- タイトル: {title}
- 日時: {formatted_date}
- 参加者: {speakers_text}

# 文字起こし内容
{content}
"""
        
        # OpenAIに送信
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": MINUTES_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000
        )
        
        # 応答の処理
        minutes_content = response.choices[0].message.content if response.choices else ""
        
        # タイトルの生成
        title_prompt = f"""
以下は会議の文字起こしから生成した議事録です。この議事録に適切なタイトルを30文字以内で考えてください。
日本語で、会議の内容を端的に表すタイトルにしてください。タイトルのみを出力してください。

# 会議情報
- 元のタイトル: {title}
- 日時: {formatted_date}

# 議事録
{minutes_content[:500]}...
"""
        
        title_response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": title_prompt}
            ],
            max_tokens=50
        )
        
        generated_title = title_response.choices[0].message.content.strip() if title_response.choices else ""
        
        # 文字数制限（30文字）
        if len(generated_title) > 30:
            generated_title = generated_title[:30]
        
        return {
            "minutes_content": minutes_content,
            "generated_title": generated_title
        }
    
    except Exception as e:
        logger.error(f"OpenAIでの議事録生成中にエラーが発生しました: {str(e)}")
        raise 