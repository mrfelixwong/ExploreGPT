#!/usr/bin/env python3
"""
Simplified ExploreGPT Debug Logger

Minimal debugging system for Claude Code assistance.
Provides structured JSON logging when CLAUDE_DEBUG=1 is set.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class SimpleDebugger:
    """Minimal debugger for Claude Code integration"""
    
    def __init__(self):
        self.enabled = os.getenv('CLAUDE_DEBUG', '0').lower() in ('1', 'true', 'yes')
        if self.enabled:
            self._setup_logging()
    
    def _setup_logging(self):
        """Setup file logging when debug enabled"""
        log_dir = Path("/tmp/exploregpt_logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / "exploregpt_debug.log",
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            filemode='a'
        )
    
    def log(self, event_type: str, data: Dict[str, Any]):
        """Log event if debug enabled"""
        if not self.enabled:
            return
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data
        }
        logging.info(json.dumps(entry))
    
    def log_api_call(self, provider: str, success: bool, duration_ms: float, 
                     error: str = None, **kwargs):
        """Log API call with timing"""
        data = {
            "provider": provider,
            "success": success,
            "duration_ms": duration_ms
        }
        if error:
            data["error"] = error
        data.update(kwargs)
        
        self.log("api_call", data)
    
    def log_search(self, query: str, provider: str, results_count: int, 
                   success: bool, duration_ms: float, error: str = None):
        """Log web search activity"""
        self.log("web_search", {
            "query": query,
            "provider": provider,
            "results_count": results_count,
            "success": success,
            "duration_ms": duration_ms,
            "error": error
        })
    
    def log_error(self, error_type: str, message: str, context: Dict[str, Any] = None):
        """Log error with context"""
        data = {"error_type": error_type, "message": message}
        if context:
            data["context"] = context
        self.log("error", data)


# Global debugger instance
debugger = SimpleDebugger()

# Convenience functions
def debug_log(event_type: str, data: Dict[str, Any]):
    """Quick debug logging"""
    debugger.log(event_type, data)

def debug_api_call(provider: str, success: bool, duration_ms: float, **kwargs):
    """Quick API call logging"""
    debugger.log_api_call(provider, success, duration_ms, **kwargs)

def debug_search(query: str, provider: str, results_count: int, success: bool, 
                duration_ms: float, error: str = None):
    """Quick search logging"""
    debugger.log_search(query, provider, results_count, success, duration_ms, error)

def debug_error(error_type: str, message: str, context: Dict[str, Any] = None):
    """Quick error logging"""
    debugger.log_error(error_type, message, context)

def is_debug_enabled() -> bool:
    """Check if debug mode is enabled"""
    return os.getenv('CLAUDE_DEBUG', '0').lower() in ('1', 'true', 'yes')