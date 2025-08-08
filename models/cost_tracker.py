import json
import os
from datetime import datetime
from typing import Dict, Optional

class SimpleCostTracker:
    """Simplified cost tracker with basic estimates"""
    
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
    
    def __init__(self, cost_file='cost_tracking.json'):
        self.cost_file = cost_file
        self.daily_total = self._load_daily_total()
    
    def _load_daily_total(self) -> float:
        """Load today's spending total"""
        if os.path.exists(self.cost_file):
            try:
                with open(self.cost_file, 'r') as f:
                    data = json.load(f)
                    today = datetime.now().strftime('%Y-%m-%d')
                    return data.get(today, 0.0)
            except:
                return 0.0
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
        """Record actual cost spending"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            data = {}
            if os.path.exists(self.cost_file):
                with open(self.cost_file, 'r') as f:
                    data = json.load(f)
            
            data[today] = data.get(today, 0.0) + cost
            self.daily_total = data[today]
            
            with open(self.cost_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass  # Fail silently if cost tracking fails
    
    def get_cost_summary(self) -> Dict:
        """Get simple cost summary"""
        return {
            'today': {'total': self.daily_total},
            'warning': 'Cost estimates are approximate and may be outdated'
        }

# Global cost tracker instance
cost_tracker = SimpleCostTracker()