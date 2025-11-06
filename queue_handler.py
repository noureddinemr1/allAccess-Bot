import asyncio

async def handle_queue(page, check_interval, log_func):
    log_func({"step": "queue_wait_start"})
    
    while True:
        current_url = page.url
        
        if "queue-it.net" not in current_url:
            iframe = page.frame_locator('iframe[src*="queue-it"]').first
            if await iframe.locator('body').count() == 0:
                break
        
        queue_position = await page.locator('text=/position|queue/i').first.text_content() if await page.locator('text=/position|queue/i').count() > 0 else "unknown"
        log_func({"step": "queue_waiting", "position": queue_position})
        
        await asyncio.sleep(check_interval)
        
        try:
            await page.wait_for_url(lambda url: "queue-it.net" not in url, timeout=check_interval * 1000)
            break
        except:
            continue
    
    log_func({"step": "queue_wait_complete"})
