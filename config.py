import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")
EVENT_URL = os.getenv("EVENT_URL", "https://www.allaccess.com.ar/event/default")
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", "2"))
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "accounts.json")
TICKET_TYPE = os.getenv("TICKET_TYPE", "Campo General")
TICKET_COUNT = int(os.getenv("TICKET_COUNT", "2"))
QUEUE_CHECK_INTERVAL = int(os.getenv("QUEUE_CHECK_INTERVAL", "5"))
CAPTCHA_TIMEOUT = int(os.getenv("CAPTCHA_TIMEOUT", "120"))
DEBUG_SCREENSHOTS = os.getenv("DEBUG_SCREENSHOTS", "true").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PROXIES_CSV = os.getenv("PROXIES", "")
PROXIES = [p.strip() for p in PROXIES_CSV.split(",") if p.strip()] if PROXIES_CSV else []

Path("logs").mkdir(exist_ok=True)
Path("screenshots").mkdir(exist_ok=True)
Path("profiles").mkdir(exist_ok=True)

def validate_config():
    if not CAPTCHA_API_KEY:
        raise ValueError("CAPTCHA_API_KEY not set in environment")
    if not Path(ACCOUNTS_FILE).exists():
        raise ValueError(f"Accounts file not found: {ACCOUNTS_FILE}")
    return True
