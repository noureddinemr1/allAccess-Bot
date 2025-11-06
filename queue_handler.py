import time
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

def is_queue_active(page: Page) -> bool:
    """Check if Queue-it is active on page."""
    url = page.url
    if "queue-it.net" in url:
        return True
    
    try:
        queue_iframe = page.frame_locator('iframe[src*="queue-it"]').first
        return queue_iframe.locator('body').count() > 0
    except:
        return False

def wait_for_queue_release(page: Page, timeout: int = 1800, check_interval: int = 5) -> bool:
    """Wait for Queue-it to release, keeping session alive."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if not is_queue_active(page):
            return True
        
        try:
            position_text = page.locator('text=/position|queue|waiting/i').first.text_content(timeout=2000)
        except:
            position_text = "unknown"
        
        try:
            page.mouse.move(100, 100)
            page.evaluate("() => { document.title = document.title; }")
        except:
            pass
        
        original_url = page.url
        time.sleep(check_interval)
        
        try:
            if page.url != original_url and "queue-it.net" not in page.url:
                return True
        except:
            pass
    
    return False

def handle_queue(page: Page, logger, check_interval: int = 5) -> bool:
    """Main queue handler with logging."""
    if not is_queue_active(page):
        logger.info({"step": "queue_not_detected"})
        return True
    
    logger.info({"step": "queue_detected", "url": page.url})
    logger.screenshot(page, "queue_start")
    
    success = wait_for_queue_release(page, check_interval=check_interval)
    
    if success:
        logger.info({"step": "queue_passed", "url": page.url})
        logger.screenshot(page, "queue_passed")
        page.wait_for_load_state("networkidle", timeout=30000)
        return True
    else:
        logger.error({"step": "queue_timeout"})
        return False
