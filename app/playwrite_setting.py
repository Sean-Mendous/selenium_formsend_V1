from playwright.sync_api import sync_playwright

def open_url(url):
    browser = p.chromium.launch(headless=False)  # GUIあり
    page = browser.new_page()
    page.goto(url)
    return page

def get_snapshot(page):
    snapshot = page.accessibility.snapshot()
    return snapshot

if __name__ == "__main__":
    with sync_playwright() as p:
        page = open_url("https://samurai-style.tokyo/#contact")
        snapshot = get_snapshot(page)
        print(snapshot)
