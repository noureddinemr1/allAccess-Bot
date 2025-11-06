import requests
import asyncio
import os

API_KEY = os.getenv("CAPTCHA_API_KEY")
BASE_URL = "http://2captcha.com"

async def solve_recaptcha(page_url, sitekey, timeout=120):
    response = requests.post(f"{BASE_URL}/in.php", data={
        "key": API_KEY,
        "method": "userrecaptcha",
        "googlekey": sitekey,
        "pageurl": page_url,
        "json": 1
    })
    result = response.json()
    if result.get("status") != 1:
        raise Exception(f"Captcha submission failed: {result}")
    
    captcha_id = result.get("request")
    
    for _ in range(timeout // 5):
        await asyncio.sleep(5)
        check_response = requests.get(f"{BASE_URL}/res.php", params={
            "key": API_KEY,
            "action": "get",
            "id": captcha_id,
            "json": 1
        })
        check_result = check_response.json()
        
        if check_result.get("status") == 1:
            return check_result.get("request")
        elif check_result.get("request") != "CAPCHA_NOT_READY":
            raise Exception(f"Captcha solve failed: {check_result}")
    
    raise Exception("Captcha timeout")
