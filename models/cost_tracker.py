import sqlite3
from datetime import datetime
from typing import Dict
from .debug_logger import debug_log, debug_error

class SimpleCostTracker:
    """Simplified cost tracker using SQLite"""
    
    # Rough pricing estimates (may be outdated - for reference only)
    ROUGH_ESTIMATES = {
        'openai': {
            'gpt-4': 0.03,           # per 1K tokens (average of input/output)
            'gpt-3.5-turbo': 0.002   # per 1K tokens (average of input/output)
        },
        'anthropic': {
            'claude-3-sonnet-20240229': 0.01,    # per 1K tokens (average)
            'claude-3-haiku-20240307': 0.001     # per 1K tokens (average)
        },
        'google': {
            'gemini-pro': 0.001,         # per 1K tokens (average)
            'gemini-1.5-flash': 0.0005   # per 1K tokens (average)
        }
    }
    
    def __init__(self):
        self.daily_total = self._load_daily_total()
    
    def _load_daily_total(self) -> float:
        """Load today's spending total from SQLite"""
        try:
            conn = sqlite3.connect('memory.db')
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT total_cost FROM cost_tracking WHERE date = ?", (today,))
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else 0.0
        except sqlite3.Error:
            return 0.0
    
    def estimate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate cost for API call - WARNING: These are rough estimates and may be outdated"""
        provider_rates = self.ROUGH_ESTIMATES.get(provider, {})
        rate = provider_rates.get(model, 0.001)  # Default fallback rate
        
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000.0) * rate
    
    def estimate_message_tokens(self, message: str) -> int:
        """Rough token estimation - approximately 1 token per 4 characters"""
        return max(1, len(message) // 4)
    
    def record_cost(self, provider: str, model: str, cost: float):
        """Record actual cost spending in SQLite"""
        debug_log("cost_record", {
            "provider": provider,
            "model": model,
            "cost": cost
        })
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect('memory.db')
            cursor = conn.cursor()
            
            # Get current total for today
            cursor.execute("SELECT total_cost FROM cost_tracking WHERE date = ?", (today,))
            row = cursor.fetchone()
            current_total = row[0] if row else 0.0
            
            # Update or insert new total
            new_total = current_total + cost
            cursor.execute('''
                INSERT OR REPLACE INTO cost_tracking (date, total_cost) 
                VALUES (?, ?)
            ''', (today, new_total))
            
            conn.commit()
            conn.close()
            
            self.daily_total = new_total
            debug_log("cost_record_success", {"new_total": new_total})
        except sqlite3.Error as e:
            debug_error("cost_record_error", str(e))
            pass  # Fail silently if cost tracking fails
    
    def get_cost_summary(self) -> Dict:
        """Get simple cost summary"""
        return {
            'today': {'total': self.daily_total},
            'warning': 'Cost estimates are approximate and may be outdated'
        }

# Global cost tracker instance
cost_tracker = SimpleCostTracker()