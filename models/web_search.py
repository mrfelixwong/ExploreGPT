"""Simplified web search functionality"""
import requests
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
from .debug_logger import debug_search, debug_error, debug_log

class SearchResult:
    """Simple search result container"""
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

class SimpleWebSearch:
    """Simplified web search with Brave and DuckDuckGo fallback"""
    
    def __init__(self, brave_api_key: str = None):
        self.brave_api_key = brave_api_key
        
        # Simple patterns for detecting search intent
        self.search_triggers = [
            'search', 'look up', 'find', 'latest', 'current', 'recent', 
            'today', 'news', 'happening', 'google', 'web'
        ]
        
        # Temporal keywords that often need fresh information
        self.temporal_keywords = ['today', 'latest', 'current', 'recent', '2024', '2025']
    
    def should_search(self, message: str) -> bool:
        """Check if message needs web search"""
        message_lower = message.lower()
        
        debug_log("search_intent_check", {
            "message_length": len(message),
            "has_triggers": any(trigger in message_lower for trigger in self.search_triggers),
            "has_temporal": any(keyword in message_lower for keyword in self.temporal_keywords)
        })
        
        # Check for explicit search requests
        if any(trigger in message_lower for trigger in self.search_triggers):
            return True
        
        # Check for temporal questions
        has_temporal = any(keyword in message_lower for keyword in self.temporal_keywords)
        has_question = any(q in message_lower for q in ['what', 'how', 'when', 'where', 'who'])
        
        return has_temporal and has_question
    
    def search(self, query: str, count: int = 5, extract_content: bool = False) -> List[SearchResult]:
        """Perform web search with fallback"""
        debug_log("web_search_start", {
            "query": query[:50],  # Truncate for privacy
            "count": count,
            "extract_content": extract_content,
            "has_brave_key": bool(self.brave_api_key)
        })
        
        start_time = time.time()
        results = []
        
        # Try Brave Search first
        if self.brave_api_key:
            results = self._search_brave(query, count)
        
        # Fallback to DuckDuckGo if needed
        if not results:
            results = self._search_duckduckgo(query, count)
        
        # Extract content if requested
        if extract_content and results:
            self._extract_content(results[:3])  # Only extract top 3 for performance
        
        # Log search operation
        latency = round((time.time() - start_time) * 1000, 2)
        provider = 'brave' if self.brave_api_key and results else 'duckduckgo'
        debug_search(query[:50], provider, len(results), True, latency)
        
        debug_log("web_search_complete", {
            "results_count": len(results),
            "provider_used": provider,
            "latency_ms": latency,
            "success": len(results) > 0
        })
        
        return results
    
    def _search_brave(self, query: str, count: int) -> List[SearchResult]:
        """Search using Brave API"""
        try:
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={'q': query, 'count': count},
                headers={'X-Subscription-Token': self.brave_api_key},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    SearchResult(
                        title=r.get('title', ''),
                        url=r.get('url', ''),
                        snippet=r.get('description', '')
                    )
                    for r in data.get('web', {}).get('results', [])
                ]
        except Exception as e:
            debug_error("brave_search_error", str(e), {"query": query})
        
        return []
    
    def _search_duckduckgo(self, query: str, count: int) -> List[SearchResult]:
        """Search using DuckDuckGo HTML parsing (no API needed)"""
        try:
            response = requests.get(
                "https://duckduckgo.com/html/",
                params={'q': query},
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                for result in soup.find_all('div', class_='result')[:count]:
                    title_elem = result.find('a', class_='result__a')
                    snippet_elem = result.find('a', class_='result__snippet')
                    
                    if title_elem:
                        results.append(SearchResult(
                            title=title_elem.get_text(strip=True),
                            url=title_elem.get('href', ''),
                            snippet=snippet_elem.get_text(strip=True) if snippet_elem else ''
                        ))
                
                return results
        except Exception as e:
            debug_error("duckduckgo_search_error", str(e), {"query": query})
        
        return []
    
    def _extract_content(self, results: List[SearchResult]):
        """Extract content from search results"""
        for result in results:
            try:
                response = requests.get(result.url, timeout=3, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove scripts and styles
                    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    
                    # Extract text from paragraphs
                    paragraphs = soup.find_all('p')[:5]  # First 5 paragraphs
                    content = ' '.join(p.get_text(strip=True) for p in paragraphs)
                    
                    # Limit content length
                    result.content = content[:500] + "..." if len(content) > 500 else content
                    
            except Exception:
                # Silent fail for content extraction
                pass
    
    def format_for_llm(self, query: str, results: List[SearchResult]) -> str:
        """Format search results for LLM context"""
        if not results:
            return "No search results found."
        
        formatted = f"Web search results for: {query}\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result.title}\n"
            formatted += f"   URL: {result.url}\n"
            
            if result.content:
                formatted += f"   Content: {result.content}\n"
            else:
                formatted += f"   Snippet: {result.snippet}\n"
            
            formatted += "\n"
        
        return formatted.strip()

# Global instance with optional API key
import os
web_search_manager = SimpleWebSearch(brave_api_key=os.getenv('BRAVE_API_KEY'))