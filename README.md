# AllAccess Bot

Minimal ticket-buying automation for allaccess.com.ar with Queue-it, reCAPTCHA v2, and multi-account support.

## Setup

1. Install Python 3.9+
2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Copy `.env.example` to `.env` and configure:

```env
CAPTCHA_API_KEY=your_2captcha_api_key
TELEGRAM_BOT_TOKEN=optional_telegram_bot_token
TELEGRAM_CHAT_ID=optional_telegram_chat_id
ACCOUNTS=email1:pass1:http://user:pass@proxy1:port,email2:pass2:http://user:pass@proxy2:port
```

**ACCOUNTS format:** Each account is `email:password:proxy_url` separated by commas. Proxy format: `http://user:pass@host:port` or `socks5://host:port`.

4. Edit `config.json` for runtime settings (headless, ticket count, etc).

## Run

```bash
python main.py
```

Logs saved to `logs/` directory. Screenshots saved on key steps if `debug_screenshots` is enabled.

## Config Options

- `headless`: Run browsers without UI (false for debugging)
- `max_accounts`: Max concurrent accounts
- `ticket_type`: Seat category (e.g., "Campo General")
- `ticket_count`: Tickets per account
- `debug_screenshots`: Save screenshots at each step

## 2Captcha Setup

Get API key from https://2captcha.com and add to `.env` as `CAPTCHA_API_KEY`.

## Proxy Setup

One proxy per account in ACCOUNTS env var. Format: `http://user:pass@host:port` or `socks5://host:port`.

## Notes

- Bot stops at 3DS/interactive payment. Check logs for manual intervention.
- Queue-it sessions maintained automatically.
- Each account runs in isolated browser context with dedicated proxy.
