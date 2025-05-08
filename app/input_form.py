import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utilities.logger import logger

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

def send_form(field, driver):
    meta = field["meta"]
    
    # 試す探索パターンリスト
    xpath_candidates = []

    # id
    if meta.get("id"):
        logger.info(f' -using "id"')
        xpath_candidates.append(f"//*[@id='{meta['id']}']")

    # name
    if meta.get("name"):
        logger.info(f' -using "name"')
        xpath_candidates.append(f"//button[@name='{meta['name']}']")
        xpath_candidates.append(f"//input[@name='{meta['name']}']")

    # value (inputの場合)
    if meta.get("placeholder"):
        logger.info(f' -using "placeholder"')
        xpath_candidates.append(f"//input[@value='{meta['placeholder']}']")

    # text系
    for text_val in [meta.get("label"), meta.get("near_text"), meta.get("title"), meta.get("aria_label")]:
        if text_val:
            logger.info(f' -using "text"')
            xpath_candidates.append(f"//button[contains(., '{text_val}')]")
            xpath_candidates.append(f"//input[@value='{text_val}']")

    # fallback: ボタン全部
    xpath_candidates.append("//button")
    logger.info(' -using "fallback"')

    # 探索
    for xpath in xpath_candidates:
        try:
            btn = driver.find_element(By.XPATH, xpath)
            if btn:
                btn.click()
                logger.info(f" -Clicked submit button via xpath: {xpath}")
                return True
        except Exception as e:
            logger.error(f" -Failed to find submit button: {e}")
            continue

    raise RuntimeError(" -Failed to find submit button")

def input_form(fields, actions, driver, send=False, sleep_time=1):
    error = []
    send_status = False

    # extract fields
    input_fields = [
        f for f in fields
            if (f["tag"] in ["input", "textarea", "select"] and f["type"] != "submit")
    ]
    button_fields = [
        f for f in fields
            if (f["tag"] == "button" or (f["tag"] == "input" and f["type"] == "submit"))
    ]

    logger.info(f">Found {len(input_fields)} input fields and {len(button_fields)} button fields")

    # for input fields
    for idx, field in enumerate(input_fields):
        logger.info(f">Processing {idx+1}/{len(input_fields)}: tag={field['tag']}, type={field['type']}")
        try:
            indivisual_error = fill_form(field, actions, driver, idx, sleep_time)
            if indivisual_error:
                error.extend(indivisual_error)
        except Exception as e:
            raise RuntimeError(f" >Failed to fill form: {e}") from e

    # for button fields
    for field in button_fields:
        try:
            if send:  # フラグが立ってるときだけ送信
                input("\nPress Enter to send form...\n")
                send_status = send_form(field, driver)
                if send_status:
                    logger.info(" >Form sent successfully")
                else:
                    raise RuntimeError(" >Failed to send form")
            else:
                send_status = True
                logger.info(" >Skipping form submission (send=False)")
        except Exception as e:
            raise RuntimeError(f" >Failed to send form: {e}") from e

    return error, send_status