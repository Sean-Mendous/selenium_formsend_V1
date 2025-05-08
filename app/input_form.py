import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utilities.logger import logger


def fill_input(driver, name, value, error_log):
    try:
        field = driver.find_element(By.NAME, name)
        field.clear()
        field.send_keys(value)
        logger.info(f" - 👍 input: {name} = {value}")
    except Exception as e:
        logger.error(f" - 🖕 Could not input: {name} - {e}")
        error_log.append(f"{name}={value} - {e}")

def check_checkbox(driver, name, value, error_log):
    try:
        checkbox = driver.find_element(By.XPATH, f"//input[@type='checkbox'][@name='{name}'][@value='{value}']")
        if not checkbox.is_selected():
            checkbox.click()
        logger.info(f" - 👍 check: {name} = {value}")
    except Exception as e:
        logger.error(f" - 🖕 Could not check: {name} - {e}")
        error_log.append(f"{name}={value} - {e}")


def uncheck_checkbox(driver, name, value, error_log):
    try:
        checkbox = driver.find_element(By.XPATH, f"//input[@type='checkbox'][@name='{name}'][@value='{value}']")
        if checkbox.is_selected():
            checkbox.click()
        logger.info(f" - 👍 uncheck: {name} = {value}")
    except Exception as e:
        logger.error(f" - 🖕 Could not uncheck: {name} - {e}")
        error_log.append(f"{name}={value} - {e}")


def select_radio(driver, name, value, error_log):
    try:
        radio = driver.find_element(By.XPATH, f"//input[@type='radio'][@name='{name}'][@value='{value}']")
        if not radio.is_selected():
            radio.click()
        logger.info(f" - 👍 select_radio: {name} = {value}")
    except Exception as e:
        logger.error(f" - 🖕 Could not select radio: {name} - {e}")
        error_log.append(f"{name}={value} - {e}")

def click_button(driver, name, error_log):
    clicked = False
    # 1. name/id
    for method in ["name", "id"]:
        try:
            button = driver.find_element(By.__dict__[method.upper()], name)
            button.click()
            logger.info(f" - 👍 click: {method}={name}")
            clicked = True
            break
        except:
            pass

    # 2. button text
    if not clicked:
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.text.strip() == name:
                    btn.click()
                    logger.info(f" - 👍 click: {name}")
                    clicked = True
                    break
        except:
            pass

    # 3. input[type=submit] value
    if not clicked:
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.get_attribute("type") == "submit":
                    if inp.get_attribute("value") == name:
                        inp.click()
                        logger.info(f" - 👍 click: {name}")
                        clicked = True
                        break
        except:
            pass

    if not clicked:
        logger.error(f" - 🖕 Could not find button: {name}")
        error_log.append(f"{name}")

def save_screenshot(browser, identifi_code):
    os.makedirs("screenshots", exist_ok=True)
    browser.save_screenshot(f"screenshots/{identifi_code}.png")
    logger.info(f" - 📸 screenshots/{identifi_code}.png")

def input_form(actions, browser, send=False):
    actions = actions["actions"]
    error = {
        'error_fill': [],
        'error_click': [],
        'error_check': []
    }

    try:
        for i, action in enumerate(actions, start=1):
            logger.info(f" >start input for {i}/{len(actions)}")
            action_type = action.get("type")
            name = action.get("name")
            value = action.get("value")

            if action_type == "fill":
                fill_input(browser, name, value, error['error_fill'])
            elif action_type == "check":
                check_checkbox(browser, name, value, error['error_check'])
            elif action_type == "uncheck":
                uncheck_checkbox(browser, name, value, error['error_check'])
            elif action_type == "select_radio":
                select_radio(browser, name, value, error['error_click'])
            elif action_type == "click":
                input('Do you want to send the form?: ')
                if send:
                    click_button(browser, name, error['error_click'])
        # save_screenshot(browser, identifi_code)
    except Exception as e:
        raise RuntimeError(f" >Could not input form: {e}") from e

    status = True
    return status, error