import time
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from logger import Logger
from captcha import solve_recaptcha_v2, inject_token, extract_sitekey
from queue_handler import handle_queue
from checkout import select_tickets, prepare_checkout, finalize_purchase
from config import EVENT_URL, HEADLESS, DEBUG_SCREENSHOTS

def create_browser_context(playwright, account_id: str, proxy: Optional[str], headless: bool) -> tuple[Browser, BrowserContext]:
    """Create isolated browser context with proxy."""
    user_data_dir = Path("profiles") / f"account_{account_id}"
    user_data_dir.mkdir(exist_ok=True)
    
    launch_options = {
        "headless": headless,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage"
        ]
    }
    
    browser = playwright.chromium.launch(**launch_options)
    
    context_options = {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    if proxy:
        context_options["proxy"] = {"server": proxy}
    
    context = browser.new_context(**context_options)
    return browser, context

def perform_login(page: Page, account: Dict[str, Any], logger: Logger) -> bool:
    """Handle login with captcha if needed."""
    logger.info({"step": "login_start", "email": account.get("email")})
    
    try:
        page.goto("https://www.allaccess.com.ar/login", wait_until="networkidle", timeout=30000)
        logger.screenshot(page, "login_page")
        
        page.fill('input[type="email"], input[name*="email"], input[name*="usuario"]', account.get("email"))
        page.fill('input[type="password"], input[name*="password"], input[name*="contraseña"]', account.get("password"))
        
        time.sleep(1)
        
        sitekey = extract_sitekey(page)
        if sitekey:
            logger.info({"step": "captcha_detected", "sitekey": sitekey})
            token = solve_recaptcha_v2(sitekey, page.url)
            inject_token(page, token)
            logger.info({"step": "captcha_solved"})
            time.sleep(1)
        
        page.click('button[type="submit"], button:has-text("Ingresar"), button:has-text("Login")')
        page.wait_for_load_state("networkidle", timeout=30000)
        
        if page.url.find("login") == -1 or page.locator('text=/mi cuenta|account|perfil/i').count() > 0:
            logger.screenshot(page, "login_success")
            logger.info({"step": "login_complete"})
            return True
        else:
            logger.error({"step": "login_failed", "url": page.url})
            logger.screenshot(page, "login_failed")
            return False
            
    except Exception as e:
        logger.error({"step": "login_exception", "error": str(e)})
        logger.screenshot(page, "login_error")
        return False

def run_worker(account: Dict[str, Any], account_id: str, proxy: Optional[str], headless: bool = None) -> Dict[str, Any]:
    """Main worker function to process one account."""
    logger = Logger(account_id)
    logger.info({"step": "worker_start", "email": account.get("email"), "proxy": proxy or "none"})
    
    if headless is None:
        headless = HEADLESS
    
    result = {
        "account_id": account_id,
        "email": account.get("email"),
        "success": False,
        "error": None,
        "order_number": None
    }
    
    browser = None
    context = None
    
    try:
        with sync_playwright() as playwright:
            browser, context = create_browser_context(playwright, account_id, proxy, headless)
            page = context.new_page()
            
            logger.info({"step": "navigate_to_event", "url": EVENT_URL})
            page.goto(EVENT_URL, wait_until="networkidle", timeout=30000)
            logger.screenshot(page, "event_page")
            
            queue_handled = handle_queue(page, logger)
            if not queue_handled:
                result["error"] = "queue_timeout"
                return result
            
            if page.url.find("login") != -1 or page.locator('text=/iniciar sesión|login|ingresar/i').count() > 0:
                login_success = perform_login(page, account, logger)
                if not login_success:
                    result["error"] = "login_failed"
                    return result
                
                page.goto(EVENT_URL, wait_until="networkidle", timeout=30000)
                queue_handled = handle_queue(page, logger)
                if not queue_handled:
                    result["error"] = "queue_timeout_after_login"
                    return result
            
            ticket_result = select_tickets(page, logger)
            if not ticket_result.get("success"):
                result["error"] = f"ticket_selection_failed: {ticket_result.get('error')}"
                return result
            
            checkout_result = prepare_checkout(page, account, logger)
            if not checkout_result.get("success"):
                result["error"] = f"checkout_preparation_failed: {checkout_result.get('error')}"
                return result
            
            purchase_result = finalize_purchase(page, logger)
            if purchase_result.get("success"):
                result["success"] = True
                result["order_number"] = purchase_result.get("order_number")
                logger.info({"step": "worker_complete", "success": True, "order": result["order_number"]})
            elif purchase_result.get("requires_manual"):
                result["error"] = f"manual_intervention_required: {purchase_result.get('reason')}"
                logger.error({"step": "worker_manual_required", "reason": purchase_result.get("reason")})
            else:
                result["error"] = f"purchase_failed: {purchase_result.get('error')}"
                logger.error({"step": "worker_purchase_failed", "error": purchase_result.get("error")})
            
            time.sleep(2)
            
    except Exception as e:
        logger.error({"step": "worker_exception", "error": str(e)})
        result["error"] = f"exception: {str(e)}"
        
    finally:
        try:
            if context:
                context.close()
            if browser:
                browser.close()
        except:
            pass
        
        logger.info({"step": "worker_cleanup_complete"})
    
    return result
