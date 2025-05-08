from bs4 import BeautifulSoup
from app.selenium_setting import open_url
from utilities.logger import logger

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
    
def extract_form_sections(html):
    try:
        html_soup = BeautifulSoup(html, "html.parser")
        form_sections = html_soup.find_all("form")
        if form_sections:
            return form_sections
        else:
            raise RuntimeError("Failed to get form section")
    except Exception as e:
        raise RuntimeError(f"Failed to get form section: {e}") from e
    
def extract_label(tag, soup):
    field_id = tag.get("id")
    if field_id:
        label_tag = soup.find("label", attrs={"for": field_id})
        if label_tag:
            return label_tag.get_text(strip=True)

    parent_label = tag.find_parent("label")
    if parent_label:
        return parent_label.get_text(strip=True)

    return tag.get("placeholder", "") or tag.get("name", "") or ""

def for_input_tag(tag, section, radio_groups, checkbox_groups):
    field_type = tag.get("type", "text")
    meta = {
        "name": tag.get("name"),
        "label": extract_label(tag, section),
        "placeholder": tag.get("placeholder", ""),
        "id": tag.get("id"),
        "title": tag.get("title", ""),
        "aria_label": tag.get("aria-label", ""),
        "near_text": "",
        "options": None
    }

    if field_type == "hidden":
        return None

    # groupの場合は別処理
    if field_type == "radio":
        radio_groups.setdefault(meta["name"], []).append({"value": tag.get("value"), "meta": meta})
        return None
    if field_type == "checkbox":
        checkbox_groups.setdefault(meta["name"], []).append({"value": tag.get("value"), "meta": meta})
        return None

    return meta, field_type

def for_textarea_tag(tag, section):
    meta = {
        "name": tag.get("name"),
        "label": extract_label(tag, section),
        "placeholder": tag.get("placeholder", ""),
        "id": tag.get("id"),
        "title": tag.get("title", ""),
        "aria_label": tag.get("aria-label", ""),
        "near_text": "",
        "options": None
    }
    return meta, "textarea"

def for_select_tag(tag, section):
    options = [opt.get_text(strip=True) for opt in tag.find_all("option") if opt.get_text(strip=True)]
    meta = {
        "name": tag.get("name"),
        "label": extract_label(tag, section),
        "placeholder": tag.get("placeholder", ""),
        "id": tag.get("id"),
        "title": tag.get("title", ""),
        "aria_label": tag.get("aria-label", ""),
        "near_text": "",
        "options": options
    }
    return meta, "select"

def for_button_tag(tag, section):
    meta = {
        "name": tag.get("name"),
        "label": extract_label(tag, section),
        "placeholder": tag.get("placeholder", ""),
        "id": tag.get("id"),
        "title": tag.get("title", ""),
        "aria_label": tag.get("aria-label", ""),
        "near_text": (tag.text.strip() if tag.text.strip() else "")
    }
    return meta, "button"


def extract_fields(section):
    fields = []
    radio_groups = {}
    checkbox_groups = {}

    for tag in section.find_all(["input", "textarea", "select", "button"]):
        if tag.name == "input":
            result = for_input_tag(tag, section, radio_groups, checkbox_groups)
            if result:
                meta, type_ = result
                fields.append({
                    "tag": "input",
                    "type": type_,
                    "meta": meta
                })
        elif tag.name == "textarea":
            meta, type_ = for_textarea_tag(tag, section)
            fields.append({
                "tag": "textarea",
                "type": type_,
                "meta": meta
            })
        elif tag.name == "select":
            meta, type_ = for_select_tag(tag, section)
            fields.append({
                "tag": "select",
                "type": type_,
                "meta": meta
            })
        elif tag.name == "button":
            meta, type_ = for_button_tag(tag, section)
            fields.append({
                "tag": "button",
                "type": type_,
                "meta": meta
            })

    # グループ処理も統一形式で
    for name, options_list in radio_groups.items():
        meta = {
            "name": name,
            "label": "",
            "placeholder": "",
            "id": None,
            "title": "",
            "aria_label": "",
            "near_text": "",
            "options": [opt["value"] for opt in options_list]
        }
        fields.append({
            "tag": "radio_group",
            "type": "radio_group",
            "meta": meta
        })

    for name, options_list in checkbox_groups.items():
        meta = {
            "name": name,
            "label": "",
            "placeholder": "",
            "id": None,
            "title": "",
            "aria_label": "",
            "near_text": "",
            "options": [opt["value"] for opt in options_list]
        }
        fields.append({
            "tag": "checkbox_group",
            "type": "checkbox_group",
            "meta": meta
        })

    return fields

def detect_form(form_sections, min_fields=3):
    valid_forms = []
    for form in form_sections:
        inputs = form.find_all(["input", "textarea", "select", "button"])
        if len(inputs) >= min_fields:
            valid_forms.append(form)
    
    if valid_forms:
        return valid_forms[0]
    else:
        return False

def output_form(url):
    try:
        html, browser = get_html(url)
        if html:
            logger.info(f" >Successfully got html")
        else:
            raise RuntimeError(" >Failed to get html")
    except Exception as e:
        raise RuntimeError(f" >Failed to get html: {e}") from e
    
    try:
        all_sections = extract_form_sections(html)
        if all_sections:
            logger.info(f" >Successfully got form section")
        else:
            raise RuntimeError(" >Failed to get form section")
    except Exception as e:
        raise RuntimeError(f" >Failed to get form section: {e}") from e

    try:
        section = detect_form(all_sections, min_fields=3)
        if section:
            logger.info(f" >This is a valid form")
        else:
            raise RuntimeError(" >This is not a valid form")
    except Exception as e:
        raise RuntimeError(f" >Failed to detect form: {e}") from e
    
    try:
        fields = extract_fields(section)
        if fields:
            logger.info(f" >Successfully got fields")
        else:
            raise RuntimeError(" >Failed to get fields")
    except Exception as e:
        raise RuntimeError(f" >Failed to get fields: {e}") from e
    
    print(fields)
    
    if browser:
        return fields, browser
    else:
        raise RuntimeError(" >Failed to get browser")
    
    
    


