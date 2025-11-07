"""
Debug script to analyze AllAccess.com.ar page structure
Run this to see the actual HTML elements on the page
"""
from playwright.sync_api import sync_playwright
import json

def analyze_page(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print(f"\n🔍 Analyzing: {url}\n")
        page.goto(url, wait_until="networkidle")
        
        print("=" * 60)
        print("PAGE TITLE:", page.title())
        print("=" * 60)
        
        # Check for ticket/buy buttons
        print("\n📍 BUTTONS WITH 'ENTRADA', 'TICKET', 'COMPRAR', 'VER':")
        buttons = page.query_selector_all('button, a[class*="btn"], a[class*="button"]')
        for i, btn in enumerate(buttons[:20]):
            try:
                text = btn.text_content()
                if text and any(word in text.lower() for word in ['entrada', 'ticket', 'comprar', 'ver', 'buy']):
                    classes = btn.get_attribute('class') or ''
                    href = btn.get_attribute('href') or ''
                    print(f"  [{i}] Text: '{text.strip()}' | Class: {classes[:50]} | Href: {href[:50]}")
            except:
                pass
        
        # Check for event cards/links
        print("\n📍 EVENT CARDS/LINKS:")
        event_links = page.query_selector_all('a[href*="/event/"], a[href*="/page/"]')
        for i, link in enumerate(event_links[:10]):
            try:
                href = link.get_attribute('href') or ''
                text = link.text_content().strip()
                classes = link.get_attribute('class') or ''
                print(f"  [{i}] Href: {href} | Text: '{text[:30]}' | Class: {classes[:40]}")
            except:
                pass
        
        # Check for images that might be clickable
        print("\n📍 CLICKABLE IMAGES (ticket cards):")
        images = page.query_selector_all('img[alt*="vent"], a img, div[class*="event"] img, div[class*="card"] img')
        for i, img in enumerate(images[:10]):
            try:
                alt = img.get_attribute('alt') or ''
                parent = img.evaluate('el => el.parentElement.tagName')
                parent_href = img.evaluate('el => el.parentElement.href') or ''
                print(f"  [{i}] Alt: '{alt[:50]}' | Parent: {parent} | Href: {parent_href[:50]}")
            except:
                pass
        
        # Check main content sections
        print("\n📍 MAIN CONTENT SECTIONS:")
        sections = page.query_selector_all('div[class*="event"], div[class*="card"], section, article')
        for i, section in enumerate(sections[:5]):
            try:
                classes = section.get_attribute('class') or ''
                if classes:
                    print(f"  [{i}] Class: {classes[:60]}")
            except:
                pass
        
        # Check for date selectors
        print("\n📍 DATE/TIME SELECTORS:")
        dates = page.query_selector_all('[class*="date"], [class*="fecha"], button[data-date]')
        for i, date in enumerate(dates[:10]):
            try:
                text = date.text_content()
                classes = date.get_attribute('class') or ''
                print(f"  [{i}] Text: '{text.strip()[:30]}' | Class: {classes[:50]}")
            except:
                pass
        
        # Check for ticket type options (Campo General, etc)
        print("\n📍 TICKET TYPE OPTIONS:")
        types = page.query_selector_all('[class*="ticket"], [class*="sector"], [class*="ubicacion"]')
        for i, t in enumerate(types[:10]):
            try:
                text = t.text_content()
                if text and len(text.strip()) > 0:
                    classes = t.get_attribute('class') or ''
                    print(f"  [{i}] Text: '{text.strip()[:40]}' | Class: {classes[:50]}")
            except:
                pass
        
        # Check login status
        print("\n📍 LOGIN/REGISTER ELEMENTS:")
        login_elements = page.query_selector_all('a[href*="login"], button[class*="login"], a:has-text("INGRESAR"), a:has-text("REGISTRAR")')
        for i, elem in enumerate(login_elements[:5]):
            try:
                text = elem.text_content()
                href = elem.get_attribute('href') or ''
                print(f"  [{i}] Text: '{text.strip()}' | Href: {href}")
            except:
                pass
        
        print("\n" + "=" * 60)
        print("✅ Analysis complete. Press Enter to close browser...")
        input()
        browser.close()

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.allaccess.com.ar/page/Airbag"
    analyze_page(url)
