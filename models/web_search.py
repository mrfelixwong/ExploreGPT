import requests
import re
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
from .debug_logger import debug_search, debug_error

class SearchResult:
    """Represents a single search result"""
    def __init__(self, title: str, url: str, snippet: str, content: str = None):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.content = content
    
    def to_dict(self):
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'content': self.content
        }

class SearchIntentDetector:
    """Detects when a user message requires web search"""
    
    def __init__(self):
        self.search_patterns = [
            r'search for',
            r'look up',
            r'find.*information',
            r'what.*latest',
            r'current.*news',
            r'recent.*updates',
            r'today.*news',
            r'what.*happening',
            r'latest.*on',
            r'find.*about',
            r'web search',
            r'google',
            r'search the web'
        ]
        
        self.temporal_patterns = [
            r'today',
            r'yesterday',
            r'this week',
            r'recent',
            r'latest',
            r'current',
            r'now',
            r'2024',
            r'2025'
        ]
    
    def needs_search(self, message: str) -> bool:
        """Determine if message requires web search"""
        message_lower = message.lower()
        
        # Direct search requests
        for pattern in self.search_patterns:
            if re.search(pattern, message_lower):
                return True
        
        # Questions about recent/current events
        has_temporal = any(re.search(p, message_lower) for p in self.temporal_patterns)
        has_question = any(word in message_lower for word in ['what', 'how', 'when', 'where', 'who', 'why'])
        
        return has_temporal and has_question
    
    def extract_query(self, message: str) -> str:
        """Extract search query from user message"""
        # Remove search trigger words
        query = re.sub(r'\b(search for|look up|find information about|google)\s+', '', message, flags=re.I)
        
        # Clean up common question words at the beginning
        query = re.sub(r'^(what is|what are|how do|how does|tell me about|explain)\s+', '', query, flags=re.I)
        
        return query.strip()

class BraveSearchProvider:
    """Brave Search API provider"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
    
    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """Search using Brave Search API"""
        if not self.api_key:
            return []
        
        try:
            response = requests.get(
                self.base_url,
                params={
                    'q': query,
                    'count': count,
                    'safesearch': 'moderate',
                    'freshness': 'pw'  # Past week for fresh results
                },
                headers={
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip',
                    'X-Subscription-Token': self.api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('web', {}).get('results', []):
                    result = SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('description', '')
                    )
                    results.append(result)
                
                return results
            
        except Exception as e:
            print(f"Brave Search error: {e}")
        
        return []

class DuckDuckGoProvider:
    """DuckDuckGo Instant Answers fallback provider"""
    
    def __init__(self):
        self.base_url = "https://api.duckduckgo.com"
    
    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """Search using DuckDuckGo Instant Answers API"""
        try:
            response = requests.get(
                self.base_url,
                params={
                    'q': query,
                    'format': 'json',
                    'no_redirect': '1',
                    'no_html': '1',
                    'skip_disambig': '1'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Abstract (instant answer)
                if data.get('Abstract'):
                    result = SearchResult(
                        title=data.get('Heading', 'DuckDuckGo Result'),
                        url=data.get('AbstractURL', ''),
                        snippet=data.get('Abstract', '')
                    )
                    results.append(result)
                
                # Related topics
                for topic in data.get('RelatedTopics', [])[:count-1]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        result = SearchResult(
                            title=topic.get('Text', '')[:100],
                            url=topic.get('FirstURL', ''),
                            snippet=topic.get('Text', '')
                        )
                        results.append(result)
                
                return results
                
        except Exception as e:
            print(f"DuckDuckGo Search error: {e}")
        
        return []

class SearchResultProcessor:
    """Processes and extracts content from search results"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (ExploreGPT/1.0; Web Search Bot)'
        })
    
    def extract_content(self, result: SearchResult, max_length: int = 1000) -> str:
        """Extract main content from a search result URL"""
        try:
            response = self.session.get(result.url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Find main content
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                if not main_content:
                    main_content = soup.find('body')
                
                if main_content:
                    text = main_content.get_text(separator=' ', strip=True)
                    # Clean up whitespace
                    text = re.sub(r'\s+', ' ', text)
                    return text[:max_length]
                
        except Exception as e:
            print(f"Content extraction error for {result.url}: {e}")
        
        return result.snippet
    
    def format_results(self, results: List[SearchResult], include_content: bool = False) -> str:
        """Format search results for LLM consumption"""
        if not results:
            return "No search results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            content = result.content if include_content and result.content else result.snippet
            
            formatted_result = f"""
{i}. **{result.title}**
   URL: {result.url}
   Content: {content}
"""
            formatted.append(formatted_result.strip())
        
        return "\n\n".join(formatted)

class WebSearchManager:
    """Main web search manager that coordinates all providers"""
    
    def __init__(self, brave_api_key: str = None):
        self.intent_detector = SearchIntentDetector()
        self.result_processor = SearchResultProcessor()
        
        # Initialize providers in priority order
        self.providers = []
        if brave_api_key:
            self.providers.append(BraveSearchProvider(brave_api_key))
        self.providers.append(DuckDuckGoProvider())
    
    def should_search(self, message: str) -> bool:
        """Check if message requires web search"""
        return self.intent_detector.needs_search(message)
    
    def search(self, query: str, count: int = 5, extract_content: bool = False) -> List[SearchResult]:
        """Search using available providers with fallback"""
        search_start_time = time.time()
        query = self.intent_detector.extract_query(query)
        
        for provider in self.providers:
            provider_start_time = time.time()
            provider_name = provider.__class__.__name__
            
            try:
                results = provider.search(query, count)
                provider_duration_ms = round((time.time() - provider_start_time) * 1000, 2)
                
                if results:
                    # Log successful search
                    debug_search(query, provider_name, len(results), True, provider_duration_ms)
                    
                    # Extract content if requested
                    if extract_content:
                        for result in results:
                            result.content = self.result_processor.extract_content(result)
                    
                    return results
                else:
                    # Log failed search attempt
                    debug_search(query, provider_name, 0, False, provider_duration_ms, "No results")
                    
            except Exception as e:
                error_msg = str(e)
                provider_duration_ms = round((time.time() - provider_start_time) * 1000, 2)
                
                # Log search provider error
                debug_search(query, provider_name, 0, False, provider_duration_ms, error_msg)
                debug_error("search_provider_error", error_msg, {"provider": provider_name})
                continue
        
        # No providers succeeded
        total_duration_ms = round((time.time() - search_start_time) * 1000, 2)
        debug_error("web_search_failed", f"All providers failed for query: {query}", 
                   {"duration_ms": total_duration_ms, "providers_tried": len(self.providers)})
        
        return []
    
    def format_for_llm(self, query: str, results: List[SearchResult]) -> str:
        """Format search results for LLM context"""
        if not results:
            return f"Web search for '{query}' returned no results."
        
        formatted = f"Web search results for '{query}':\n\n"
        formatted += self.result_processor.format_results(results, include_content=True)
        formatted += f"\n\n[Found {len(results)} results]"
        
        return formatted

# Global web search instance
web_search_manager = WebSearchManager()