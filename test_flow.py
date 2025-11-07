"""
Test AllAccess flow without running full bot
Run this to test the ticket selection flow manually
"""
from playwright.sync_api import sync_playwright
from allaccess_flow import handle_allaccess_flow
from logger import Logger
import sys

def test_flow():
    event_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.allaccess.com.ar/event/acdc"
    ticket_type = sys.argv[2] if len(sys.argv) > 2 else "Campo General"
    ticket_count = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    
    print(f"\n🎫 Testing AllAccess Flow")
    print(f"Event: {event_url}")
    print(f"Ticket Type: {ticket_type}")
    print(f"Ticket Count: {ticket_count}\n")
    
    logger = Logger("test")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        success = handle_allaccess_flow(page, logger, event_url, ticket_type, ticket_count)
        
        if success:
            print("\n✅ Flow completed successfully!")
            print("Check if you reached the checkout page.")
        else:
            print("\n❌ Flow failed. Check logs/test.jsonl for details.")
        
        print("\nPress Enter to close browser...")
        input()
        browser.close()

if __name__ == "__main__":
    test_flow()
