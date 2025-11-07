"""
AllAccess.com.ar flow handler
Handles the complete ticket buying flow
"""
import time
from playwright.sync_api import Page
from logger import Logger

def navigate_to_event_page(page: Page, event_url: str, logger: Logger) -> bool:
    """Navigate to event page and wait for it to load."""
    logger.info({"step": "navigate_to_event", "url": event_url})
    try:
        page.goto(event_url, wait_until="networkidle", timeout=30000)
        logger.screenshot(page, "event_page")
        return True
    except Exception as e:
        logger.error({"step": "navigate_failed", "error": str(e)})
        return False

def click_ticket_card(page: Page, logger: Logger) -> bool:
    """Click on the event ticket card/image to proceed."""
    logger.info({"step": "click_ticket_card_start"})
    
    selectors = [
        'a[href*="/event/"][class*="card"]',
        'a[href*="/event/"] img',
        'div[class*="event-card"] a',
        'div[class*="card"] a[href*="/event/"]',
        'button:has-text("Comprar")',
        'button:has-text("Ver Entradas")',
        'a:has-text("Comprar Entradas")'
    ]
    
    for selector in selectors:
        try:
            if page.locator(selector).count() > 0:
                page.click(selector, timeout=5000)
                logger.info({"step": "ticket_card_clicked", "selector": selector})
                page.wait_for_load_state("networkidle", timeout=10000)
                logger.screenshot(page, "after_card_click")
                return True
        except:
            continue
    
    logger.info({"step": "ticket_card_not_needed", "info": "possibly already on ticket page"})
    return True

def select_event_date(page: Page, logger: Logger, preferred_date: str = None) -> bool:
    """Select event date if multiple dates available."""
    logger.info({"step": "select_date_start"})
    
    date_selectors = [
        'button[class*="date"]',
        'div[class*="date-selector"] button',
        '[data-date]',
        'button[class*="fecha"]',
        'div[class*="fechas"] button'
    ]
    
    for selector in date_selectors:
        try:
            if page.locator(selector).count() > 0:
                if preferred_date:
                    page.click(f'{selector}:has-text("{preferred_date}")', timeout=5000)
                else:
                    page.locator(selector).first.click(timeout=5000)
                
                logger.info({"step": "date_selected", "selector": selector})
                time.sleep(1)
                return True
        except:
            continue
    
    logger.info({"step": "date_selection_not_needed"})
    return True

def click_ver_entradas(page: Page, logger: Logger) -> bool:
    """Click 'Ver Entradas' or similar button to see tickets."""
    logger.info({"step": "click_ver_entradas_start"})
    
    selectors = [
        'button:has-text("Ver Entradas")',
        'button:has-text("Ver entradas")',
        'button:has-text("Comprar")',
        'button:has-text("Comprar Entradas")',
        'a:has-text("Ver Entradas")',
        'button[class*="buy"]',
        'button[class*="comprar"]'
    ]
    
    for selector in selectors:
        try:
            if page.locator(selector).count() > 0:
                page.click(selector, timeout=5000)
                logger.info({"step": "ver_entradas_clicked", "selector": selector})
                page.wait_for_load_state("networkidle", timeout=10000)
                logger.screenshot(page, "ticket_selection_page")
                return True
        except:
            continue
    
    logger.info({"step": "ver_entradas_not_needed"})
    return True

def select_campo_general(page: Page, logger: Logger, ticket_type: str, ticket_count: int) -> bool:
    """Select Campo General or specified ticket type and quantity."""
    logger.info({"step": "select_ticket_type_start", "type": ticket_type, "count": ticket_count})
    
    type_selectors = [
        f'button:has-text("{ticket_type}")',
        f'div:has-text("{ticket_type}") button',
        f'[data-sector="{ticket_type}"]',
        f'div[class*="ticket"]:has-text("{ticket_type}")',
        f'div[class*="sector"]:has-text("{ticket_type}")'
    ]
    
    type_clicked = False
    for selector in type_selectors:
        try:
            if page.locator(selector).count() > 0:
                page.click(selector, timeout=5000)
                logger.info({"step": "ticket_type_selected", "selector": selector})
                time.sleep(1)
                type_clicked = True
                break
        except:
            continue
    
    if not type_clicked:
        logger.error({"step": "ticket_type_not_found", "type": ticket_type})
        return False
    
    quantity_selectors = [
        'button[aria-label*="Agregar"]',
        'button:has-text("+")',
        'button[class*="increment"]',
        'button[class*="add"]',
        'input[type="number"]'
    ]
    
    for i in range(ticket_count):
        added = False
        for selector in quantity_selectors:
            try:
                if page.locator(selector).count() > 0:
                    elem = page.locator(selector).first
                    tag = elem.evaluate('el => el.tagName')
                    
                    if tag == 'INPUT':
                        elem.fill(str(ticket_count))
                        added = True
                        break
                    else:
                        elem.click(timeout=3000)
                        time.sleep(0.5)
                        added = True
                        break
            except:
                continue
        
        if not added and i == 0:
            logger.error({"step": "quantity_selector_not_found"})
            return False
    
    logger.info({"step": "ticket_quantity_set", "count": ticket_count})
    logger.screenshot(page, "tickets_selected")
    
    continue_selectors = [
        'button:has-text("Continuar")',
        'button:has-text("Continue")',
        'button:has-text("Siguiente")',
        'button[type="submit"]',
        'button[class*="continue"]',
        'button[class*="next"]'
    ]
    
    for selector in continue_selectors:
        try:
            if page.locator(selector).count() > 0:
                page.click(selector, timeout=5000)
                logger.info({"step": "continue_clicked", "selector": selector})
                page.wait_for_load_state("networkidle", timeout=10000)
                return True
        except:
            continue
    
    logger.error({"step": "continue_button_not_found"})
    return False

def handle_allaccess_flow(page: Page, logger: Logger, event_url: str, ticket_type: str, ticket_count: int) -> bool:
    """Complete AllAccess ticket selection flow."""
    
    if not navigate_to_event_page(page, event_url, logger):
        return False
    
    time.sleep(2)
    
    if not click_ticket_card(page, logger):
        return False
    
    time.sleep(1)
    
    if not select_event_date(page, logger):
        return False
    
    time.sleep(1)
    
    if not click_ver_entradas(page, logger):
        return False
    
    time.sleep(2)
    
    if not select_campo_general(page, logger, ticket_type, ticket_count):
        return False
    
    logger.info({"step": "allaccess_flow_complete"})
    return True
