import json
import sqlite3
from typing import Dict, Any

class SettingsManager:
    """Settings manager using SQLite for persistence"""
    
    def __init__(self):
        self.default_settings = self._get_default_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Simplified default configuration settings"""
        return {
            'models': {
                'openai': 'gpt-3.5-turbo',
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
        """Load settings from SQLite database"""
        try:
            conn = sqlite3.connect('memory.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM settings WHERE key = 'user_settings' LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            
            if row:
                saved_settings = json.loads(row[0])
                # Merge with defaults to ensure all keys exist
                return self._merge_settings(self.default_settings, saved_settings)
        except (sqlite3.Error, json.JSONDecodeError):
            pass
        
        return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to SQLite database"""
        try:
            # Merge with defaults to ensure consistency
            merged_settings = self._merge_settings(self.default_settings, settings)
            settings_json = json.dumps(merged_settings, indent=2)
            
            conn = sqlite3.connect('memory.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value) 
                VALUES ('user_settings', ?)
            ''', (settings_json,))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
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