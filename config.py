#!/usr/bin/env python3
"""
FelixGPT Configuration Manager
Handles API key setup and validation
"""

import os
# Environment variables loaded from ~/.zshrc

# Load environment variables from .env file

class Config:
    """Configuration settings for FelixGPT"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    @classmethod
    def validate_keys(cls):
        """Validate that required API keys are set"""
        missing_keys = []
        warnings = []
        
        # Check Flask secret key
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-key-change-in-production':
            warnings.append("SECRET_KEY not set properly")
        
        # Check OpenAI key (required for basic functionality)
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == 'your-openai-api-key-here':
            missing_keys.append("OPENAI_API_KEY")
        
        # Check optional keys
        if not cls.ANTHROPIC_API_KEY or cls.ANTHROPIC_API_KEY == 'your-anthropic-api-key-here':
            warnings.append("ANTHROPIC_API_KEY (Anthropic provider will be disabled)")
        
        if not cls.GOOGLE_API_KEY or cls.GOOGLE_API_KEY == 'your-google-api-key-here':
            warnings.append("GOOGLE_API_KEY (Google provider will be disabled)")
        
        return missing_keys, warnings
    
    @classmethod
    def print_status(cls):
        """Print configuration status"""
        print("🔧 FelixGPT Configuration Status")
        print("=" * 40)
        
        missing_keys, warnings = cls.validate_keys()
        
        # Required keys
        if cls.OPENAI_API_KEY and cls.OPENAI_API_KEY != 'your-openai-api-key-here':
            print("✅ OpenAI API Key: Configured")
        else:
            print("❌ OpenAI API Key: MISSING (Required)")
        
        # Optional keys
        if cls.ANTHROPIC_API_KEY and cls.ANTHROPIC_API_KEY != 'your-anthropic-api-key-here':
            print("✅ Anthropic API Key: Configured")
        else:
            print("⚠️  Anthropic API Key: Missing (Optional)")
        
        if cls.GOOGLE_API_KEY and cls.GOOGLE_API_KEY != 'your-google-api-key-here':
            print("✅ Google API Key: Configured")
        else:
            print("⚠️  Google API Key: Missing (Optional)")
        
        if cls.SECRET_KEY and cls.SECRET_KEY != 'dev-key-change-in-production':
            print("✅ Flask Secret Key: Configured")
        else:
            print("⚠️  Flask Secret Key: Using default")
        
        print("=" * 40)
        
        if missing_keys:
            print("❌ CRITICAL: Missing required API keys:")
            for key in missing_keys:
                print(f"   - {key}")
            return False
        else:
            print("✅ All required keys configured!")
            if warnings:
                print("⚠️  Warnings:")
                for warning in warnings:
                    print(f"   - {warning}")
            return True

def setup_api_key():
    """Interactive setup for OpenAI API key"""
    print("\n🔑 OpenAI API Key Setup")
    print("=" * 30)
    print("Please provide your OpenAI API key.")
    print("You can get one from: https://platform.openai.com/api-keys")
    print()
    
    while True:
        api_key = input("Enter your OpenAI API key (sk-...): ").strip()
        
        if not api_key:
            print("❌ API key cannot be empty. Please try again.")
            continue
        
        if not api_key.startswith('sk-'):
            print("⚠️  OpenAI API keys usually start with 'sk-'. Are you sure this is correct?")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
        
        # Update .env file
        env_path = '.env'
        if os.path.exists(env_path):
            # Read existing content
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Replace the OpenAI API key line
            lines = content.split('\n')
            updated_lines = []
            openai_updated = False
            
            for line in lines:
                if line.startswith('OPENAI_API_KEY='):
                    updated_lines.append(f'OPENAI_API_KEY={api_key}')
                    openai_updated = True
                else:
                    updated_lines.append(line)
            
            # If key wasn't found, add it
            if not openai_updated:
                updated_lines.append(f'OPENAI_API_KEY={api_key}')
            
            # Write back to file
            with open(env_path, 'w') as f:
                f.write('\n'.join(updated_lines))
            
            print(f"✅ API key saved to {env_path}")
            break
        else:
            print(f"❌ .env file not found at {env_path}")
            break
    
    # Reload environment variables
    load_dotenv(override=True)
    print("✅ Configuration reloaded!")

if __name__ == '__main__':
    Config.print_status()
    
    missing_keys, warnings = Config.validate_keys()
    if 'OPENAI_API_KEY' in missing_keys:
        print("\n" + "=" * 50)
        setup_api_key()
        print("\n" + "=" * 50)
        Config.print_status()