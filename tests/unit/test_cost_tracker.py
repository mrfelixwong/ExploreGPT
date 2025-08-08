import unittest
import tempfile
import os
import json
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the models directory to Python path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.cost_tracker import CostTracker


class TestCostTracker(unittest.TestCase):
    """
    Test scenarios for Cost Tracking:
    1. Cost estimation for different providers and models
    2. Token estimation accuracy and edge cases
    3. Cost recording and aggregation (daily/monthly/total)
    4. Budget validation and threshold checking
    5. File persistence and error handling
    6. Data cleanup and retention
    7. Cost summary generation
    8. Edge cases with malformed data
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_cost_file = os.path.join(self.test_dir, 'test_costs.json')
        self.cost_tracker = CostTracker(self.test_cost_file)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def test_estimate_cost_openai_gpt4(self):
        """Test 1a: Cost estimation for OpenAI GPT-4"""
        input_tokens = 1000
        output_tokens = 500
        
        estimated_cost = self.cost_tracker.estimate_cost('openai', 'gpt-4', input_tokens, output_tokens)
        
        # GPT-4: $0.03 input, $0.06 output per 1K tokens
        expected_cost = (1000/1000 * 0.03) + (500/1000 * 0.06)
        expected_cost = round(expected_cost, 4)
        
        self.assertEqual(estimated_cost, expected_cost)
        self.assertEqual(estimated_cost, 0.06)  # 0.03 + 0.03
    
    def test_estimate_cost_anthropic_claude(self):
        """Test 1b: Cost estimation for Anthropic Claude"""
        input_tokens = 2000
        output_tokens = 1000
        
        estimated_cost = self.cost_tracker.estimate_cost('anthropic', 'claude-3-sonnet-20240229', input_tokens, output_tokens)
        
        # Claude Sonnet: $0.003 input, $0.015 output per 1K tokens
        expected_cost = (2000/1000 * 0.003) + (1000/1000 * 0.015)
        expected_cost = round(expected_cost, 4)
        
        self.assertEqual(estimated_cost, expected_cost)
        self.assertEqual(estimated_cost, 0.021)  # 0.006 + 0.015
    
    def test_estimate_cost_google_gemini(self):
        """Test 1c: Cost estimation for Google Gemini"""
        input_tokens = 1500
        output_tokens = 300
        
        estimated_cost = self.cost_tracker.estimate_cost('google', 'gemini-pro', input_tokens, output_tokens)
        
        # Gemini Pro: $0.0005 input, $0.0015 output per 1K tokens
        expected_cost = (1500/1000 * 0.0005) + (300/1000 * 0.0015)
        expected_cost = round(expected_cost, 4)
        
        self.assertEqual(estimated_cost, expected_cost)
        self.assertEqual(estimated_cost, 0.0012)  # 0.00075 + 0.00045
    
    def test_estimate_cost_unknown_provider(self):
        """Test 1d: Cost estimation for unknown provider/model"""
        estimated_cost = self.cost_tracker.estimate_cost('unknown_provider', 'unknown_model', 1000, 500)
        
        # Should return default estimate
        self.assertEqual(estimated_cost, 0.01)
    
    def test_estimate_message_tokens_simple_message(self):
        """Test 2a: Token estimation for simple message"""
        message = "Hello world, this is a test message"
        
        estimated_tokens = self.cost_tracker.estimate_message_tokens(message)
        
        # 4 chars ≈ 1 token, message is 34 chars
        expected_tokens = max(1, len(message) // 4)
        self.assertEqual(estimated_tokens, expected_tokens)
        self.assertEqual(estimated_tokens, 8)
    
    def test_estimate_message_tokens_with_context(self):
        """Test 2b: Token estimation with context"""
        message = "Hello world"
        context = ["Previous message 1", "Previous message 2"]
        
        estimated_tokens = self.cost_tracker.estimate_message_tokens(message, context)
        
        total_chars = len(message) + len("Previous message 1") + len("Previous message 2")
        expected_tokens = max(1, total_chars // 4)
        self.assertEqual(estimated_tokens, expected_tokens)
    
    def test_estimate_message_tokens_empty_message(self):
        """Test 2c: Token estimation for empty message"""
        estimated_tokens = self.cost_tracker.estimate_message_tokens("")
        
        # Should return at least 1 token
        self.assertEqual(estimated_tokens, 1)
    
    def test_record_cost_daily_aggregation(self):
        """Test 3a: Record costs and verify daily aggregation"""
        # Record costs for today
        today = datetime.now().strftime('%Y-%m-%d')
        
        self.cost_tracker.record_cost('openai', 'gpt-4', 0.05)
        self.cost_tracker.record_cost('openai', 'gpt-4', 0.03)
        self.cost_tracker.record_cost('anthropic', 'claude-3-sonnet', 0.02)
        
        daily_spending = self.cost_tracker.get_daily_spending(today)
        
        # Should aggregate by provider
        self.assertEqual(daily_spending['openai'], 0.08)  # 0.05 + 0.03
        self.assertEqual(daily_spending['anthropic'], 0.02)
    
    def test_record_cost_monthly_aggregation(self):
        """Test 3b: Record costs and verify monthly aggregation"""
        month = datetime.now().strftime('%Y-%m')
        
        self.cost_tracker.record_cost('google', 'gemini-pro', 0.001)
        self.cost_tracker.record_cost('google', 'gemini-pro', 0.002)
        
        monthly_spending = self.cost_tracker.get_monthly_spending(month)
        
        self.assertEqual(monthly_spending['google'], 0.003)  # 0.001 + 0.002
    
    def test_record_cost_total_aggregation(self):
        """Test 3c: Record costs and verify total aggregation"""
        initial_total = self.cost_tracker.get_total_spending()
        
        self.cost_tracker.record_cost('openai', 'gpt-4', 0.10)
        self.cost_tracker.record_cost('anthropic', 'claude-3-sonnet', 0.05)
        
        final_total = self.cost_tracker.get_total_spending()
        
        # Use round to handle floating point precision issues
        self.assertEqual(round(final_total - initial_total, 2), 0.15)
    
    def test_is_over_budget_within_limits(self):
        """Test 4a: Budget validation within limits"""
        # Record some costs
        self.cost_tracker.record_cost('openai', 'gpt-4', 2.00)  # Daily
        
        budget_status = self.cost_tracker.is_over_budget(daily_budget=5.0, monthly_budget=20.0)
        
        self.assertFalse(budget_status['daily'])
        self.assertFalse(budget_status['monthly'])
    
    def test_is_over_budget_exceeds_daily(self):
        """Test 4b: Budget validation exceeding daily limit"""
        # Record costs exceeding daily budget
        self.cost_tracker.record_cost('openai', 'gpt-4', 6.00)
        
        budget_status = self.cost_tracker.is_over_budget(daily_budget=5.0, monthly_budget=20.0)
        
        self.assertTrue(budget_status['daily'])
        self.assertFalse(budget_status['monthly'])  # Still within monthly
    
    def test_is_over_budget_exceeds_monthly(self):
        """Test 4c: Budget validation exceeding monthly limit"""
        # Record costs exceeding monthly budget
        self.cost_tracker.record_cost('anthropic', 'claude-3-sonnet', 25.00)
        
        budget_status = self.cost_tracker.is_over_budget(daily_budget=30.0, monthly_budget=20.0)
        
        self.assertFalse(budget_status['daily'])  # Within daily
        self.assertTrue(budget_status['monthly'])
    
    def test_load_costs_missing_file(self):
        """Test 5a: Load costs when file doesn't exist"""
        # Ensure file doesn't exist
        if os.path.exists(self.test_cost_file):
            os.remove(self.test_cost_file)
        
        tracker = CostTracker(self.test_cost_file)
        
        # Should initialize with empty structure
        self.assertEqual(tracker.costs['total'], 0.0)
        self.assertEqual(tracker.costs['daily'], {})
        self.assertEqual(tracker.costs['monthly'], {})
    
    def test_load_costs_corrupted_file(self):
        """Test 5b: Load costs with corrupted JSON file"""
        # Create corrupted file
        with open(self.test_cost_file, 'w') as f:
            f.write('{"corrupted": json data')
        
        tracker = CostTracker(self.test_cost_file)
        
        # Should fallback to default structure
        self.assertEqual(tracker.costs['total'], 0.0)
        self.assertEqual(tracker.costs['daily'], {})
        self.assertEqual(tracker.costs['monthly'], {})
    
    def test_save_costs_persistence(self):
        """Test 5c: Verify costs are persisted to file"""
        self.cost_tracker.record_cost('openai', 'gpt-4', 0.10)
        
        # Create new tracker instance to test persistence
        new_tracker = CostTracker(self.test_cost_file)
        
        self.assertEqual(new_tracker.get_total_spending(), 0.10)
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_costs_io_error(self, mock_open):
        """Test 5d: Handle IO errors during save"""
        # Should not raise exception, should handle gracefully
        try:
            self.cost_tracker.record_cost('openai', 'gpt-4', 0.10)
        except IOError:
            self.fail("record_cost should handle IO errors gracefully")
    
    def test_cleanup_old_data(self):
        """Test 6a: Clean up old daily cost data"""
        # Add old data (100 days ago)
        old_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        recent_date = datetime.now().strftime('%Y-%m-%d')
        
        # Manually add data to test cleanup
        self.cost_tracker.costs['daily'][old_date] = {'openai': 1.0}
        self.cost_tracker.costs['daily'][recent_date] = {'anthropic': 2.0}
        self.cost_tracker._save_costs()
        
        # Clean up data older than 90 days
        self.cost_tracker.cleanup_old_data(days_to_keep=90)
        
        # Old data should be removed, recent data should remain
        self.assertNotIn(old_date, self.cost_tracker.costs['daily'])
        self.assertIn(recent_date, self.cost_tracker.costs['daily'])
    
    def test_cleanup_old_data_edge_case(self):
        """Test 6b: Clean up with boundary date (exactly 90 days)"""
        boundary_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        self.cost_tracker.costs['daily'][boundary_date] = {'google': 0.5}
        self.cost_tracker._save_costs()
        
        self.cost_tracker.cleanup_old_data(days_to_keep=90)
        
        # Boundary date should be kept (>= cutoff)
        self.assertIn(boundary_date, self.cost_tracker.costs['daily'])
    
    def test_get_cost_summary_comprehensive(self):
        """Test 7a: Generate comprehensive cost summary"""
        # Add various costs
        self.cost_tracker.record_cost('openai', 'gpt-4', 1.50)
        self.cost_tracker.record_cost('anthropic', 'claude-3-sonnet', 0.75)
        self.cost_tracker.record_cost('google', 'gemini-pro', 0.25)
        
        summary = self.cost_tracker.get_cost_summary()
        
        # Check structure
        self.assertIn('today', summary)
        self.assertIn('this_month', summary)
        self.assertIn('all_time', summary)
        
        # Check today's totals
        self.assertEqual(summary['today']['total'], 2.50)
        self.assertIn('openai', summary['today']['by_provider'])
        self.assertIn('anthropic', summary['today']['by_provider'])
        self.assertIn('google', summary['today']['by_provider'])
        
        # Check all-time total
        self.assertEqual(summary['all_time']['total'], 2.50)
    
    def test_get_cost_summary_empty_data(self):
        """Test 7b: Generate cost summary with no data"""
        summary = self.cost_tracker.get_cost_summary()
        
        self.assertEqual(summary['today']['total'], 0)
        self.assertEqual(summary['this_month']['total'], 0)
        self.assertEqual(summary['all_time']['total'], 0.0)
        self.assertEqual(summary['today']['by_provider'], {})
    
    def test_get_daily_spending_specific_date(self):
        """Test 8a: Get spending for specific date"""
        target_date = '2024-01-15'
        
        # Manually add data for specific date
        self.cost_tracker.costs['daily'][target_date] = {
            'openai': 1.0,
            'anthropic': 0.5
        }
        
        spending = self.cost_tracker.get_daily_spending(target_date)
        
        self.assertEqual(spending['openai'], 1.0)
        self.assertEqual(spending['anthropic'], 0.5)
    
    def test_get_daily_spending_no_data(self):
        """Test 8b: Get spending for date with no data"""
        spending = self.cost_tracker.get_daily_spending('2020-01-01')
        
        self.assertEqual(spending, {})
    
    def test_get_monthly_spending_specific_month(self):
        """Test 8c: Get spending for specific month"""
        target_month = '2024-01'
        
        # Manually add data for specific month
        self.cost_tracker.costs['monthly'][target_month] = {
            'google': 2.0,
            'openai': 3.0
        }
        
        spending = self.cost_tracker.get_monthly_spending(target_month)
        
        self.assertEqual(spending['google'], 2.0)
        self.assertEqual(spending['openai'], 3.0)
    
    def test_multiple_providers_cost_isolation(self):
        """Test 9: Verify costs are properly isolated by provider"""
        # Record costs for different providers
        self.cost_tracker.record_cost('openai', 'gpt-4', 1.00)
        self.cost_tracker.record_cost('openai', 'gpt-3.5-turbo', 0.50)
        self.cost_tracker.record_cost('anthropic', 'claude-3-sonnet', 2.00)
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_spending = self.cost_tracker.get_daily_spending(today)
        
        # OpenAI should aggregate both models
        self.assertEqual(daily_spending['openai'], 1.50)
        # Anthropic should be separate
        self.assertEqual(daily_spending['anthropic'], 2.00)
        # Total should be correct
        total_today = sum(daily_spending.values())
        self.assertEqual(total_today, 3.50)


if __name__ == '__main__':
    unittest.main()