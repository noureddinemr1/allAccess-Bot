import json
from pathlib import Path
from datetime import datetime
import os
import requests

def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    Path("screenshots").mkdir(exist_ok=True)

def log_to_file(account_id, data):
    timestamp = datetime.now().isoformat()
    log_entry = {"timestamp": timestamp, "account_id": account_id, **data}
    
    log_file = Path("logs") / f"account_{account_id}.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    print(f"[Account {account_id}] {data.get('step', 'log')}")

async def take_screenshot(page, account_id, name):
    filename = f"screenshots/account_{account_id}_{name}_{datetime.now().strftime('%H%M%S')}.png"
    await page.screenshot(path=filename)

def notify(message):
    print(message)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
                "chat_id": chat_id,
                "text": message
            })
        except:
            pass
