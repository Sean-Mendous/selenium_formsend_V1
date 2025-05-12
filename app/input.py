import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from app.chatgpt_setting import chatgpt_4omini
from utilities.logger import logger

#///get_action///
def erase_click_control(fields):
    return [field for field in fields if field.get('control') != 'click']

def create_prompt(fields, sender_info, sentence):
    fields_json = json.dumps(fields, ensure_ascii=False, indent=2)
    sender_json = json.dumps(sender_info, ensure_ascii=False, indent=2)

    basic_prompt = """
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
    - type="date": yyyymmdd形式
    - type="tel": 電話番号形式
    - type="radio": 選択するoptionのvalue
    - type="checkbox": 選択するoptionのvalue
- 下記に【問い合わせ内容およびメッセージ】は、基本的にtagが<textarea>のものに含めてください。
- 値が入力不要な場合もしくは不明な場合、""（空文字）を入れてください。

出力形式の例:
{
  "actions": [
    "20240405",
    "山田太郎",
    "example@example.com"
  ]
}

※必ず上記のJSON形式でのみ出力してください。
"""

    overall_prompt = f"""
{basic_prompt}

【フォーム構造情報】
{fields_json}

【ユーザー情報】
{sender_json}

【問い合わせ内容およびメッセージ】
{sentence}
"""
    return overall_prompt

def input_action_json(fields, sender_info, sentence):
    original_fields = fields

    try:
        nonclick_fields = erase_click_control(original_fields)
        if nonclick_fields:
            logger.info(f" >Successfully erased [{len(original_fields)} → {len(nonclick_fields)}] click fields")
        else:
            raise RuntimeError("Failed to erase click fields")
    except Exception as e:
        raise RuntimeError(f"Failed to erase click fields: {e}") from e

    try:
        prompt = create_prompt(nonclick_fields, sender_info, sentence)
        if prompt:
            logger.info(f" >Successfully got prompt")
        else:
            raise RuntimeError("Failed to get prompt")
    except Exception as e:
        raise RuntimeError(f"Failed to get prompt: {e}") from e
    
    try:
        response = chatgpt_4omini(prompt)
        if response:
            logger.info(f" >Successfully got response")
        else:
            raise RuntimeError("Failed to get response")
    except Exception as e:
        raise RuntimeError(f"Failed to get response: {e}") from e
    
    try:
        response_json = json.loads(response)
        if response_json:
            logger.info(f" >Successfully got response_json")
        else:
            raise RuntimeError("Failed to get response_json")
    except Exception as e:
        raise RuntimeError(f"Failed to convert response to json: {e}") from e
    
    return response_json


#///input_form///
def find_element(driver, meta, tag, input_type=None):
    selectors = []

    # 優先順位: name > id > placeholder > label > near_text
    if meta.get("name"):
        selectors.append((By.NAME, meta["name"]))
    if meta.get("id"):
        selectors.append((By.ID, meta["id"]))
    if meta.get("placeholder"):
        xpath = f"//{tag}[@placeholder='{meta['placeholder']}']"
        selectors.append((By.XPATH, xpath))
    if meta.get("label"):
        xpath = f"//label[contains(text(), '{meta['label']}')]/following::{tag}[1]"
        selectors.append((By.XPATH, xpath))
    if meta.get("near_text"):
        xpath = f"//*[contains(text(), '{meta['near_text']}')]/following::{tag}[1]"
        selectors.append((By.XPATH, xpath))

    for method, value in selectors:
        try:
            return driver.find_element(method, value)
        except:
            continue
    return None

def fill_form(field, actions, driver, idx, sleep_time):
    error = []

    tag = field["tag"]
    input_type = field["type"]
    meta = field["meta"]
    value = actions["actions"][idx]

    try:
        elem = find_element(driver, meta, tag)
        if not elem:
            raise Exception("Element not found")

        if tag == "input":
            elem.clear()
            elem.send_keys(value)
            logger.info(f" - input: {meta.get('name')} = {value}")
        elif tag == "textarea":
            elem.clear()
            elem.send_keys(value)
            logger.info(f" - textarea input: {meta.get('name')} = {value}")
        elif tag == "select":
            from selenium.webdriver.support.ui import Select
            select = Select(elem)
            select.select_by_visible_text(value)
            logger.info(f" - select: {meta.get('name')} = {value}")
    
        time.sleep(sleep_time)

    except Exception as e:
        logger.error(f" - error on {meta.get('name')}: {e}")
        error.append(f"{meta.get('name')}: {e}")

    return error

def click_form(field, driver):
    meta = field["meta"]
    
    # 試す探索パターンリスト
    xpath_candidates = []

    # id
    if meta.get("id"):
        xpath_candidates.append(f"//*[@id='{meta['id']}']")
        logger.info(f' - using "id"')

    # name
    if meta.get("name"):
        xpath_candidates.append(f"//button[@name='{meta['name']}']")
        xpath_candidates.append(f"//input[@name='{meta['name']}']")
        logger.info(f' - using "name"')

    # value (inputの場合)
    if meta.get("placeholder"):
        xpath_candidates.append(f"//input[@value='{meta['placeholder']}']")
        logger.info(f' - using "placeholder"')

    # text系
    for text_val in [meta.get("label"), meta.get("near_text"), meta.get("title"), meta.get("aria_label")]:
        if text_val:
            xpath_candidates.append(f"//button[contains(., '{text_val}')]")
            xpath_candidates.append(f"//input[@value='{text_val}']")
            logger.info(f' - using "text"')

    # fallback: ボタン全部
    xpath_candidates.append("//button")
    logger.info(' - using "fallback"')

    # 探索
    for xpath in xpath_candidates:
        try:
            btn = driver.find_element(By.XPATH, xpath)
            if btn:
                btn.click()
                logger.info(f" - Clicked submit button via xpath: {xpath}")
                return True
        except Exception as e:
            logger.error(f"Failed to find submit button: {e}")
            continue

    raise RuntimeError("Failed to find submit button")

def input_form(fields, actions, driver, send=False, sleep_time=1):
    error = []
    send_status = False

    # extract fields
    input_fields = [
        f for f in fields
            if (f["control"] in ["fill"])
    ]
    button_fields = [
        f for f in fields
            if (f["control"] in ["click"])
    ]

    logger.info(f" >Found {len(input_fields)} input fields and {len(button_fields)} button fields")

    # for input fields
    for idx, field in enumerate(input_fields):
        logger.info(f" >Processing {idx+1}/{len(input_fields)}: tag={field['tag']}, type={field['type']}")
        try:
            indivisual_error = fill_form(field, actions, driver, idx, sleep_time)
            if indivisual_error:
                error.extend(indivisual_error)
        except Exception as e:
            raise RuntimeError(f"Failed to fill form: {e}") from e

    # for button fields
    for field in button_fields:
        try:
            if send:
                # input("\nPress Enter to send form...\n")
                send_status = click_form(field, driver)
                if send_status:
                    logger.info(" >Form sent successfully")
                else:
                    raise RuntimeError("Failed to send form")
            else:
                send_status = True
                logger.info(" >Skipping form submission (send=False)")
        except Exception as e:
            raise RuntimeError(f"Failed to send form: {e}") from e

    return error, send_status


