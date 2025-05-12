import json
import re
from bs4 import BeautifulSoup, Comment
from app.selenium_setting import open_url
from app.chatgpt_setting import chatgpt_4omini
from utilities.logger import logger


#///get_html///
def get_html(url):
    try:
        browser = open_url(url, window_whosh=False)
        html = browser.page_source
        if html:
            return html, browser
        else:
            raise RuntimeError("Failed to get html")
    except Exception as e:
        raise RuntimeError(f"Failed to get html: {e}") from e
    
from bs4 import BeautifulSoup, Comment

def fix_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # formに関係するタグ
    FORM_TAGS = ["form", "input", "select", "textarea", "button", "label"]

    def is_form_related(tag):
        return tag.find(FORM_TAGS) is not None

    # 完全除去する不要タグ（form要素を含まない場合に限る）
    REMOVE_TAGS = ["header", "footer", "nav", "script", "style", "noscript", "meta", "iframe", "link"]
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            if not is_form_related(tag):
                tag.decompose()

    # # タグ構造を壊す：親タグをunwrap（中身だけ残す）
    # UNWRAP_TAGS = ["html", "head", "body", "div", "section", "article", "main", "span"]
    # for tag in soup.find_all(UNWRAP_TAGS):
    #     if not is_form_related(tag):
    #         tag.unwrap()

    # 空タグ（中身なし）を削除
    EMPTY_CONTAINER_TAGS = ["div", "span", "section", "article"]
    for tag in soup.find_all(EMPTY_CONTAINER_TAGS):
        if not tag.text.strip() and not tag.find(True):
            tag.decompose()

    # コメント削除
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    fixed_html = str(soup)

    # 終了タグの消去
    safe_to_remove = [
        "html", "head", "body", "main", "section", "article", "header", "footer", "aside", "nav",
        "div", "span",
        "ul", "ol", "li", "dl", "dt", "dd",
        "b", "i", "u", "strong", "em", "small", "sub", "sup", "mark", "abbr", "cite", "code",
        "hr", "br",
        "table", "thead", "tbody", "tfoot", "tr", "th", "td", "colgroup", "col"
    ]
    pattern = r"</(?:{})>".format("|".join(safe_to_remove))
    fixed_html = re.sub(pattern, "", fixed_html, flags=re.IGNORECASE)

    # 空白行の削除
    fixed_html = "\n".join([line for line in fixed_html.splitlines() if line.strip()])

    return fixed_html

def output_html(url):
    try:
        html, browser = get_html(url)
        if html:
            logger.info(f" >Successfully got html ({len(html)})")
        else:
            raise RuntimeError("Failed to get html")
    except Exception as e:
        raise RuntimeError(f"Failed to get html: {e}") from e
    
    try:
        fixed_html = fix_html(html)
        if fixed_html:
            logger.info(f" >Successfully got fixed html ({len(fixed_html)})")
        else:
            raise RuntimeError("Failed to get fixed html")
    except Exception as e:
        raise RuntimeError(f"Failed to get fixed html: {e}") from e
    
    return fixed_html, browser


#///get_fields///
def create_prompt(fixed_html):
    basic_prompt = """
あなたはHTML解析エンジンです。

以下のHTMLコードの中から、フォームに関連する `input`, `textarea`, `select`, `button` 要素をすべて抽出してください。

【抽出ルール】
input, textarea, select, button を対象とします。

control の設定基準：
・入力や選択を伴う要素は "fill"
・ユーザーが押す操作（送信や選択など）を伴うボタンは "click"
・button タグは type=“submit” の場合は "click"、それ以外も "click" としつつ、意味は near_text などで補足します。

【出力フォーマット】
・各要素について、以下のJSON形式で出力してください。
・コードブロック（```json）などは付けず、プレーンテキストで返してください。

[
  {
    "control": "<fill | click>",
    "tag": "<input | textarea | select | button>",
    "type": "<hiddenなら'hidden'、inputのtype属性値、textareaなら'textarea'、selectなら'select'、buttonなら'button'>",
    "meta": {
      "name": "<name属性値 or 空文字>",
      "label": "<labelタグのテキスト or 空文字>",
      "placeholder": "<placeholder属性値 or 空文字>",
      "id": "<id属性値 or 空文字>",
      "title": "<title属性値 or 空文字>",
      "aria_label": "<aria-label属性値 or 空文字>",
      "near_text": "<inputやtextareaなどに直近で関連付けられそうなテキストノード>",
      "options": "<select の場合は選択肢のラベルリスト。その他は null>"
    }
  },
  ...
]

【詳細ルール】
・各属性が存在しない場合は空文字 "" を指定してください。
・label は <label for="id"> または <label> に囲まれたテキストから取得してください。
・near_text は <p>, <span>, <div> など直前・直上にあるテキストノードから取得してください。

【注意事項】
<form> タグの外に存在する要素も抽出対象としてください。特に以下のような重要要素は、<form> の外に配置されることが多くあります：
・「送信」「確認」などの button 要素
・「個人情報の取り扱いに関する同意」「利用規約への同意」などの checkbox 要素や補足テキスト
これらも他のフォーム要素と同様に抽出し、適切に control, type, meta を設定してください。

以下のHTMLを解析してください。
    """

    overall_prompt = f"""
{basic_prompt}
{fixed_html}
"""

    return overall_prompt

def erase_hidden_field(fields):
    return [field for field in fields if field.get('type') != 'hidden']

def output_fields_json(fixed_html):
    try:
        prompt = create_prompt(fixed_html)
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
    
    if not response:
        raise RuntimeError("Dont see any form related elements")
    
    try:
        response_json = json.loads(response)
        if response_json:
            logger.info(f" >Successfully got response_json")
        else:
            raise RuntimeError("Failed to get response_json")
    except Exception as e:
        raise RuntimeError(f"Failed to convert response to json: {e}") from e
    
    original_fields = response_json

    try:
        fixed_fields = erase_hidden_field(original_fields)
        if fixed_fields:
            logger.info(f" >Successfully erased [{len(original_fields)} → {len(fixed_fields)}] hidden fields")
        else:
            raise RuntimeError("Failed to erase hidden fields")
    except Exception as e:
        raise RuntimeError(f"Failed to erase hidden fields: {e}") from e
    
    return fixed_fields

