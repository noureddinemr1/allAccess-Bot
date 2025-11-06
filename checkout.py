import time
from typing import Dict, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from config import TICKET_TYPE, TICKET_COUNT

def select_tickets(page: Page, logger, ticket_type: str = None, ticket_count: int = None) -> Dict[str, Any]:
    """Select ticket type and quantity."""
    ticket_type = ticket_type or TICKET_TYPE
    ticket_count = ticket_count or TICKET_COUNT
    
    logger.info({"step": "ticket_selection_start", "type": ticket_type, "count": ticket_count})
    
    try:
        page.wait_for_selector(f'text="{ticket_type}"', timeout=10000)
        page.click(f'text="{ticket_type}"')
        time.sleep(1)
        
        for i in range(ticket_count):
            try:
                page.click('button:has-text("+")', timeout=5000)
                time.sleep(0.5)
            except:
                page.click('button[aria-label*="increase"], button[aria-label*="increment"]', timeout=5000)
                time.sleep(0.5)
        
        logger.screenshot(page, "tickets_selected")
        
        page.click('button:has-text("Continuar"), button:has-text("Continue"), button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=30000)
        
        logger.info({"step": "ticket_selection_complete"})
        return {"success": True}
        
    except Exception as e:
        logger.error({"step": "ticket_selection_failed", "error": str(e)})
        logger.screenshot(page, "ticket_selection_error")
        return {"success": False, "error": str(e)}

def fill_billing_info(page: Page, account: Dict[str, Any], logger) -> Dict[str, Any]:
    """Fill billing information form."""
    logger.info({"step": "billing_fill_start"})
    billing = account.get("billing", {})
    
    try:
        selectors_map = {
            "first_name": ['input[name*="first"], input[name*="nombre"]', billing.get("first_name")],
            "last_name": ['input[name*="last"], input[name*="apellido"]', billing.get("last_name")],
            "document_number": ['input[name*="document"], input[name*="dni"]', billing.get("document_number")],
            "phone": ['input[name*="phone"], input[name*="telefono"]', billing.get("phone")],
            "email": ['input[type="email"]', account.get("email")],
            "address": ['input[name*="address"], input[name*="direccion"]', billing.get("address")],
            "city": ['input[name*="city"], input[name*="ciudad"]', billing.get("city")],
            "postal_code": ['input[name*="postal"], input[name*="codigo"]', billing.get("postal_code")],
        }
        
        for field, (selector, value) in selectors_map.items():
            if value:
                try:
                    page.fill(selector, str(value), timeout=5000)
                except:
                    pass
        
        logger.screenshot(page, "billing_filled")
        logger.info({"step": "billing_fill_complete"})
        return {"success": True}
        
    except Exception as e:
        logger.error({"step": "billing_fill_failed", "error": str(e)})
        return {"success": False, "error": str(e)}

def fill_payment_info(page: Page, account: Dict[str, Any], logger) -> Dict[str, Any]:
    """Fill payment card information."""
    logger.info({"step": "payment_fill_start"})
    card = account.get("card", {})
    
    try:
        card_selectors = {
            "number": ['input[name*="card"][name*="number"], input[placeholder*="card number"]', card.get("number")],
            "holder": ['input[name*="holder"], input[name*="name"]', card.get("holder")],
            "expiry_month": ['input[name*="month"], select[name*="month"]', card.get("expiry_month")],
            "expiry_year": ['input[name*="year"], select[name*="year"]', card.get("expiry_year")],
            "cvv": ['input[name*="cvv"], input[name*="security"]', card.get("cvv")],
        }
        
        for field, (selector, value) in card_selectors.items():
            if value:
                try:
                    element = page.locator(selector).first
                    if element.count() > 0:
                        tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                        if tag_name == "select":
                            element.select_option(str(value))
                        else:
                            element.fill(str(value))
                except:
                    pass
        
        logger.screenshot(page, "payment_filled")
        logger.info({"step": "payment_fill_complete"})
        return {"success": True}
        
    except Exception as e:
        logger.error({"step": "payment_fill_failed", "error": str(e)})
        return {"success": False, "error": str(e)}

def finalize_purchase(page: Page, logger) -> Dict[str, Any]:
    """Attempt to finalize purchase, detect 3DS or success."""
    logger.info({"step": "purchase_finalize_start"})
    
    try:
        logger.screenshot(page, "before_submit")
        
        page.click('button:has-text("Finalizar"), button:has-text("Pagar"), button:has-text("Confirmar")', timeout=10000)
        time.sleep(3)
        
        if page.locator('text=/3d secure|3ds|verificación/i').count() > 0 or page.locator('iframe[src*="3ds"]').count() > 0:
            logger.error({"step": "purchase_blocked_3ds"})
            logger.screenshot(page, "3ds_detected")
            return {"success": False, "requires_manual": True, "reason": "3DS_authentication_required"}
        
        if page.locator('text=/error|invalid|declined/i').count() > 0:
            error_text = page.locator('text=/error|invalid|declined/i').first.text_content()
            logger.error({"step": "purchase_error", "error": error_text})
            logger.screenshot(page, "payment_error")
            return {"success": False, "error": error_text}
        
        time.sleep(2)
        
        if page.locator('text=/confirmación|confirmation|éxito|success|orden|order/i').count() > 0:
            logger.screenshot(page, "purchase_success")
            
            order_number = None
            try:
                order_number = page.locator('text=/orden|order|#/i').first.text_content()
            except:
                pass
            
            logger.info({"step": "purchase_complete", "order": order_number})
            return {"success": True, "order_number": order_number}
        
        logger.screenshot(page, "purchase_unknown_state")
        return {"success": False, "requires_manual": True, "reason": "unknown_state"}
        
    except Exception as e:
        logger.error({"step": "purchase_finalize_failed", "error": str(e)})
        logger.screenshot(page, "purchase_error")
        return {"success": False, "error": str(e)}

def prepare_checkout(page: Page, account: Dict[str, Any], logger) -> Dict[str, Any]:
    """Complete checkout flow: billing + payment info."""
    billing_result = fill_billing_info(page, account, logger)
    if not billing_result.get("success"):
        return billing_result
    
    payment_result = fill_payment_info(page, account, logger)
    if not payment_result.get("success"):
        return payment_result
    
    return {"success": True}
