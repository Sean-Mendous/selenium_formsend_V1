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

    main_prompt = f"""
あなたはウェブフォーム自動入力支援AIです。
以下にフォームの構造情報（JSON形式）とユーザー情報（TXT形式）を提供します。

フォーム構造情報では、各入力フィールドの「meta」属性として name, label, placeholder, id, near_textなどの情報が含まれています。
このmeta情報から、そのフィールドがどのユーザー情報に対応するかを推測してください。

出力では、各フィールドに入力するべき値をJSON形式で返してください。

【出力仕様】
- 通常の入力欄（text, email など）は "フィールド名": "入力する値" としてください。
- radioボタンは "フィールド名": "選択するvalue" としてください。
- checkboxは:
    - 複数選択の場合: "フィールド名": ["選択するvalue1", "選択するvalue2"]
    - 1個のみの場合: "フィールド名": true または false
    - 該当する入力値が無い場合は ""（空文字）、または checkbox は false にしてください。

出力形式の例:
{{
  "first_name": "Taro",
  "gender": "male",
  "hobbies": ["reading", "sports"],
  "newsletter": true
}}

必ず上記のJSON形式でのみ出力してください。
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

def convert_to_actions(response):
    actions = []
    for key, value in response.items():
        actions.append({
            "type": "fill",
            "name": key,
            "value": value
        })
    return {"actions": actions}

def ask_gpt(form_structure, sender_info, sentence):
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
    
    try:
        actions = convert_to_actions(response_json)
        if actions:
            logger.info(f' >actions:\n{actions}')
        else:
            raise RuntimeError(f'Failed to convert response to actions')
    except Exception as e:
        raise RuntimeError(f'Failed to convert response to actions: {e}') from e
    
    return actions
