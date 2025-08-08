import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import patch, mock_open

# Add the models directory to Python path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.settings import SettingsManager


class TestSettingsManager(unittest.TestCase):
    """
    Test scenarios for Settings Management:
    1. Default settings generation and structure validation
    2. Settings file loading with various file conditions
    3. Settings saving with file system errors
    4. Settings merging with nested dictionaries
    5. Provider configuration and priority handling
    6. Budget validation and edge cases
    7. UI class generation
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_settings_file = os.path.join(self.test_dir, 'test_settings.json')
        self.settings_manager = SettingsManager(self.test_settings_file)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def test_default_settings_structure(self):
        """Test 1: Verify default settings have all required keys and correct types"""
        defaults = self.settings_manager._get_default_settings()
        
        # Check top-level keys
        required_keys = ['models', 'response_settings', 'memory_settings', 
                        'ui_settings', 'cost_management', 'provider_settings']
        for key in required_keys:
            self.assertIn(key, defaults)
        
        # Check models structure
        self.assertIn('openai', defaults['models'])
        self.assertIn('anthropic', defaults['models'])
        self.assertIn('google', defaults['models'])
        
        # Check provider settings structure
        for provider in ['openai', 'anthropic', 'google']:
            self.assertIn(provider, defaults['provider_settings'])
            provider_config = defaults['provider_settings'][provider]
            self.assertIn('enabled', provider_config)
            self.assertIn('priority', provider_config)
            self.assertIn('fallback', provider_config)
            self.assertIsInstance(provider_config['enabled'], bool)
            self.assertIsInstance(provider_config['priority'], int)
        
        # Check cost management structure
        cost_mgmt = defaults['cost_management']
        self.assertIn('track_costs', cost_mgmt)
        self.assertIn('daily_budget', cost_mgmt)
        self.assertIn('monthly_budget', cost_mgmt)
        self.assertIsInstance(cost_mgmt['daily_budget'], (int, float))
        self.assertIsInstance(cost_mgmt['monthly_budget'], (int, float))
    
    def test_load_settings_with_missing_file(self):
        """Test 2a: Load settings when file doesn't exist - should return defaults"""
        # Ensure file doesn't exist
        if os.path.exists(self.test_settings_file):
            os.remove(self.test_settings_file)
        
        loaded_settings = self.settings_manager.load_settings()
        default_settings = self.settings_manager._get_default_settings()
        
        self.assertEqual(loaded_settings, default_settings)
    
    def test_load_settings_with_corrupted_json(self):
        """Test 2b: Load settings with corrupted JSON - should return defaults"""
        # Create corrupted JSON file
        with open(self.test_settings_file, 'w') as f:
            f.write('{"incomplete": json, "missing_brace":')
        
        loaded_settings = self.settings_manager.load_settings()
        default_settings = self.settings_manager._get_default_settings()
        
        self.assertEqual(loaded_settings, default_settings)
    
    def test_load_settings_with_valid_file(self):
        """Test 2c: Load settings with valid JSON file"""
        test_settings = {
            'models': {'openai': 'gpt-3.5-turbo'},
            'cost_management': {'daily_budget': 10.0}
        }
        
        with open(self.test_settings_file, 'w') as f:
            json.dump(test_settings, f)
        
        loaded_settings = self.settings_manager.load_settings()
        
        # Should have merged with defaults
        self.assertEqual(loaded_settings['models']['openai'], 'gpt-3.5-turbo')
        self.assertEqual(loaded_settings['cost_management']['daily_budget'], 10.0)
        # Should still have default values for unspecified keys
        self.assertIn('anthropic', loaded_settings['models'])
        self.assertIn('monthly_budget', loaded_settings['cost_management'])
    
    def test_save_settings_success(self):
        """Test 3a: Successfully save settings to file"""
        test_settings = {
            'models': {'openai': 'gpt-4'},
            'cost_management': {'daily_budget': 15.0}
        }
        
        result = self.settings_manager.save_settings(test_settings)
        self.assertTrue(result)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(self.test_settings_file))
        
        with open(self.test_settings_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['models']['openai'], 'gpt-4')
        self.assertEqual(saved_data['cost_management']['daily_budget'], 15.0)
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_settings_io_error(self, mock_file):
        """Test 3b: Handle IO error during save operation"""
        test_settings = {'models': {'openai': 'gpt-4'}}
        
        result = self.settings_manager.save_settings(test_settings)
        self.assertFalse(result)
    
    def test_merge_settings_nested_dictionaries(self):
        """Test 4a: Merge nested dictionaries correctly"""
        defaults = {
            'models': {'openai': 'gpt-4', 'anthropic': 'claude-3-sonnet'},
            'cost_management': {'daily_budget': 5.0, 'monthly_budget': 50.0}
        }
        
        user_settings = {
            'models': {'openai': 'gpt-3.5-turbo'},  # Override one model
            'cost_management': {'daily_budget': 10.0}  # Override one budget
        }
        
        merged = self.settings_manager._merge_settings(defaults, user_settings)
        
        # Should have user overrides
        self.assertEqual(merged['models']['openai'], 'gpt-3.5-turbo')
        self.assertEqual(merged['cost_management']['daily_budget'], 10.0)
        
        # Should preserve defaults for non-overridden values
        self.assertEqual(merged['models']['anthropic'], 'claude-3-sonnet')
        self.assertEqual(merged['cost_management']['monthly_budget'], 50.0)
    
    def test_merge_settings_with_new_keys(self):
        """Test 4b: Merge settings with completely new keys"""
        defaults = {'existing_key': {'sub_key': 'value'}}
        user_settings = {'new_key': {'new_sub_key': 'new_value'}}
        
        merged = self.settings_manager._merge_settings(defaults, user_settings)
        
        # Should have both old and new keys
        self.assertIn('existing_key', merged)
        self.assertIn('new_key', merged)
        self.assertEqual(merged['new_key']['new_sub_key'], 'new_value')
    
    def test_get_enabled_providers_with_priorities(self):
        """Test 5a: Get enabled providers in correct priority order"""
        test_settings = {
            'provider_settings': {
                'openai': {'enabled': True, 'priority': 3},
                'anthropic': {'enabled': True, 'priority': 1},
                'google': {'enabled': False, 'priority': 2}
            }
        }
        
        enabled_providers = self.settings_manager.get_enabled_providers(test_settings)
        
        # Should return enabled providers in priority order (1 = highest priority)
        expected = ['anthropic', 'openai']  # google disabled, anthropic has priority 1
        self.assertEqual(enabled_providers, expected)
    
    def test_get_enabled_providers_all_disabled(self):
        """Test 5b: Get enabled providers when all are disabled"""
        test_settings = {
            'provider_settings': {
                'openai': {'enabled': False, 'priority': 1},
                'anthropic': {'enabled': False, 'priority': 2},
                'google': {'enabled': False, 'priority': 3}
            }
        }
        
        enabled_providers = self.settings_manager.get_enabled_providers(test_settings)
        self.assertEqual(enabled_providers, [])
    
    def test_is_within_budget_tracking_disabled(self):
        """Test 6a: Budget check when tracking is disabled"""
        test_settings = {
            'cost_management': {'track_costs': False, 'daily_budget': 1.0}
        }
        
        result = self.settings_manager.is_within_budget(test_settings, 10.0)
        self.assertTrue(result)  # Should always return True when tracking disabled
    
    def test_is_within_budget_within_limit(self):
        """Test 6b: Budget check within reasonable limit"""
        test_settings = {
            'cost_management': {'track_costs': True, 'daily_budget': 10.0}
        }
        
        # Request costs 0.5, which is < 10% of daily budget (1.0)
        result = self.settings_manager.is_within_budget(test_settings, 0.5)
        self.assertTrue(result)
    
    def test_is_within_budget_exceeds_limit(self):
        """Test 6c: Budget check exceeding reasonable limit"""
        test_settings = {
            'cost_management': {'track_costs': True, 'daily_budget': 10.0}
        }
        
        # Request costs 2.0, which is > 10% of daily budget (1.0)
        result = self.settings_manager.is_within_budget(test_settings, 2.0)
        self.assertFalse(result)
    
    def test_get_ui_classes_all_settings(self):
        """Test 7a: Generate UI classes from settings"""
        test_settings = {
            'ui_settings': {
                'theme': 'dark',
                'font_size': 'large', 
                'layout': 'vertical'
            }
        }
        
        ui_classes = self.settings_manager.get_ui_classes(test_settings)
        
        expected = {
            'theme_class': 'theme-dark',
            'font_class': 'font-large', 
            'layout_class': 'layout-vertical'
        }
        self.assertEqual(ui_classes, expected)
    
    def test_get_ui_classes_missing_settings(self):
        """Test 7b: Generate UI classes with missing ui_settings"""
        test_settings = {}  # No ui_settings
        
        ui_classes = self.settings_manager.get_ui_classes(test_settings)
        
        # Should use defaults
        expected = {
            'theme_class': 'theme-light',
            'font_class': 'font-medium',
            'layout_class': 'layout-grid'
        }
        self.assertEqual(ui_classes, expected)
    
    def test_get_model_config(self):
        """Test 8: Extract model configuration from settings"""
        test_settings = {
            'models': {
                'openai': 'custom-gpt-4',
                'anthropic': 'custom-claude'
            }
        }
        
        model_config = self.settings_manager.get_model_config(test_settings)
        
        self.assertEqual(model_config['openai'], 'custom-gpt-4')
        self.assertEqual(model_config['anthropic'], 'custom-claude')
    
    def test_get_model_config_missing_models(self):
        """Test 8b: Get model config when models key is missing"""
        test_settings = {}  # No models key
        
        model_config = self.settings_manager.get_model_config(test_settings)
        
        # Should return defaults
        defaults = self.settings_manager._get_default_settings()
        self.assertEqual(model_config, defaults['models'])


if __name__ == '__main__':
    unittest.main()