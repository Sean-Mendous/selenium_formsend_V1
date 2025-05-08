import time
from utilities.google_spreadsheet import *
from utilities.save_file import *
from utilities.logger import logger
from app.output_form import output_form
from app.ask_form import ask_form
from app.input_form import input_form
from app.check import check_screenshot

def run_flow(start_row, end_row, spreadsheet, sender_info, screenshot_path):
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
    for data in input_multi_data:
        logger.info(f"==starting for #{row}===")

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

        try:
            form_structure, browser = output_form(url)
            if form_structure:
                logger.info(f'🟢 Successfully got form structure from {url[:10]}..')
            else:
                raise RuntimeError(f'🔴 Failed to get form structure from {url[:10]}..') from e
        except Exception as e:
            raise RuntimeError(f'🔴 Failed to get form structure from {url[:10]}..: {e}') from e

        try:
            actions = ask_form(form_structure, sender_info, sentence)
            if actions:
                logger.info(f'🟢 Successfully got actions from {url[:10]}..')
            else:
                raise RuntimeError(f'🔴 Failed to get actions from {url[:10]}..') from e
        except Exception as e:
            raise RuntimeError(f'🔴 Failed to get actions from {url[:10]}..: {e}') from e
        
        send=False
        
        try:
            input_error, send_status = input_form(form_structure, actions, browser, send, sleep_time=2)
            if send_status == True:
                logger.info(f'🟢 Successfully inputted form from {url[:10]}..')
            else:
                raise RuntimeError(f'🔴 Failed to input form from {url[:10]}..')
        except Exception as e:
            raise RuntimeError(f'🔴 Failed to input form from {url[:10]}..: {e}') from e
        
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
                    raise RuntimeError(f'🔴 Failed to check screenshot from {url[:10]}..') from e
            except Exception as e:
                raise RuntimeError(f'🔴 Failed to check screenshot from {url[:10]}..: {e}') from e
        else:
            screenshot_status = True
            logger.info(f'🟡 Does not require screenshot for {url[:10]}..')

        email_status = True

        try:
            overall_status = whats_the_status(send_status, screenshot_status, email_status)
            if overall_status:
                logger.info(f'🟢 Successfully got overall status')
            else:
                raise RuntimeError(f'🔴 Failed to get overall status')
        except Exception as e:
            raise RuntimeError(f'🔴 Failed to get overall status: {e}') from e

        try:
            output_status_1 = {}
            output_status_1["system_status"] = overall_status
            output_status_1["system_error"] = "\n".join(input_error) if input_error else ""
            output_status = output_google_spreadsheet(sheet, column_map, row, output_status_1)
            if output_status == True:
                logger.info(f'🟢 Successfully outputted status for sheet {name}')
            else:
                raise RuntimeError(f'🔴 Failed to output status for sheet {name}') from e
        except Exception as e:
            raise RuntimeError(f'🔴 Failed to output status for sheet {name}: {e}') from e

        logger.info(f"==ending for #{row}===")
        row += 1

def whats_the_status(input_status, screenshot_status, email_status):
    if input_status == True and screenshot_status == True:
        return 'completed'
    elif input_status == True and screenshot_status == False:
        return 'screenshot_failed'
    elif input_status == False and screenshot_status == True:
        return 'input_failed'
    elif input_status == False and screenshot_status == False:
        return 'error'
