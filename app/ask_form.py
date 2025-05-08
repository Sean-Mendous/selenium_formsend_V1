from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from utilities.logger import logger

def chatgpt_4omini(prompt):
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a form sender agent."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9
    )
    return response.choices[0].message.content

def create_prompt(form_structure, sender_info, sentence):
    form_json = json.dumps(form_structure, ensure_ascii=False, indent=2)
    sender_json = json.dumps(sender_info, ensure_ascii=False, indent=2)

    main_prompt = """
あなたはウェブフォーム自動入力支援AIです。

以下にフォーム構造情報（fields）とユーザー情報を提供します。

フォーム構造情報は、各入力項目の「tag」「type」「meta情報」を順番にリストで提供しています。

あなたの役割は、この順番に沿って、各項目に入力する値（value）だけをリストで返すことです。

出力仕様:
- 出力はJSON形式で "actions" キーを持つオブジェクトとしてください。
- "actions" の値は、フォーム構造情報の順番に対応する値のリストです。
- 各typeに合った形式で返してください。
    - type="text": 文字列
    - type="email": メールアドレス形式
    - type="date": yyyy-mm-dd形式
    - type="tel": 電話番号形式
    - type="radio": 選択するoptionのvalue
    - type="checkbox": 選択するoptionのvalue
- 下記に【問い合わせ内容およびメッセージ】は、基本的にtagが<textarea>のものに含めてください。
- 値が入力不要な場合もしくは不明な場合、""（空文字）を入れてください。

出力形式の例:
{
  "actions": [
    "2024-04-05",
    "山田太郎",
    "example@example.com"
  ]
}

※必ず上記のJSON形式でのみ出力してください。
"""

    overall_prompt = f"""
{main_prompt}

【フォーム構造情報】
{form_json}

【ユーザー情報】
{sender_json}

【問い合わせ内容およびメッセージ】
{sentence}
"""

    return overall_prompt

def ask_form(form_structure, sender_info, sentence):
    try:
        prompt = create_prompt(form_structure, sender_info, sentence)
        if prompt:
            logger.info(f' >prompt:\n{prompt}')
        else:
            raise RuntimeError(f'Failed to create prompt')
    except Exception as e:
        raise RuntimeError(f'Failed to create prompt: {e}') from e
    
    try:
        response = chatgpt_4omini(prompt)
        if response:
            logger.info(f' >response:\n{response}')
        else:
            raise RuntimeError(f'Failed to get response from chatgpt')
    except Exception as e:
        raise RuntimeError(f'Failed to get response from chatgpt: {e}') from e
    
    try:
        response_json = json.loads(response)
    except Exception as e:
        raise RuntimeError(f'Failed to convert response to json: {e}') from e
    
    return response_json
