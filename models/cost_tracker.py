import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class CostTracker:
    """Track API costs across providers"""
    
    # Approximate pricing (as of 2024, subject to change)
    PRICING = {
        'openai': {
            'gpt-4': {'input': 0.03, 'output': 0.06},  # per 1K tokens
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002}
        },
        'anthropic': {
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125}
        },
        'google': {
            'gemini-pro': {'input': 0.0005, 'output': 0.0015}
        }
    }
    
    def __init__(self, cost_file='cost_tracking.json'):
        self.cost_file = cost_file
        self.costs = self._load_costs()
    
    def _load_costs(self) -> Dict:
        """Load cost tracking data from file"""
        if os.path.exists(self.cost_file):
            try:
                with open(self.cost_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {'daily': {}, 'monthly': {}, 'total': 0.0}
    
    def _save_costs(self):
        """Save cost tracking data to file"""
        try:
            with open(self.cost_file, 'w') as f:
                json.dump(self.costs, f, indent=2)
        except IOError:
            pass
    
    def estimate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int = 100) -> float:
        """Estimate cost for a request"""
        if provider not in self.PRICING or model not in self.PRICING[provider]:
            return 0.01  # Default estimate
        
        pricing = self.PRICING[provider][model]
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        
        return round(input_cost + output_cost, 4)
    
    def estimate_message_tokens(self, message: str, context: List[str] = None) -> int:
        """Rough estimate of token count (4 chars ≈ 1 token)"""
        total_chars = len(message)
        if context:
            total_chars += sum(len(ctx) for ctx in context)
        return max(1, total_chars // 4)
    
    def record_cost(self, provider: str, model: str, actual_cost: float):
        """Record actual cost for a request"""
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')
        
        # Daily tracking
        if today not in self.costs['daily']:
            self.costs['daily'][today] = {}
        if provider not in self.costs['daily'][today]:
            self.costs['daily'][today][provider] = 0.0
        self.costs['daily'][today][provider] += actual_cost
        
        # Monthly tracking
        if month not in self.costs['monthly']:
            self.costs['monthly'][month] = {}
        if provider not in self.costs['monthly'][month]:
            self.costs['monthly'][month][provider] = 0.0
        self.costs['monthly'][month][provider] += actual_cost
        
        # Total tracking
        self.costs['total'] += actual_cost
        
        self._save_costs()
    
    def get_daily_spending(self, date: str = None) -> Dict[str, float]:
        """Get spending for a specific day"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        return self.costs['daily'].get(date, {})
    
    def get_monthly_spending(self, month: str = None) -> Dict[str, float]:
        """Get spending for a specific month"""
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        return self.costs['monthly'].get(month, {})
    
    def get_total_spending(self) -> float:
        """Get total spending across all providers"""
        return self.costs.get('total', 0.0)
    
    def is_over_budget(self, daily_budget: float, monthly_budget: float) -> Dict[str, bool]:
        """Check if over daily or monthly budget"""
        today_total = sum(self.get_daily_spending().values())
        month_total = sum(self.get_monthly_spending().values())
        
        return {
            'daily': today_total >= daily_budget,
            'monthly': month_total >= monthly_budget
        }
    
    def get_cost_summary(self) -> Dict:
        """Get comprehensive cost summary"""
        today_spending = self.get_daily_spending()
        month_spending = self.get_monthly_spending()
        
        return {
            'today': {
                'total': sum(today_spending.values()),
                'by_provider': today_spending
            },
            'this_month': {
                'total': sum(month_spending.values()),
                'by_provider': month_spending
            },
            'all_time': {
                'total': self.get_total_spending()
            }
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old daily cost data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Remove old daily data
        old_dates = [date for date in self.costs['daily'].keys() if date < cutoff_str]
        for date in old_dates:
            del self.costs['daily'][date]
        
        self._save_costs()

# Global cost tracker instance
cost_tracker = CostTracker()