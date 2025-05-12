import time
import json
from utilities.google_spreadsheet import *
from utilities.save_file import *
from utilities.logger import logger
from app.output import output_html, output_fields_json
from app.input import input_action_json, input_form
from app.check import check_screenshot

def run_flow(start_row, end_row, spreadsheet, sender_info, screenshot_path, send=False):
    sheet_id = spreadsheet["sheet_id"]
    sheet = spreadsheet["sheet"]
    column_map = spreadsheet["column_map"]
    headder = column_map["headder"]
    credentials_path = spreadsheet["credentials_path"]

    try:
        sheet = certification_google_spreadsheet(sheet_id, sheet, credentials_path)
        if sheet:
            logger.info(f'🟢 Successfully got certification for sheet_1')
        else:
            raise RuntimeError(f'🔴 Failed to get certification for sheet_1')
    except Exception as e:
        raise RuntimeError(f'🔴 Failed to get certification for sheet_1: {e}') from e

    try:
        input_multi_data = input_google_spreadsheet_multi(sheet, column_map, start_row, end_row)
        if input_multi_data:
            logger.info(f'🟢 Successfully input data for sheet_1')
        else:
            raise RuntimeError(f'🔴 Failed to input data for sheet_1')
    except Exception as e:
        raise RuntimeError(f'🔴 Failed to input data for sheet_1: {e}') from e

    row = start_row
    error_count = 0
    for data in input_multi_data:

        if error_count:
            browser.quit()
            if error_count > 100:
                raise RuntimeError(f'🔴 #{row}: got failed multi times')
            try:
                output_status = {}
                output_status["system_status"] = error_log
                output_status = output_google_spreadsheet(sheet, column_map, row, output_status)
                if output_status == True:
                    logger.info(f'🟢 Successfully outputted status')
                else:
                    raise RuntimeError(f'🔴 Failed to output status')
            except Exception as e:
                raise RuntimeError(f'🔴 Failed to output status: {e}') from e
            row += 1

        error_log = None
        logger.info(f"==starting for #{row}===")
        logger.info(f"（error_count: {error_count}）")

        name = data["basic_name"]
        url = data["basic_url"]
        sentence = data["basic_sentence"]
        status = data["system_status"]
        num = data["system_num"]

        if not name:
            logger.warning(f"🟡 #{row} does not have a name. Going to next row.")
            row += 1
            continue

        if not url:
            logger.warning(f"🟡 #{row} does not have a url. Going to next row.")
            row += 1
            continue

        if status == 'completed':
            logger.warning(f"🟡 #{row} is already completed. Going to next row.")
            row += 1
            continue

        logger.info(f"🔄 1. Getting fixed html from {url[:10]}..")
        
        try:
            fixed_html, browser = output_html(url)
            if fixed_html:
                logger.info(f'🟢 Successfully got fixed html from {url[:10]}..')
            else:
                logger.error(f'🔴 Failed to get fixed html from {url[:10]}..')
                error_count += 1
                error_log = 'Could not get fixed html / Selenium error'
                continue
        except Exception as e:
            logger.error(f'🔴 Failed to get fixed html from {url[:10]}..: {e}')
            error_count += 1
            error_log = 'Could not get fixed html / Selenium error'
            continue
        
        if len(fixed_html) > 25000:
            logger.error(f'🔴 HTML is too long')
            error_count += 1
            error_log = 'HTML is too long'
            continue

        logger.info(f"🔄 2. Getting fields from {url[:10]}..")

        try:
            fields = output_fields_json(fixed_html)
            if fields:
                logger.info(f'🟢 Successfully got fields from {url[:10]}..')
            else:
                logger.error(f'🔴 Failed to get fields from {url[:10]}..')
                error_count += 1
                error_log = 'Could not get fields / Not a form page / GPT response error'
                continue
        except Exception as e:
            logger.error(f'🔴 Failed to get fields from {url[:10]}..: {e}')
            error_count += 1
            error_log = 'Could not get fields / Not a form page / GPT response error'
            continue
        
        if len(fields) < 3:
            logger.error(f'🔴 Fields are too short')
            error_count += 1
            error_log = 'Fields are too short / Not a form page'
            continue
        
        logger.info(f"--------------------------------")
        logger.info(json.dumps(fields, indent=2, ensure_ascii=False))
        logger.info(len(fields))
        logger.info(f"--------------------------------")

        logger.info(f"🔄 3. Getting actions from {url[:10]}..")
        
        try:
            fields_actions = input_action_json(fields, sender_info, sentence)
            if fields_actions:
                logger.info(f'🟢 Successfully got actions from {url[:10]}..')
            else:
                logger.error(f'🔴 Failed to get actions from {url[:10]}..')
                error_count += 1
                error_log = 'Could not get actions / GPT response error'
                continue
        except Exception as e:
            logger.error(f'🔴 Failed to get actions from {url[:10]}..: {e}')
            error_count += 1
            error_log = 'Could not get actions / GPT response error'
            continue
        
        logger.info(f"--------------------------------")
        logger.info(json.dumps(fields_actions, indent=2, ensure_ascii=False))
        logger.info(len(fields_actions))
        logger.info(f"--------------------------------")

        logger.info(f"🔄 4. Inputting form from {url[:10]}..")
        
        try:
            input_error, send_status = input_form(fields_actions, browser, send, sleep_time=2)
            if send_status == True:
                logger.info(f'🟢 Successfully inputted form from {url[:10]}..')
            else:
                logger.error(f'🔴 Failed to input form from {url[:10]}..')
                error_count += 1
                error_log = 'Could not input form / Selenium error'
                continue
        except Exception as e:
            logger.error(f'🔴 Failed to input form from {url[:10]}..: {e}')
            error_count += 1
            error_log = 'Could not input form / Selenium error'
            continue
        
        logger.info(f"🔄 5. Checking screenshot from {url[:10]}..")
        time.sleep(5)
        
        if send == True:
            try:
                if send_status == True:
                    screenshot_status = check_screenshot(browser, screenshot_path, num)
                    if screenshot_status == True:
                        logger.info(f'🟢 Successfully checked screenshot from {url[:10]}.. (yes)')
                    elif screenshot_status == False:
                        logger.info(f'🟢 Successfully checked screenshot from {url[:10]}.. (no)')
                else:
                    logger.error(f'🔴 Failed to check screenshot from {url[:10]}..')
                    error_count += 1
                    error_log = 'Could not check screenshot / Selenium error'
                    continue
            except Exception as e:
                logger.error(f'🔴 Failed to check screenshot from {url[:10]}..: {e}')
                error_count += 1
                error_log = 'Could not check screenshot / Selenium error'
                continue
        else:
            screenshot_status = True
            logger.info(f'🟡 Does not require screenshot for {url[:10]}..')

        browser.quit()
        email_status = True

        try:
            overall_status = whats_the_status(send_status, screenshot_status, email_status)
            if overall_status:
                logger.info(f'🟢 Successfully got overall status')
            else:
                logger.error(f'🔴 Failed to get overall status')
                error_count += 1
                error_log = 'Could not get overall status'
                continue
        except Exception as e:
            logger.error(f'🔴 Failed to get overall status: {e}')
            error_count += 1
            error_log = 'Could not get overall status'
            continue

        try:
            output_status_1 = {}
            output_status_1["system_status"] = overall_status
            output_status_1["system_error"] = "\n".join(input_error) if input_error else ""
            output_status = output_google_spreadsheet(sheet, column_map, row, output_status_1)
            if output_status == True:
                logger.info(f'🟢 Successfully outputted status for sheet {name}')
            else:
                logger.error(f'🔴 Failed to output status for sheet {name}')
                error_count += 1
                error_log = 'Could not output status'
                continue
        except Exception as e:
            logger.error(f'🔴 Failed to output status for sheet {name}: {e}')
            error_count += 1
            error_log = 'Could not output status'
            continue

        logger.info(f"==ending for #{row}===")
        error_count = 0
        row += 1

def whats_the_status(input_status, screenshot_status, email_status):
    if input_status == True and screenshot_status == True:
        return 'completed'
    elif input_status == True and screenshot_status == False:
        return 'screenshot_failed'
    elif input_status == False and screenshot_status == True:
        return 'input_failed'
    elif input_status == False and screenshot_status == False:
        return 'other error'
