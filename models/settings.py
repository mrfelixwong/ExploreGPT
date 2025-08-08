import json
import os
from typing import Dict, Any

class SettingsManager:
    def __init__(self, settings_file='user_settings.json'):
        self.settings_file = settings_file
        self.default_settings = self._get_default_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Simplified default configuration settings"""
        return {
            'models': {
                'openai': 'gpt-3.5-turbo',
                'anthropic': 'claude-3-sonnet-20240229',
                'google': 'gemini-1.5-flash'
            },
            'response_settings': {
                'max_tokens': 1000,
                'temperature': 0.7,
                'timeout': 30,
                'show_metadata': True
            },
            'ui_settings': {
                'theme': 'light',
                'selected_provider': 'openai',
                'show_timestamps': True
            },
            'cost_management': {
                'track_costs': True
            }
        }
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_settings(self.default_settings, saved_settings)
            except (json.JSONDecodeError, IOError):
                pass
        return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            # Merge with defaults to ensure consistency
            merged_settings = self._merge_settings(self.default_settings, settings)
            with open(self.settings_file, 'w') as f:
                json.dump(merged_settings, f, indent=2)
            return True
        except IOError:
            return False
    
    def _merge_settings(self, defaults: Dict, user_settings: Dict) -> Dict:
        """Recursively merge user settings with defaults"""
        result = defaults.copy()
        for key, value in user_settings.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result
    
    def get_model_config(self, settings: Dict[str, Any]) -> Dict[str, str]:
        """Get model configuration for LLM clients"""
        return settings.get('models', self.default_settings['models'])
    
    # Removed unused methods: get_enabled_providers, is_within_budget
    # These were part of the complex multi-provider system that's no longer needed
    
    def get_ui_classes(self, settings: Dict[str, Any]) -> Dict[str, str]:
        """Get CSS classes based on UI settings"""
        ui_settings = settings.get('ui_settings', {})
        
        return {
            'theme_class': f"theme-{ui_settings.get('theme', 'light')}",
            'font_class': f"font-{ui_settings.get('font_size', 'medium')}",
            'layout_class': f"layout-{ui_settings.get('layout', 'grid')}"
        }

# Global settings instance
settings_manager = SettingsManager()