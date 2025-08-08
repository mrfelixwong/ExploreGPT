import openai
import anthropic
from google import generativeai as genai
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .cost_tracker import cost_tracker

class LLMOrchestrator:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.clients = {}
        
        # Initialize OpenAI client
        try:
            self.clients['openai'] = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        except Exception as e:
            print(f"Warning: OpenAI client initialization failed: {e}")
            
        # Initialize Anthropic client with error handling
        try:
            self.clients['anthropic'] = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        except Exception as e:
            print(f"Warning: Anthropic client initialization failed: {e}")
            
        # Initialize Google client
        try:
            self.clients['google'] = self._setup_google()
        except Exception as e:
            print(f"Warning: Google client initialization failed: {e}")
    
    def _setup_google(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        return genai.GenerativeModel('gemini-1.5-flash')
    
    def update_settings(self, settings):
        """Update orchestrator settings"""
        self.settings = settings
        
        # Update Google model if needed
        google_model = settings.get('models', {}).get('google', 'gemini-pro')
        self.clients['google'] = genai.GenerativeModel(google_model)
    
    def chat_single(self, message, context=None):
        """Send message to the selected LLM provider"""
        # Get selected provider from settings
        selected_provider = self.settings.get('ui_settings', {}).get('selected_provider', 'openai')
        
        # Check if provider is available
        if selected_provider not in self.clients:
            return {
                'response': f'Provider {selected_provider} is not available',
                'success': False,
                'latency': 0,
                'provider': selected_provider
            }
        
        # Prepare context
        context_text = ""
        if context:
            context_count = self.settings.get('memory_settings', {}).get('context_count', 5)
            limited_context = context[:context_count]
            context_text = "\n\nRelevant context:\n" + "\n".join(limited_context)
        
        full_message = message + context_text
        
        # Check budget if cost tracking enabled
        if self._should_check_budget():
            estimated_tokens = cost_tracker.estimate_message_tokens(full_message)
            model = self.settings.get('models', {}).get(selected_provider, '')
            estimated_cost = cost_tracker.estimate_cost(selected_provider, model, estimated_tokens)
            
            daily_budget = self.settings.get('cost_management', {}).get('daily_budget', float('inf'))
            if estimated_cost > daily_budget / 5:  # Don't use more than 20% of daily budget on one request
                return {
                    'response': f'Request skipped: estimated cost ${estimated_cost:.4f} exceeds budget limits',
                    'success': False,
                    'latency': 0,
                    'provider': selected_provider
                }
        
        # Call the selected provider
        response = self._call_provider(selected_provider, full_message)
        response['provider'] = selected_provider
        
        return response
    
    def _get_enabled_providers(self):
        """Get list of enabled providers in priority order"""
        provider_settings = self.settings.get('provider_settings', {})
        enabled_providers = []
        
        # Get enabled providers with their priorities
        provider_priorities = []
        for provider in ['openai', 'anthropic', 'google']:
            config = provider_settings.get(provider, {'enabled': True, 'priority': 999})
            if config.get('enabled', True):
                priority = config.get('priority', 999)
                provider_priorities.append((priority, provider))
        
        # Sort by priority and return provider names
        provider_priorities.sort()
        return [provider for _, provider in provider_priorities]
    
    def _should_check_budget(self):
        """Check if budget tracking is enabled"""
        return self.settings.get('cost_management', {}).get('track_costs', False)
    
    def _chat_parallel(self, message, providers):
        """Send requests to all providers in parallel"""
        responses = {}
        
        with ThreadPoolExecutor(max_workers=len(providers)) as executor:
            # Submit all requests
            future_to_provider = {}
            for provider in providers:
                future = executor.submit(self._call_provider, provider, message)
                future_to_provider[future] = provider
            
            # Collect results
            for future in as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    result = future.result()
                    responses[provider] = result
                except Exception as e:
                    responses[provider] = {
                        'response': f'Error: {str(e)}',
                        'success': False,
                        'latency': 0
                    }
        
        return responses
    
    def _chat_sequential(self, message, providers):
        """Send requests to providers one by one"""
        responses = {}
        
        for provider in providers:
            try:
                result = self._call_provider(provider, message)
                responses[provider] = result
                
                # If smart routing is enabled and we got a good response, stop here
                if (self.settings.get('cost_management', {}).get('smart_routing', False) 
                    and result.get('success', False)):
                    break
                    
            except Exception as e:
                responses[provider] = {
                    'response': f'Error: {str(e)}',
                    'success': False,
                    'latency': 0
                }
        
        return responses
    
    def _call_provider(self, provider, message):
        """Call a specific provider"""
        # Check if provider client is available
        if provider not in self.clients:
            return {
                'response': f'{provider.title()} client not available',
                'success': False,
                'latency': 0
            }
            
        if provider == 'openai':
            return self._call_openai(message)
        elif provider == 'anthropic':
            return self._call_anthropic(message)
        elif provider == 'google':
            return self._call_google(message)
        else:
            return {
                'response': f'Unknown provider: {provider}',
                'success': False,
                'latency': 0
            }
    
    def _call_openai(self, message):
        start_time = time.time()
        try:
            model = self.settings.get('models', {}).get('openai', 'gpt-4')
            max_tokens = self.settings.get('response_settings', {}).get('max_tokens', 1000)
            temperature = self.settings.get('response_settings', {}).get('temperature', 0.7)
            timeout = self.settings.get('response_settings', {}).get('timeout', 30)
            
            response = self.clients['openai'].chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            result = {
                'response': response.choices[0].message.content,
                'success': True,
                'latency': round((time.time() - start_time) * 1000, 2),
                'model': model,
                'tokens': {
                    'input': response.usage.prompt_tokens,
                    'output': response.usage.completion_tokens,
                    'total': response.usage.total_tokens
                }
            }
            
            # Record cost if tracking enabled
            if self._should_check_budget():
                estimated_cost = cost_tracker.estimate_cost(
                    'openai', model, 
                    response.usage.prompt_tokens, 
                    response.usage.completion_tokens
                )
                cost_tracker.record_cost('openai', model, estimated_cost)
                result['estimated_cost'] = estimated_cost
            
            return result
            
        except Exception as e:
            return {
                'response': f'Error: {str(e)}',
                'success': False,
                'latency': round((time.time() - start_time) * 1000, 2)
            }
    
    def _call_anthropic(self, message):
        start_time = time.time()
        try:
            model = self.settings.get('models', {}).get('anthropic', 'claude-3-sonnet-20240229')
            max_tokens = self.settings.get('response_settings', {}).get('max_tokens', 1000)
            temperature = self.settings.get('response_settings', {}).get('temperature', 0.7)
            
            response = self.clients['anthropic'].messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": message}]
            )
            
            result = {
                'response': response.content[0].text,
                'success': True,
                'latency': round((time.time() - start_time) * 1000, 2),
                'model': model,
                'tokens': {
                    'input': response.usage.input_tokens,
                    'output': response.usage.output_tokens,
                    'total': response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            # Record cost if tracking enabled
            if self._should_check_budget():
                estimated_cost = cost_tracker.estimate_cost(
                    'anthropic', model,
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )
                cost_tracker.record_cost('anthropic', model, estimated_cost)
                result['estimated_cost'] = estimated_cost
            
            return result
            
        except Exception as e:
            return {
                'response': f'Error: {str(e)}',
                'success': False,
                'latency': round((time.time() - start_time) * 1000, 2)
            }
    
    def _call_google(self, message):
        start_time = time.time()
        try:
            model = self.settings.get('models', {}).get('google', 'gemini-1.5-flash')
            
            # Google doesn't expose the same configuration options
            response = self.clients['google'].generate_content(message)
            
            result = {
                'response': response.text,
                'success': True,
                'latency': round((time.time() - start_time) * 1000, 2),
                'model': model
            }
            
            # Record estimated cost if tracking enabled (Google doesn't provide token counts)
            if self._should_check_budget():
                estimated_tokens = cost_tracker.estimate_message_tokens(message)
                estimated_cost = cost_tracker.estimate_cost('google', model, estimated_tokens, 100)
                cost_tracker.record_cost('google', model, estimated_cost)
                result['estimated_cost'] = estimated_cost
            
            return result
            
        except Exception as e:
            return {
                'response': f'Error: {str(e)}',
                'success': False,
                'latency': round((time.time() - start_time) * 1000, 2)
            }