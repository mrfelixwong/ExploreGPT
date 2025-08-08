import unittest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, Future
import time

# Add the models directory to Python path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.llm_clients import LLMOrchestrator


class TestLLMOrchestrator(unittest.TestCase):
    """
    Test scenarios for LLM Orchestration:
    1. Orchestrator initialization and client setup
    2. Settings integration and updates
    3. Provider enabling/disabling and priority handling
    4. Parallel vs sequential execution modes
    5. Individual provider API call mocking and responses
    6. Error handling for each provider
    7. Budget checking and cost integration
    8. Context preparation and limiting
    9. Timeout and response handling
    10. Provider fallback mechanisms
    """
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock settings for testing
        self.test_settings = {
            'models': {
                'openai': 'gpt-4',
                'anthropic': 'claude-3-sonnet-20240229',
                'google': 'gemini-pro'
            },
            'provider_settings': {
                'openai': {'enabled': True, 'priority': 1, 'fallback': True},
                'anthropic': {'enabled': True, 'priority': 2, 'fallback': True},
                'google': {'enabled': True, 'priority': 3, 'fallback': True}
            },
            'response_settings': {
                'max_tokens': 1000,
                'timeout': 30,
                'temperature': 0.7,
                'parallel_requests': True,
                'show_metadata': True
            },
            'memory_settings': {
                'context_count': 5,
                'auto_learning': True
            },
            'cost_management': {
                'track_costs': False,
                'daily_budget': 5.0,
                'smart_routing': False
            }
        }
        
        # Mock the API clients to avoid actual API calls
        self.mock_env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_openai_key',
            'ANTHROPIC_API_KEY': 'test_anthropic_key',
            'GOOGLE_API_KEY': 'test_google_key'
        })
        self.mock_env_patcher.start()
        
        # Create orchestrator with mocked clients
        with patch('models.llm_clients.openai.OpenAI') as mock_openai, \
             patch('models.llm_clients.anthropic.Anthropic') as mock_anthropic, \
             patch('models.llm_clients.genai') as mock_genai:
            
            # Set up mock returns
            mock_genai.GenerativeModel.return_value = Mock()
            mock_genai.configure = Mock()
            
            self.orchestrator = LLMOrchestrator(self.test_settings)
            
            # Store mocks for later use
            self.mock_openai_client = mock_openai.return_value
            self.mock_anthropic_client = mock_anthropic.return_value
            self.mock_google_client = mock_genai.GenerativeModel.return_value
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.mock_env_patcher.stop()
    
    def test_orchestrator_initialization(self):
        """Test 1: Verify orchestrator initializes with correct settings"""
        self.assertEqual(self.orchestrator.settings, self.test_settings)
        self.assertIn('openai', self.orchestrator.clients)
        self.assertIn('anthropic', self.orchestrator.clients)
        self.assertIn('google', self.orchestrator.clients)
    
    @patch('models.llm_clients.genai')
    def test_update_settings_google_model_change(self, mock_genai):
        """Test 2a: Update settings changes Google model"""
        new_settings = self.test_settings.copy()
        new_settings['models']['google'] = 'gemini-pro-vision'
        
        mock_genai.GenerativeModel.return_value = Mock()
        
        self.orchestrator.update_settings(new_settings)
        
        # Should create new Google client with updated model
        mock_genai.GenerativeModel.assert_called_with('gemini-pro-vision')
        self.assertEqual(self.orchestrator.settings, new_settings)
    
    def test_get_enabled_providers_all_enabled(self):
        """Test 3a: Get enabled providers when all are enabled"""
        enabled_providers = self.orchestrator._get_enabled_providers()
        
        # Should return all providers in priority order
        expected = ['openai', 'anthropic', 'google']  # Based on priority 1, 2, 3
        self.assertEqual(enabled_providers, expected)
    
    def test_get_enabled_providers_some_disabled(self):
        """Test 3b: Get enabled providers when some are disabled"""
        # Disable Google
        self.orchestrator.settings['provider_settings']['google']['enabled'] = False
        
        enabled_providers = self.orchestrator._get_enabled_providers()
        
        expected = ['openai', 'anthropic']  # Google disabled
        self.assertEqual(enabled_providers, expected)
    
    def test_get_enabled_providers_custom_priorities(self):
        """Test 3c: Get enabled providers with custom priorities"""
        # Change priorities: Google=1, OpenAI=2, Anthropic=3
        self.orchestrator.settings['provider_settings']['google']['priority'] = 1
        self.orchestrator.settings['provider_settings']['openai']['priority'] = 2
        self.orchestrator.settings['provider_settings']['anthropic']['priority'] = 3
        
        enabled_providers = self.orchestrator._get_enabled_providers()
        
        expected = ['google', 'openai', 'anthropic']  # New priority order
        self.assertEqual(enabled_providers, expected)
    
    def test_should_check_budget_disabled(self):
        """Test 4a: Budget checking when disabled"""
        # Budget tracking disabled in test_settings
        result = self.orchestrator._should_check_budget()
        self.assertFalse(result)
    
    def test_should_check_budget_enabled(self):
        """Test 4b: Budget checking when enabled"""
        self.orchestrator.settings['cost_management']['track_costs'] = True
        result = self.orchestrator._should_check_budget()
        self.assertTrue(result)
    
    @patch('models.llm_clients.cost_tracker')
    def test_chat_with_all_parallel_execution(self, mock_cost_tracker):
        """Test 5a: Chat with all providers in parallel mode"""
        # Set up mock responses
        self.orchestrator._call_openai = Mock(return_value={
            'response': 'OpenAI response', 'success': True, 'latency': 100
        })
        self.orchestrator._call_anthropic = Mock(return_value={
            'response': 'Anthropic response', 'success': True, 'latency': 150
        })
        self.orchestrator._call_google = Mock(return_value={
            'response': 'Google response', 'success': True, 'latency': 200
        })
        
        # Mock cost tracking
        mock_cost_tracker.estimate_message_tokens.return_value = 100
        mock_cost_tracker.estimate_cost.return_value = 0.01
        
        responses = self.orchestrator.chat_with_all("Test message")
        
        # Should have responses from all providers
        self.assertIn('openai', responses)
        self.assertIn('anthropic', responses)
        self.assertIn('google', responses)
        
        # Verify all provider methods were called
        self.orchestrator._call_openai.assert_called_once()
        self.orchestrator._call_anthropic.assert_called_once()
        self.orchestrator._call_google.assert_called_once()
    
    @patch('models.llm_clients.cost_tracker')
    def test_chat_with_all_sequential_execution(self, mock_cost_tracker):
        """Test 5b: Chat with all providers in sequential mode"""
        # Disable parallel requests
        self.orchestrator.settings['response_settings']['parallel_requests'] = False
        
        # Mock responses
        self.orchestrator._call_openai = Mock(return_value={
            'response': 'OpenAI response', 'success': True, 'latency': 100
        })
        self.orchestrator._call_anthropic = Mock(return_value={
            'response': 'Anthropic response', 'success': True, 'latency': 150
        })
        self.orchestrator._call_google = Mock(return_value={
            'response': 'Google response', 'success': True, 'latency': 200
        })
        
        # Mock cost tracking
        mock_cost_tracker.estimate_message_tokens.return_value = 100
        mock_cost_tracker.estimate_cost.return_value = 0.01
        
        responses = self.orchestrator.chat_with_all("Test message")
        
        # Should still have responses from all providers
        self.assertIn('openai', responses)
        self.assertIn('anthropic', responses)
        self.assertIn('google', responses)
    
    @patch('models.llm_clients.cost_tracker')
    def test_chat_with_all_smart_routing(self, mock_cost_tracker):
        """Test 5c: Chat with smart routing stops at first success"""
        # Enable smart routing and sequential processing
        self.orchestrator.settings['cost_management']['smart_routing'] = True
        self.orchestrator.settings['response_settings']['parallel_requests'] = False
        
        # Mock first provider success
        self.orchestrator._call_openai = Mock(return_value={
            'response': 'OpenAI response', 'success': True, 'latency': 100
        })
        self.orchestrator._call_anthropic = Mock(return_value={
            'response': 'Anthropic response', 'success': True, 'latency': 150
        })
        self.orchestrator._call_google = Mock(return_value={
            'response': 'Google response', 'success': True, 'latency': 200
        })
        
        mock_cost_tracker.estimate_message_tokens.return_value = 100
        mock_cost_tracker.estimate_cost.return_value = 0.01
        
        responses = self.orchestrator.chat_with_all("Test message")
        
        # Should only have OpenAI response (first successful)
        self.assertIn('openai', responses)
        self.assertEqual(len(responses), 1)
        
        # Only OpenAI should be called
        self.orchestrator._call_openai.assert_called_once()
        self.orchestrator._call_anthropic.assert_not_called()
        self.orchestrator._call_google.assert_not_called()
    
    def test_chat_with_all_no_enabled_providers(self):
        """Test 5d: Chat with no enabled providers"""
        # Disable all providers
        for provider in ['openai', 'anthropic', 'google']:
            self.orchestrator.settings['provider_settings'][provider]['enabled'] = False
        
        responses = self.orchestrator.chat_with_all("Test message")
        
        # Should return error
        self.assertIn('error', responses)
        self.assertEqual(responses['error'], 'No providers enabled')
    
    def test_call_openai_success(self):
        """Test 6a: Successful OpenAI API call"""
        # Mock successful OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "OpenAI test response"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 25
        mock_response.usage.total_tokens = 75
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.orchestrator._call_openai("Test message")
        
        # Verify response structure
        self.assertTrue(result['success'])
        self.assertEqual(result['response'], "OpenAI test response")
        self.assertEqual(result['model'], 'gpt-4')
        self.assertIn('latency', result)
        self.assertIn('tokens', result)
        self.assertEqual(result['tokens']['total'], 75)
    
    def test_call_openai_error(self):
        """Test 6b: OpenAI API call with error"""
        # Mock API error
        self.mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = self.orchestrator._call_openai("Test message")
        
        # Should handle error gracefully
        self.assertFalse(result['success'])
        self.assertIn('Error: API Error', result['response'])
        self.assertIn('latency', result)
    
    def test_call_anthropic_success(self):
        """Test 7a: Successful Anthropic API call"""
        # Mock successful Anthropic response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Anthropic test response"
        mock_response.usage.input_tokens = 40
        mock_response.usage.output_tokens = 30
        
        self.mock_anthropic_client.messages.create.return_value = mock_response
        
        result = self.orchestrator._call_anthropic("Test message")
        
        # Verify response structure
        self.assertTrue(result['success'])
        self.assertEqual(result['response'], "Anthropic test response")
        self.assertEqual(result['model'], 'claude-3-sonnet-20240229')
        self.assertIn('latency', result)
        self.assertIn('tokens', result)
        self.assertEqual(result['tokens']['total'], 70)  # 40 + 30
    
    def test_call_anthropic_error(self):
        """Test 7b: Anthropic API call with error"""
        # Mock API error
        self.mock_anthropic_client.messages.create.side_effect = Exception("Anthropic API Error")
        
        result = self.orchestrator._call_anthropic("Test message")
        
        # Should handle error gracefully
        self.assertFalse(result['success'])
        self.assertIn('Error: Anthropic API Error', result['response'])
        self.assertIn('latency', result)
    
    def test_call_google_success(self):
        """Test 8a: Successful Google API call"""
        # Mock successful Google response
        mock_response = Mock()
        mock_response.text = "Google test response"
        
        self.mock_google_client.generate_content.return_value = mock_response
        
        result = self.orchestrator._call_google("Test message")
        
        # Verify response structure
        self.assertTrue(result['success'])
        self.assertEqual(result['response'], "Google test response")
        self.assertEqual(result['model'], 'gemini-pro')
        self.assertIn('latency', result)
    
    def test_call_google_error(self):
        """Test 8b: Google API call with error"""
        # Mock API error
        self.mock_google_client.generate_content.side_effect = Exception("Google API Error")
        
        result = self.orchestrator._call_google("Test message")
        
        # Should handle error gracefully
        self.assertFalse(result['success'])
        self.assertIn('Error: Google API Error', result['response'])
        self.assertIn('latency', result)
    
    def test_call_provider_unknown_provider(self):
        """Test 9: Call unknown provider"""
        result = self.orchestrator._call_provider('unknown_provider', "Test message")
        
        self.assertFalse(result['success'])
        # Updated to match actual error message format
        self.assertEqual(result['response'], 'Unknown_Provider client not available')
        self.assertEqual(result['latency'], 0)
    
    @patch('models.llm_clients.cost_tracker')
    def test_budget_checking_prevents_request(self, mock_cost_tracker):
        """Test 10a: Budget checking prevents expensive requests"""
        # Enable budget tracking
        self.orchestrator.settings['cost_management']['track_costs'] = True
        self.orchestrator.settings['cost_management']['daily_budget'] = 1.0
        
        # Mock high cost estimate
        mock_cost_tracker.estimate_message_tokens.return_value = 1000
        mock_cost_tracker.estimate_cost.return_value = 0.5  # More than 20% of $1 budget
        
        responses = self.orchestrator.chat_with_all("Expensive test message")
        
        # Should skip requests due to budget
        for provider, response in responses.items():
            self.assertFalse(response['success'])
            self.assertIn('budget limits', response['response'])
    
    @patch('models.llm_clients.cost_tracker')
    def test_budget_checking_allows_reasonable_request(self, mock_cost_tracker):
        """Test 10b: Budget checking allows reasonable requests"""
        # Enable budget tracking
        self.orchestrator.settings['cost_management']['track_costs'] = True
        self.orchestrator.settings['cost_management']['daily_budget'] = 10.0
        
        # Mock reasonable cost estimate
        mock_cost_tracker.estimate_message_tokens.return_value = 100
        mock_cost_tracker.estimate_cost.return_value = 0.01  # Much less than 20% of $10 budget
        
        # Mock provider responses
        self.orchestrator._call_openai = Mock(return_value={
            'response': 'OpenAI response', 'success': True, 'latency': 100
        })
        self.orchestrator._call_anthropic = Mock(return_value={
            'response': 'Anthropic response', 'success': True, 'latency': 150
        })
        self.orchestrator._call_google = Mock(return_value={
            'response': 'Google response', 'success': True, 'latency': 200
        })
        
        responses = self.orchestrator.chat_with_all("Reasonable test message")
        
        # Should proceed with requests
        self.assertIn('openai', responses)
        self.assertIn('anthropic', responses)
        self.assertIn('google', responses)
    
    def test_context_preparation_with_limit(self):
        """Test 11: Context preparation respects limit"""
        # Set context limit
        self.orchestrator.settings['memory_settings']['context_count'] = 3
        
        # Mock provider to avoid actual API calls
        self.orchestrator._call_openai = Mock(return_value={
            'response': 'Test response', 'success': True, 'latency': 100
        })
        
        # Provide more context than limit
        context = ["Context 1", "Context 2", "Context 3", "Context 4", "Context 5"]
        
        # Mock cost tracking to avoid errors
        with patch('models.llm_clients.cost_tracker') as mock_cost_tracker:
            mock_cost_tracker.estimate_message_tokens.return_value = 100
            mock_cost_tracker.estimate_cost.return_value = 0.01
            
            self.orchestrator.chat_with_all("Test message", context)
            
            # Check that the call was made (context limiting happens internally)
            self.orchestrator._call_openai.assert_called_once()
            
            # Verify the message includes limited context
            call_args = self.orchestrator._call_openai.call_args[0][0]
            # Should only include first 3 context items
            for i in range(3):
                self.assertIn(f"Context {i+1}", call_args)
            # Should not include contexts 4 and 5
            self.assertNotIn("Context 4", call_args)
            self.assertNotIn("Context 5", call_args)
    
    def test_response_settings_integration(self):
        """Test 12: Response settings are passed to API calls"""
        # Custom response settings
        self.orchestrator.settings['response_settings'] = {
            'max_tokens': 2000,
            'temperature': 0.9,
            'timeout': 60,
            'parallel_requests': True
        }
        
        # Mock OpenAI call to capture arguments
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        self.orchestrator._call_openai("Test message")
        
        # Verify settings were passed to API call
        call_kwargs = self.mock_openai_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['max_tokens'], 2000)
        self.assertEqual(call_kwargs['temperature'], 0.9)
        self.assertEqual(call_kwargs['timeout'], 60)


if __name__ == '__main__':
    unittest.main()