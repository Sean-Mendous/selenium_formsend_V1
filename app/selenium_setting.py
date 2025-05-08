from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
from utilities.logger import logger

def open_url(url, window_whosh=False):
    chrome_options = Options()
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=chrome_options)
    browser.set_window_size(1280, 800)

    if window_whosh:
        browser.set_window_position(-2000, 0)
    
    browser.get(url)
    return browser

def login(browser, cookie):
    with open(cookie, "r") as file:
        cookies = json.load(file)
    for cookie in cookies:
        browser.add_cookie(cookie)
    browser.refresh()
    return None

def logout(browser, cookie):
    cookies = browser.get_cookies()
    with open(cookie, "w") as file:
        json.dump(cookies, file)
    browser.quit()
    return None
    

if __name__ == "__main__":
    import time
    browser = open_url("https://www.google.com")
    time.sleep(3)
    browser.quit()
