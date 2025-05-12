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
あなたの役割は、fieldsの順番に沿って、それぞれの入力値（value）を指定し、最終的に JSON 形式で出力することです。

出力仕様:
・出力はJSON形式で “actions” キーを持つオブジェクトとしてください。
・“actions” の値は、フォーム構造情報の順番に対応する値のリストです。
・値の数は必ずfieldsの数と一致させてください。
・各typeに合った形式で返してください。

【typeごとの入力形式】
・type=“text”: 文字列（例: “山田太郎”）
・type=“email”: メールアドレス形式（例: “example@example.com”）
・type=“tel”: 電話番号形式（例: “0312345678”）
・type=“date”: “yyyymmdd” 形式の8桁日付（例: “20240512”）
・type=“textarea”: 問い合わせ内容などの自由記述（例: “サービスについて問い合わせます”）
・type=“radio”: 選択する項目に “True”、選択しない項目に “” を入れてください。
・type=“checkbox”: チェックする項目に “True”、チェックしない項目に “” を入れてください。
・type=“hidden”: 値の入力は不要なため、””（空文字）を入れてください。
・type=“button”: 動作対象ではないため、””（空文字）を入れてください。

【radioとcheckboxに関する補足】
・radioやcheckboxは同じname属性を持つものを同一グループとみなしますが、本プロンプトでは各項目を個別のフィールドとして出力しています。
・そのため、選択する項目に “True”、選択しない項目に “” を設定してください。
・「利用規約への同意」や「個人情報の取り扱いへの同意」などに関するものは、基本的に “True” を設定してください。

【その他ルール】
・問い合わせ内容などの自由記述は、通常はtagがのものに含めてください。
・入力が不要、または該当情報が不明な場合は、””（空文字）を返してください。

【注意事項】
・fieldsの順番は厳守してください。
・fieldsの数は必ずfieldsの数と一致させてください。

出力形式の例:
{
    “actions”: [
        “20240512”,
        “山田太郎”,
        “example@example.com”,
        “True”,
        “”,
        “True”
    ]
}

※必ず上記のJSON形式でのみ出力してください（マークダウンコードブロックは使用しないでください）。
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

def merge_action_to_fields(fields, actions):
    actions = actions["actions"]

    for i, field in enumerate(fields):
        if field["control"] == "fill":
            field["action"] = actions[i]
        elif field["control"] == "click":
            field["action"] = ""
        else:
            field["action"] = ""

    return fields

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
    
    logger.info(f"--------------------------------")
    logger.info(json.dumps(response_json, indent=2, ensure_ascii=False))
    logger.info(f"--------------------------------")
    
    try:
        merged_fields = merge_action_to_fields(original_fields, response_json)
        if merged_fields:
            logger.info(f" >Successfully merged fields")
        else:
            raise RuntimeError("Failed to merge fields")
    except Exception as e:
        raise RuntimeError(f"Failed to merge fields: {e}") from e
    
    return merged_fields


#///input_form///
def find_element(browser, meta, tag):
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
            return browser.find_element(method, value)
        except:
            continue
    return None

def fill_form(field, browser, sleep_time):
    error = []

    value = field["action"]
    tag = field["tag"]
    type_type = field["type"]
    meta = field["meta"]

    try:
        elem = find_element(browser, meta, tag)
        if not elem:
            raise Exception("Element not found")

        if tag == "textarea":
            elem.clear()
            elem.send_keys(value)
            logger.info(f" - textarea input: {meta.get('name')} = {value}")
        elif tag == "select":
            from selenium.webdriver.support.ui import Select
            select = Select(elem)
            select.select_by_visible_text(value)
            logger.info(f" - select: {meta.get('name')} = {value}")
        elif tag == "input":
            if type_type == "radio" or type_type == "checkbox":
                # label_label = browser.find_element(By.XPATH, f"//label[contains(text(), '{meta['label']}')]")
                label_label = browser.find_element(By.XPATH, f"//label[@for='{meta['id']}']")
                if value:
                    if not label_label.is_selected():
                        label_label.click()
                        logger.info(f" - {type_type}: {meta.get('name')} = True")
                    else:
                        logger.info(f" - {type_type}: {meta.get('name')} = True (already selected)")
                else:
                    if label_label.is_selected():
                        label_label.click()
                        logger.info(f" - {type_type}: {meta.get('name')} = False")
                    else:
                        logger.info(f" - {type_type}: {meta.get('name')} = False (already unselected)")
            else:
                elem.clear()
                elem.send_keys(value)
                logger.info(f" - input: {meta.get('name')} = {value}")
    
        time.sleep(sleep_time)

    except Exception as e:
        logger.error(f" - error on {meta.get('name')}: {e}")
        error.append(f"{meta.get('name')}: {e}")

    return error

def click_form(field, browser):
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
            btn = browser.find_element(By.XPATH, xpath)
            if btn:
                btn.click()
                logger.info(f" - Clicked submit button via xpath: {xpath}")
                return True
        except Exception as e:
            logger.error(f"Failed to find submit button: {e}")
            continue

    raise RuntimeError("Failed to find submit button")

def input_form(merged_fields, browser, send=False, sleep_time=1):
    error = []
    send_status = False

    # extract fields
    input_fields = [
        f for f in merged_fields
            if (f["control"] in ["fill"])
    ]
    button_fields = [
        f for f in merged_fields
            if (f["control"] in ["click"])
    ]

    logger.info(f" >Found {len(input_fields)} input fields and {len(button_fields)} button fields")

    # for input fields
    for i, field in enumerate(input_fields):
        logger.info(f" >Input: processing {i+1}/{len(input_fields)}: tag={field['tag']}, type={field['type']}")
        try:
            indivisual_error = fill_form(field, browser, sleep_time)
            if indivisual_error:
                error.extend(indivisual_error)
        except Exception as e:
            raise RuntimeError(f"Failed to fill form: {e}") from e

    # for button fields
    for i, field in enumerate(button_fields):
        logger.info(f" >Button: processing {i+1}/{len(button_fields)}: tag={field['tag']}, type={field['type']}")
        try:
            if send:
                send_status = click_form(field, browser)
                if send_status:
                    logger.info(" >Form sent successfully")
                else:
                    raise RuntimeError("Failed to send form")
            else:
                send_status = True
                logger.info(" >Skipping form submission (send=False)")
        except Exception as e:
            logger.error(f"Failed to send form: {e}")

    return error, send_status


