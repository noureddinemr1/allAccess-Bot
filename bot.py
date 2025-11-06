from playwright.async_api import async_playwright
import asyncio
from captcha import solve_recaptcha
from utils import log_to_file, take_screenshot
from queue_handler import handle_queue

class TicketBot:
    def __init__(self, account, config, account_id):
        self.account = account
        self.config = config
        self.account_id = account_id
        self.browser = None
        self.context = None
        self.page = None
        
    def log(self, data):
        log_to_file(self.account_id, data)
        
    async def screenshot(self, name):
        if self.config.get("debug_screenshots"):
            await take_screenshot(self.page, self.account_id, name)
    
    async def setup_browser(self):
        p = await async_playwright().start()
        proxy_config = {"server": self.account["proxy"]} if self.account.get("proxy") else None
        self.browser = await p.chromium.launch(headless=self.config.get("headless", False))
        self.context = await self.browser.new_context(proxy=proxy_config)
        self.page = await self.context.new_page()
        self.log({"step": "browser_setup", "proxy": self.account.get("proxy", "none")})
    
    async def login(self):
        self.log({"step": "login_start"})
        await self.page.goto("https://www.allaccess.com.ar/login")
        await self.screenshot("login_page")
        
        await self.page.fill('input[type="email"]', self.account["email"])
        await self.page.fill('input[type="password"]', self.account["password"])
        
        recaptcha_frame = self.page.frame_locator('iframe[src*="recaptcha"]').first
        if await recaptcha_frame.locator('div').count() > 0:
            sitekey = await self.page.evaluate("""() => {
                const iframe = document.querySelector('iframe[src*="recaptcha"]');
                return iframe ? new URL(iframe.src).searchParams.get('k') : null;
            }""")
            if sitekey:
                self.log({"step": "captcha_solving", "sitekey": sitekey})
                token = await solve_recaptcha(self.page.url, sitekey, self.config.get("captcha_timeout", 120))
                await self.page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML="{token}";')
                self.log({"step": "captcha_solved"})
        
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")
        await self.screenshot("logged_in")
        self.log({"step": "login_complete"})
    
    async def handle_queue_if_present(self):
        if "queue-it.net" in self.page.url or await self.page.locator('iframe[src*="queue-it"]').count() > 0:
            self.log({"step": "queue_detected"})
            await handle_queue(self.page, self.config.get("queue_check_interval", 5), self.log)
            await self.screenshot("queue_passed")
            self.log({"step": "queue_passed"})
    
    async def select_tickets(self):
        self.log({"step": "ticket_selection_start"})
        
        ticket_type = self.config.get("ticket_type", "Campo General")
        ticket_count = self.config.get("ticket_count", 2)
        
        await self.page.click(f'text="{ticket_type}"')
        await asyncio.sleep(1)
        
        for _ in range(ticket_count):
            await self.page.click('button:has-text("+")')
            await asyncio.sleep(0.5)
        
        await self.screenshot("tickets_selected")
        await self.page.click('button:has-text("Continuar")')
        await self.page.wait_for_load_state("networkidle")
        self.log({"step": "ticket_selection_complete", "count": ticket_count})
    
    async def checkout(self):
        self.log({"step": "checkout_start"})
        await self.screenshot("checkout_page")
        
        await self.page.click('button:has-text("Finalizar")')
        await asyncio.sleep(2)
        
        if await self.page.locator('text="3D Secure"').count() > 0 or await self.page.locator('iframe[src*="3ds"]').count() > 0:
            self.log({"step": "checkout_blocked", "reason": "3DS_detected"})
            await self.screenshot("3ds_blocked")
            return False
        
        await self.screenshot("checkout_complete")
        self.log({"step": "checkout_complete"})
        return True
    
    async def run(self):
        await self.setup_browser()
        await self.login()
        await self.handle_queue_if_present()
        await self.select_tickets()
        success = await self.checkout()
        return success
    
    async def cleanup(self):
        if self.browser:
            await self.browser.close()
