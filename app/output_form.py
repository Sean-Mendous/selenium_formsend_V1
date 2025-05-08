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
    
def extract_form_section(html):
    try:
        html_soup = BeautifulSoup(html, "html.parser")
        form_section = html_soup.find("form")
        if form_section:
            return form_section
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
    name = tag.get("name")
    field_id = tag.get("id")
    label = extract_label(tag, section)
    placeholder = tag.get("placeholder", "")
    title = tag.get("title", "")
    aria_label = tag.get("aria-label", "")

    # near_text: 直前のテキストノード（p, span, divなど）
    near_text = ""
    prev = tag.find_previous(string=True)
    if prev and prev.strip():
        near_text = prev.strip()

    meta = {
        "name": name,
        "label": label,
        "placeholder": placeholder,
        "id": field_id,
        "title": title,
        "aria_label": aria_label,
        "near_text": near_text
    }

    if field_type == "hidden":
        return None

    if field_type == "radio" and name:
        radio_groups.setdefault(name, []).append({
            "value": tag.get("value"),
            "meta": meta
        })
        return None

    if field_type == "checkbox" and name:
        checkbox_groups.setdefault(name, []).append({
            "value": tag.get("value"),
            "meta": meta
        })
        return None

    field = {
        "tag": "input",
        "type": field_type,
        "meta": meta
    }

    if field_type == "file":
        field["accept"] = tag.get("accept", "")

    return field

def for_textarea_tag(tag, section):
    name = tag.get("name")
    field_id = tag.get("id")
    label = extract_label(tag, section)

    return {
        "tag": "textarea",
        "type": "textarea",
        "id": field_id,
        "name": name,
        "label": label
    }

def for_select_tag(tag, section):
    name = tag.get("name")
    field_id = tag.get("id")
    label = extract_label(tag, section)
    options = [opt.get_text(strip=True) for opt in tag.find_all("option") if opt.get_text(strip=True)]

    return {
        "tag": "select",
        "type": "select",
        "id": field_id,
        "name": name,
        "label": label,
        "options": options
    }

def process_radio_group(radio_groups):
    return [
        {
            "type": "radio_group",
            "name": name,
            "options": options
        }
        for name, options in radio_groups.items()
    ]

def process_checkbox_group(checkbox_groups):
    return [
        {
            "type": "checkbox_group",
            "name": name,
            "options": options
        }
        for name, options in checkbox_groups.items()
    ]

def extract_fields(section):
    fields = []
    radio_groups = {}
    checkbox_groups = {}

    for tag in section.find_all(["input", "textarea", "select"]):
        if tag.name == "input":
            result = for_input_tag(tag, section, radio_groups, checkbox_groups)
            if result:
                fields.append(result)
        elif tag.name == "textarea":
            fields.append(for_textarea_tag(tag, section))
        elif tag.name == "select":
            fields.append(for_select_tag(tag, section))

    # グループ処理後に追加
    fields.extend(process_radio_group(radio_groups))
    fields.extend(process_checkbox_group(checkbox_groups))

    return fields

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
        section = extract_form_section(html)
        if section:
            logger.info(f" >Successfully got form section")
        else:
            raise RuntimeError(" >Failed to get form section")
    except Exception as e:
        raise RuntimeError(f" >Failed to get form section: {e}") from e
    
    try:
        fields = extract_fields(section)
        if fields:
            logger.info(f" >Successfully got fields")
        else:
            raise RuntimeError(" >Failed to get fields")
    except Exception as e:
        raise RuntimeError(f" >Failed to get fields: {e}") from e
    
    if browser:
        return fields, browser
    else:
        raise RuntimeError(" >Failed to get browser")
    
    
    


