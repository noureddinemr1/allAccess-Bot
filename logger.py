import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

class Logger:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.log_file = Path("logs") / f"account_{account_id}.jsonl"
        
    def _write(self, level: str, data: Dict[str, Any]):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": self.account_id,
            "level": level,
            **data
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        
        step = data.get("step", data.get("message", ""))
        print(f"[{self.account_id}] {level.upper()}: {step}")
    
    def info(self, data: Dict[str, Any]):
        self._write("info", data)
    
    def error(self, data: Dict[str, Any]):
        self._write("error", data)
    
    def screenshot(self, page, step: str) -> str:
        from config import DEBUG_SCREENSHOTS
        if not DEBUG_SCREENSHOTS:
            return None
            
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"screenshots/account_{self.account_id}_{step}_{timestamp}.png"
        try:
            page.screenshot(path=filename, full_page=True)
            self.info({"step": f"screenshot_{step}", "file": filename})
            return filename
        except Exception as e:
            return None
