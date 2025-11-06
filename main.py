import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
import os
from bot import TicketBot
from utils import setup_logging, notify

load_dotenv()

def load_config():
    with open("config.json") as f:
        return json.load(f)

def parse_accounts():
    accounts_str = os.getenv("ACCOUNTS", "")
    if not accounts_str:
        return []
    accounts = []
    for acc in accounts_str.split(","):
        parts = acc.strip().split(":")
        if len(parts) >= 3:
            email, password = parts[0], parts[1]
            proxy = ":".join(parts[2:])
            accounts.append({"email": email, "password": password, "proxy": proxy})
    return accounts

async def run_account(account, config, account_id):
    bot = TicketBot(account, config, account_id)
    try:
        success = await bot.run()
        if success:
            notify(f"✅ Account {account['email']} succeeded!")
        return success
    except Exception as e:
        bot.log({"error": str(e)})
        return False
    finally:
        await bot.cleanup()

async def main():
    setup_logging()
    config = load_config()
    accounts = parse_accounts()
    
    if not accounts:
        print("❌ No accounts found in ACCOUNTS env variable")
        return
    
    max_accounts = min(config.get("max_accounts", len(accounts)), len(accounts))
    accounts = accounts[:max_accounts]
    
    print(f"🚀 Starting {len(accounts)} account(s)...")
    
    tasks = [run_account(acc, config, i) for i, acc in enumerate(accounts)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(results)
    print(f"\n✅ {success_count}/{len(accounts)} accounts succeeded")

if __name__ == "__main__":
    asyncio.run(main())
