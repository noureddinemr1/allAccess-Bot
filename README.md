# AllAccess Bot

Production-ready ticket automation for allaccess.com.ar with Queue-it, reCAPTCHA v2, and multi-account support using Playwright.

## Setup

1. **Install Python 3.10+**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

3. **Configure environment:**
```bash
copy .env.example .env
```

Edit `.env` with your credentials:
```env
CAPTCHA_API_KEY=your_2captcha_api_key_here
EVENT_URL=https://www.allaccess.com.ar/event/your-event-slug
MAX_ACCOUNTS=2
HEADLESS=false
TICKET_TYPE=Campo General
TICKET_COUNT=2
PROXIES=http://user:pass@proxy1:8080,socks5://proxy2:1080
```

4. **Configure accounts:**

Edit `accounts.json` with your login credentials and billing info. Each account requires:
- Login credentials (email, password)
- Billing information (name, document, address, etc.)
- Payment card details

**Security Note:** Use environment-specific accounts.json and never commit real credentials.

## Run

**Normal mode (with browser UI for debugging):**
```bash
python main.py
```

**Headless mode (production):**
```bash
python main.py --headless
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CAPTCHA_API_KEY` | Yes | - | Your 2Captcha API key |
| `EVENT_URL` | Yes | - | Full URL to event page |
| `MAX_ACCOUNTS` | No | 2 | Max concurrent accounts |
| `HEADLESS` | No | false | Run browsers headless |
| `ACCOUNTS_FILE` | No | accounts.json | Path to accounts file |
| `TICKET_TYPE` | No | Campo General | Ticket category name |
| `TICKET_COUNT` | No | 2 | Tickets per account |
| `QUEUE_CHECK_INTERVAL` | No | 5 | Queue polling interval (seconds) |
| `CAPTCHA_TIMEOUT` | No | 120 | Max captcha solve time (seconds) |
| `DEBUG_SCREENSHOTS` | No | true | Save screenshots at each step |
| `TELEGRAM_BOT_TOKEN` | No | - | Optional Telegram notifications |
| `TELEGRAM_CHAT_ID` | No | - | Optional Telegram chat ID |
| `PROXIES` | No | - | Comma-separated proxy list |

## Proxy Configuration

**Format:** `http://user:pass@host:port` or `socks5://host:port`

**Example:**
```env
PROXIES=http://user1:pass1@proxy1.com:8080,socks5://proxy2.com:1080
```

Proxies are cycled per account. If you have 3 accounts and 2 proxies, account 0 uses proxy 0, account 1 uses proxy 1, account 2 uses proxy 0, etc.

## 2Captcha Setup

1. Sign up at https://2captcha.com
2. Get your API key from dashboard
3. Add to `.env`: `CAPTCHA_API_KEY=your_api_key`
4. Ensure you have sufficient balance (≈$0.003 per captcha)

## Output

**Logs:** `logs/account_XX.jsonl` - Compact JSON logs per account
**Screenshots:** `screenshots/account_XX_step_HHMMSS.png` - Debug screenshots
**Report:** `logs/run_report.json` - Aggregate results after each run

## Architecture

```
main.py           → Orchestrator: loads accounts, spawns workers
worker.py         → Per-account flow: browser setup → login → queue → tickets → checkout
config.py         → Environment validation and constants
logger.py         → Compact JSON logging + screenshots
captcha.py        → 2Captcha API integration (submit → poll → inject)
queue_handler.py  → Queue-it detection and session keep-alive
checkout.py       → Ticket selection, billing fill, payment submission
accounts.json     → Account credentials and billing data
```

## Flow

1. **Browser Launch:** Isolated context per account with dedicated proxy
2. **Navigation:** Go to event URL
3. **Queue Handling:** Detect Queue-it, keep session alive until release
4. **Login:** Fill credentials, solve reCAPTCHA if present
5. **Ticket Selection:** Choose ticket type and quantity
6. **Checkout:** Fill billing and payment info
7. **Purchase:** Submit order, detect 3DS or success
8. **Notification:** Log result, send Telegram notification on success

## 3DS Handling

Bot **stops** at 3D Secure authentication and logs `manual_intervention_required`. Check screenshots and complete manually. This is intentional for safety and compliance.

## Troubleshooting

**No accounts running:**
- Check `accounts.json` exists and is valid JSON
- Verify `CAPTCHA_API_KEY` is set

**Queue timeout:**
- Increase `QUEUE_CHECK_INTERVAL` or wait for less busy times
- Queue sessions can expire; bot keeps them alive with minimal interactions

**Captcha failures:**
- Verify 2Captcha balance
- Check `CAPTCHA_API_KEY` is correct
- Increase `CAPTCHA_TIMEOUT` if needed

**Login failures:**
- Verify credentials in `accounts.json`
- Check if account requires email verification
- Review `logs/account_XX.jsonl` for details

**Payment errors:**
- Verify card details in `accounts.json`
- Check billing address matches card
- Some cards may be blocked by site

## Security Best Practices

✅ Never commit `.env` or `accounts.json` with real data
✅ Use separate accounts for automation
✅ Rotate proxies regularly
✅ Monitor 2Captcha costs
✅ Review logs for sensitive data leakage
✅ Use headless mode in production
❌ Do not bypass 3DS authentication
❌ Do not share API keys or proxies
