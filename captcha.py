import requests
import time
from typing import Optional
from config import CAPTCHA_API_KEY, CAPTCHA_TIMEOUT

TWOCAPTCHA_IN_URL = "http://2captcha.com/in.php"
TWOCAPTCHA_RES_URL = "http://2captcha.com/res.php"

def solve_recaptcha_v2(site_key: str, page_url: str) -> Optional[str]:
    """Submit recaptcha task and poll for solution."""
    response = requests.post(TWOCAPTCHA_IN_URL, data={
        "key": CAPTCHA_API_KEY,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
        "json": 1
    }, timeout=30)
    
    result = response.json()
    if result.get("status") != 1:
        raise Exception(f"2Captcha submission failed: {result}")
    
    captcha_id = result.get("request")
    start_time = time.time()
    
    while time.time() - start_time < CAPTCHA_TIMEOUT:
        time.sleep(5)
        
        check_response = requests.get(TWOCAPTCHA_RES_URL, params={
            "key": CAPTCHA_API_KEY,
            "action": "get",
            "id": captcha_id,
            "json": 1
        }, timeout=30)
        
        check_result = check_response.json()
        
        if check_result.get("status") == 1:
            return check_result.get("request")
        elif check_result.get("request") == "CAPCHA_NOT_READY":
            continue
        else:
            raise Exception(f"2Captcha solve failed: {check_result}")
    
    raise Exception("Captcha timeout exceeded")

def inject_token(page, token: str) -> bool:
    """Inject recaptcha token using multiple strategies."""
    try:
        page.evaluate(f"""
            (token) => {{
                const textarea = document.getElementById('g-recaptcha-response');
                if (textarea) {{
                    textarea.innerHTML = token;
                    textarea.value = token;
                }}
                
                if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {{
                    Object.keys(window.___grecaptcha_cfg.clients).forEach(key => {{
                        const client = window.___grecaptcha_cfg.clients[key];
                        Object.keys(client).forEach(id => {{
                            if (client[id] && client[id].callback) {{
                                client[id].callback(token);
                            }}
                        }});
                    }});
                }}
            }}
        """, token)
        return True
    except Exception as e:
        return False

def extract_sitekey(page) -> Optional[str]:
    """Extract recaptcha sitekey from page."""
    try:
        sitekey = page.evaluate("""() => {
            const iframe = document.querySelector('iframe[src*="recaptcha"]');
            if (iframe) {
                const url = new URL(iframe.src);
                return url.searchParams.get('k');
            }
            
            const divs = document.querySelectorAll('div[data-sitekey]');
            if (divs.length > 0) {
                return divs[0].getAttribute('data-sitekey');
            }
            
            return null;
        }""")
        return sitekey
    except:
        return None
