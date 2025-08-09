import openai
from google import generativeai as genai
import os
import time
from .cost_tracker import cost_tracker
from .web_search import web_search_manager
from .debug_logger import debug_api_call

class LLMOrchestrator:
    """Simplified LLM orchestrator for single-provider use"""
    
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.clients = {}
        
        # Initialize OpenAI client
        try:
            self.clients['openai'] = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        except Exception as e:
            print(f"Warning: OpenAI client initialization failed: {e}")
            
        # Initialize Google client
        try:
            google_model = settings.get('models', {}).get('google', 'gemini-1.5-flash')
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self.clients['google'] = genai.GenerativeModel(google_model)
        except Exception as e:
            print(f"Warning: Google client initialization failed: {e}")
    
    def update_settings(self, settings):
        """Update orchestrator settings"""
        self.settings = settings
        
        # Update Google model if needed
        google_model = settings.get('models', {}).get('google', 'gemini-1.5-flash')
        if 'google' in self.clients:
            self.clients['google'] = genai.GenerativeModel(google_model)
    
    def chat_single(self, message, context=None):
        """Send message to the selected LLM provider"""
        selected_provider = self.settings.get('ui_settings', {}).get('selected_provider', 'openai')
        
        # Check if provider is available
        if selected_provider not in self.clients:
            return {
                'response': f'Provider {selected_provider} is not available',
                'success': False,
                'latency': 0,
                'provider': selected_provider
            }
        
        # Prepare message with context
        full_message = self._prepare_message(message, context)
        
        # Call the selected provider
        if selected_provider == 'openai':
            response = self._call_openai(full_message)
        elif selected_provider == 'google':
            response = self._call_google(full_message)
        else:
            response = {
                'response': f'Unknown provider: {selected_provider}',
                'success': False,
                'latency': 0
            }
        
        response['provider'] = selected_provider
        return response
    
    def chat_single_stream(self, message, context=None):
        """Stream message to the selected LLM provider with optional web search"""
        selected_provider = self.settings.get('ui_settings', {}).get('selected_provider', 'openai')
        
        # Check if provider is available
        if selected_provider not in self.clients:
            yield {
                'type': 'error',
                'message': f'Provider {selected_provider} is not available',
                'provider': selected_provider
            }
            return
        
        # Check if web search is needed
        search_results_text = ""
        if web_search_manager.should_search(message):
            yield {'type': 'searching', 'message': '🔍 Searching the web...'}
            
            search_results = web_search_manager.search(message, count=5, extract_content=True)
            if search_results:
                search_results_text = "\n\n" + web_search_manager.format_for_llm(message, search_results)
                yield {
                    'type': 'search_complete', 
                    'message': f'📰 Found {len(search_results)} results',
                    'results': [r.to_dict() for r in search_results]
                }
            else:
                yield {'type': 'search_complete', 'message': '⚠️ No search results found'}
        
        # Prepare message with context and search results
        full_message = self._prepare_message(message, context, search_results_text)
        
        # Stream from the selected provider
        if selected_provider == 'openai':
            yield from self._stream_openai(full_message)
        else:
            # Fallback to non-streaming for other providers
            yield {'type': 'start', 'provider': selected_provider}
            response = self._call_google(full_message)
            yield {
                'type': 'content', 
                'text': response['response'],
                'provider': selected_provider
            }
            yield {
                'type': 'end',
                'provider': selected_provider,
                'model': response.get('model', ''),
                'latency': response.get('latency', 0)
            }

    def _prepare_message(self, message, context=None, search_results=""):
        """Prepare message with context and search results"""
        parts = [message]
        
        if search_results:
            parts.append(search_results)
        
        if context:
            parts.append("\n\nRelevant context:\n" + "\n".join(context))
        
        return "".join(parts)

    def _stream_openai(self, message):
        """Stream OpenAI response"""
        start_time = time.time()
        model = self.settings.get('models', {}).get('openai', 'gpt-3.5-turbo')
        
        try:
            yield {'type': 'start', 'provider': 'openai', 'model': model}
            
            # Create streaming request
            stream = self.clients['openai'].chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                max_tokens=self.settings.get('response_settings', {}).get('max_tokens', 1000),
                temperature=self.settings.get('response_settings', {}).get('temperature', 0.7),
                timeout=self.settings.get('response_settings', {}).get('timeout', 30),
                stream=True
            )
            
            full_response = ""
            chunk_count = 0
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    chunk_count += 1
                    yield {
                        'type': 'content',
                        'text': content,
                        'provider': 'openai'
                    }
            
            # Send completion metadata
            latency = round((time.time() - start_time) * 1000, 2)
            
            # Log successful streaming call
            debug_api_call('openai', True, latency, model=model, 
                          streaming=True, chunks=chunk_count)
            
            yield {
                'type': 'end',
                'provider': 'openai',
                'model': model,
                'latency': latency,
                'full_response': full_response
            }
            
        except Exception as e:
            error_msg = str(e)
            latency = round((time.time() - start_time) * 1000, 2)
            
            # Log failed streaming call
            debug_api_call('openai', False, latency, model=model, 
                          streaming=True, error=error_msg)
            
            yield {
                'type': 'error',
                'message': f'Error: {error_msg}',
                'provider': 'openai',
                'latency': latency
            }
    
    def _call_openai(self, message):
        """Call OpenAI API"""
        start_time = time.time()
        model = self.settings.get('models', {}).get('openai', 'gpt-3.5-turbo')
        
        try:
            response = self.clients['openai'].chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                max_tokens=self.settings.get('response_settings', {}).get('max_tokens', 1000),
                temperature=self.settings.get('response_settings', {}).get('temperature', 0.7),
                timeout=self.settings.get('response_settings', {}).get('timeout', 30)
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
            if self.settings.get('cost_management', {}).get('track_costs', False):
                estimated_cost = cost_tracker.estimate_cost(
                    'openai', model, 
                    response.usage.prompt_tokens, 
                    response.usage.completion_tokens
                )
                cost_tracker.record_cost('openai', model, estimated_cost)
                result['estimated_cost'] = estimated_cost
            
            # Log successful API call
            debug_api_call('openai', True, result['latency'], 
                          model=model, tokens=result.get('tokens', {}))
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            result = {
                'response': f'Error: {error_msg}',
                'success': False,
                'latency': round((time.time() - start_time) * 1000, 2)
            }
            
            # Log failed API call
            debug_api_call('openai', False, result['latency'], 
                          model=model, error=error_msg)
            
            return result
    
    def _call_google(self, message):
        """Call Google Gemini API"""
        start_time = time.time()
        model = self.settings.get('models', {}).get('google', 'gemini-1.5-flash')
        
        try:
            response = self.clients['google'].generate_content(message)
            
            result = {
                'response': response.text,
                'success': True,
                'latency': round((time.time() - start_time) * 1000, 2),
                'model': model
            }
            
            # Record estimated cost if tracking enabled (Google doesn't provide token counts)
            if self.settings.get('cost_management', {}).get('track_costs', False):
                estimated_tokens = cost_tracker.estimate_message_tokens(message)
                estimated_cost = cost_tracker.estimate_cost('google', model, estimated_tokens, 100)
                cost_tracker.record_cost('google', model, estimated_cost)
                result['estimated_cost'] = estimated_cost
            
            # Log successful API call
            debug_api_call('google', True, result['latency'], model=model)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            result = {
                'response': f'Error: {error_msg}',
                'success': False,
                'latency': round((time.time() - start_time) * 1000, 2)
            }
            
            # Log failed API call
            debug_api_call('google', False, result['latency'], 
                          model=model, error=error_msg)
            
            return result