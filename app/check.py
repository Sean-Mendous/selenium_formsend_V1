import os
from openai import OpenAI
from dotenv import load_dotenv
import base64
from utilities.logger import logger

def save_screenshot(browser, output_path, id):
    image_path = f"{output_path}/{id}.png"
    os.makedirs(output_path, exist_ok=True)
    browser.save_screenshot(image_path)
    browser.quit()
    logger.info(f" -saved screenshot {image_path}")
    return image_path

def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        base64_encoded = base64.b64encode(img_file.read()).decode('utf-8')
    return base64_encoded

def chatgpt_4o_image_model(encoded_image, prompt):
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
    model="gpt-4o",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
            ]}
        ],
        temperature=0
    )

    result = response.choices[0].message.content.strip().lower()
    return result

def check_screenshot(browser, screenshot_path, id):

    prompt = """
あなたはウェブフォーム送信の確認担当です。
以下のスクリーンショット画像が「フォーム送信が正常に完了したことを示す画面」であるかを判定してください。
出力は "yes" か "no" のみとしてください。
"""

    try:
        image_path = save_screenshot(browser, screenshot_path, id)
        if image_path:
            logger.info(f" >Successfully saved screenshot")
        else:
            raise RuntimeError(f" >Failed to save screenshot")
    except Exception as e:
        raise RuntimeError(f" >failed to save screenshot: {e}") from e
   
    try:
        encoded_image = encode_image(image_path)
        if encoded_image:
            logger.info(f" >Successfully encoded image")
        else:
            raise RuntimeError(f" >Failed to encode image")
    except Exception as e:
        raise RuntimeError(f" >failed to encode image: {e}") from e

    try:
        result = chatgpt_4o_image_model(encoded_image, prompt)
        if result:
            logger.info(f" >Successfully checked screenshot")
        else:
            raise RuntimeError(f" >Failed to check screenshot")
    except Exception as e:
        raise RuntimeError(f" >failed to check screenshot: {e}") from e

    try:
        if result == "yes":
            logger.info(f" >Successfully checked screenshot (yes)")
            return True
        elif result == "no":
            logger.info(f" >Successfully checked screenshot (no)")
            return False
        else:
            raise RuntimeError(f" >Failed to check screenshot")
    except Exception as e:
        raise RuntimeError(f" >failed to check screenshot: {e}") from e
    

