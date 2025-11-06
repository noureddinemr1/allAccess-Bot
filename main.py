import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import requests
import config
from worker import run_worker

def load_accounts() -> List[Dict[str, Any]]:
    """Load accounts from JSON file."""
    with open(config.ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_proxy_for_account(account_index: int) -> str:
    """Get proxy for account by index, cycling if needed."""
    if not config.PROXIES:
        return None
    return config.PROXIES[account_index % len(config.PROXIES)]

def notify_success(account_email: str, order_number: str = None):
    """Send success notification."""
    message = f"✅ Purchase successful for {account_email}"
    if order_number:
        message += f"\nOrder: {order_number}"
    
    print(f"\n{message}\n")
    
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": config.TELEGRAM_CHAT_ID, "text": message},
                timeout=10
            )
        except:
            pass

def save_report(results: List[Dict[str, Any]]):
    """Save aggregate JSON report."""
    report = {
        "total_accounts": len(results),
        "successful": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "results": results
    }
    
    report_file = Path("logs") / "run_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Report saved to {report_file}")
    print(f"✅ Successful: {report['successful']}/{report['total_accounts']}")
    print(f"❌ Failed: {report['failed']}/{report['total_accounts']}")

def main():
    parser = argparse.ArgumentParser(description="AllAccess Ticket Bot")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()
    
    try:
        config.validate_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    accounts = load_accounts()
    if not accounts:
        print("❌ No accounts found in accounts.json")
        return
    
    max_accounts = min(config.MAX_ACCOUNTS, len(accounts))
    accounts = accounts[:max_accounts]
    
    print(f"🚀 Starting bot for {len(accounts)} account(s)")
    print(f"🎯 Event URL: {config.EVENT_URL}")
    print(f"🎫 Ticket: {config.TICKET_TYPE} x{config.TICKET_COUNT}")
    print(f"👁️  Headless: {args.headless or config.HEADLESS}")
    print(f"🌐 Proxies: {len(config.PROXIES) if config.PROXIES else 0}")
    print()
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_accounts) as executor:
        futures = {}
        
        for i, account in enumerate(accounts):
            proxy = get_proxy_for_account(i)
            account_id = f"{i:02d}"
            future = executor.submit(run_worker, account, account_id, proxy, args.headless)
            futures[future] = (account_id, account.get("email"))
        
        for future in as_completed(futures):
            account_id, email = futures[future]
            try:
                result = future.result()
                results.append(result)
                
                if result.get("success"):
                    notify_success(email, result.get("order_number"))
                else:
                    print(f"❌ Account {account_id} ({email}) failed: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Account {account_id} ({email}) exception: {str(e)}")
                results.append({
                    "account_id": account_id,
                    "email": email,
                    "success": False,
                    "error": f"executor_exception: {str(e)}"
                })
    
    save_report(results)

if __name__ == "__main__":
    main()
