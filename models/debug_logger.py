#!/usr/bin/env python3
"""
ExploreGPT Debug Logger

Comprehensive logging system designed for Claude Code debugging assistance.
Provides structured JSON logging, session tracking, and Claude-specific debug modes.
"""

import json
import logging
import os
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ExploreGPTDebugger:
    """
    Main debugging class for ExploreGPT
    
    Features:
    - Structured JSON logging
    - Session tracking
    - Claude-specific debug mode
    - Error context capture
    - Performance monitoring
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.claude_debug_mode = os.getenv('CLAUDE_DEBUG', '0').lower() in ('1', 'true', 'yes')
        
        # Setup logging
        self._setup_logger()
        
        # Track session start
        self.session_start_time = time.time()
        self.log_debug("session_start", {
            "session_id": self.session_id,
            "claude_debug_mode": self.claude_debug_mode,
            "timestamp": datetime.now().isoformat()
        })
    
    def _setup_logger(self):
        """Configure structured logging"""
        # Create logs directory if it doesn't exist
        log_dir = Path("/tmp/exploregpt_logs")
        log_dir.mkdir(exist_ok=True)
        
        # Setup file handler
        log_file = log_dir / "exploregpt_debug.log"
        
        # Configure logger
        self.logger = logging.getLogger(f"exploregpt.{self.session_id}")
        self.logger.setLevel(logging.DEBUG if self.claude_debug_mode else logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler for persistent logs
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for Claude debug mode
        if self.claude_debug_mode:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '🐛 [%(levelname)s] %(asctime)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def log_debug(self, event_type: str, data: Dict[str, Any], level: str = "info"):
        """
        Log structured debug information
        
        Args:
            event_type: Type of event (e.g., 'api_call', 'search_query', 'error')
            data: Event data dictionary
            level: Log level ('debug', 'info', 'warning', 'error')
        """
        log_entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "claude_debug": self.claude_debug_mode
        }
        
        # Add performance context
        log_entry["session_duration"] = round(time.time() - self.session_start_time, 2)
        
        message = json.dumps(log_entry, indent=2 if self.claude_debug_mode else None)
        
        # Log at appropriate level
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
    
    def log_api_call(self, provider: str, model: str, message_length: int, 
                     start_time: float, success: bool = True, error: str = None,
                     response_data: Dict[str, Any] = None):
        """Log API call with comprehensive details"""
        duration = round((time.time() - start_time) * 1000, 2)  # ms
        
        call_data = {
            "provider": provider,
            "model": model,
            "message_length": message_length,
            "duration_ms": duration,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            call_data["error"] = error
            call_data["error_traceback"] = traceback.format_exc() if self.claude_debug_mode else None
        
        if response_data:
            call_data.update(response_data)
        
        level = "error" if not success else "info"
        self.log_debug("api_call", call_data, level)
    
    def log_search_activity(self, query: str, provider: str, results_count: int,
                           duration_ms: float, success: bool = True, error: str = None):
        """Log web search activity"""
        search_data = {
            "query": query,
            "provider": provider,
            "results_count": results_count,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            search_data["error"] = error
        
        level = "error" if not success else "info"
        self.log_debug("web_search", search_data, level)
    
    def log_streaming_event(self, event_type: str, provider: str, 
                           chunk_size: int = None, total_chunks: int = None,
                           error: str = None):
        """Log streaming events"""
        streaming_data = {
            "event_type": event_type,  # 'start', 'chunk', 'end', 'error'
            "provider": provider,
            "timestamp": datetime.now().isoformat()
        }
        
        if chunk_size is not None:
            streaming_data["chunk_size"] = chunk_size
        if total_chunks is not None:
            streaming_data["total_chunks"] = total_chunks
        if error:
            streaming_data["error"] = error
        
        level = "error" if error else "debug"
        self.log_debug("streaming", streaming_data, level)
    
    def log_user_action(self, action: str, details: Dict[str, Any] = None):
        """Log user interactions"""
        action_data = {
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            action_data.update(details)
        
        self.log_debug("user_action", action_data)
    
    def log_error(self, error_type: str, error_message: str, 
                  context: Dict[str, Any] = None, include_traceback: bool = True):
        """Log errors with full context"""
        error_data = {
            "error_type": error_type,
            "error_message": str(error_message),
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            error_data["context"] = context
        
        if include_traceback and self.claude_debug_mode:
            error_data["traceback"] = traceback.format_exc()
        
        self.log_debug("error", error_data, "error")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Generate session summary for debugging"""
        return {
            "session_id": self.session_id,
            "duration_seconds": round(time.time() - self.session_start_time, 2),
            "claude_debug_mode": self.claude_debug_mode,
            "start_time": datetime.fromtimestamp(self.session_start_time).isoformat(),
            "current_time": datetime.now().isoformat()
        }
    
    def create_debug_snapshot(self) -> Dict[str, Any]:
        """Create comprehensive debug snapshot"""
        snapshot = {
            "session_summary": self.get_session_summary(),
            "environment": {
                "claude_debug": self.claude_debug_mode,
                "python_version": os.sys.version,
                "working_directory": os.getcwd(),
                "environment_vars": {
                    key: "***" if "key" in key.lower() or "token" in key.lower() else value
                    for key, value in os.environ.items()
                    if key.startswith(('OPENAI_', 'ANTHROPIC_', 'GOOGLE_', 'CLAUDE_'))
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if self.claude_debug_mode:
            self.log_debug("debug_snapshot", snapshot)
        
        return snapshot


# Global debugger instance - initialized when first imported
_global_debugger: Optional[ExploreGPTDebugger] = None

def get_debugger(session_id: Optional[str] = None) -> ExploreGPTDebugger:
    """Get or create global debugger instance"""
    global _global_debugger
    
    if _global_debugger is None or (session_id and _global_debugger.session_id != session_id):
        _global_debugger = ExploreGPTDebugger(session_id)
    
    return _global_debugger

def is_claude_debug_enabled() -> bool:
    """Quick check if Claude debug mode is enabled"""
    return os.getenv('CLAUDE_DEBUG', '0').lower() in ('1', 'true', 'yes')


# Convenience functions for quick logging
def debug_log(event_type: str, data: Dict[str, Any], level: str = "info", session_id: str = None):
    """Quick debug logging function"""
    debugger = get_debugger(session_id)
    debugger.log_debug(event_type, data, level)

def debug_api_call(provider: str, model: str, message_length: int, start_time: float,
                   success: bool = True, error: str = None, response_data: Dict[str, Any] = None,
                   session_id: str = None):
    """Quick API call logging"""
    debugger = get_debugger(session_id)
    debugger.log_api_call(provider, model, message_length, start_time, success, error, response_data)

def debug_error(error_type: str, error_message: str, context: Dict[str, Any] = None,
                session_id: str = None):
    """Quick error logging"""
    debugger = get_debugger(session_id)
    debugger.log_error(error_type, error_message, context)