# CLAUDE.md - ExploreGPT Developer Guide

## Code Efficiency Mandate

**ALWAYS maintain the simplest and most efficient approach:**

- ✅ Single SQLite database for all storage (conversations, settings, costs)
- ✅ Only 2 LLM providers: OpenAI + Google (Anthropic removed - library issues)
- ✅ Single-purpose classes with minimal methods
- ✅ No multi-provider orchestration complexity
- ✅ Consolidated web search with simple fallback
- ✅ Basic cost estimation (not complex accounting)

**Current architecture is optimized at 1,029 lines (31.5% reduction achieved)**

## Project Structure

```
app.py              # Flask app (368 lines) - conversations, routes, db init
models/llm_clients.py   # LLM integration (289 lines) - OpenAI + Google only
models/settings.py      # Settings (99 lines) - SQLite-based config
models/cost_tracker.py  # Cost tracking (89 lines) - simple daily estimates
models/web_search.py    # Web search (184 lines) - Brave + DuckDuckGo
models/debug_logger.py  # Debug logging for Claude Code integration
```

## Development Guidelines

### Database
- Single SQLite file (`memory.db`) for all data
- Tables: conversations, settings, cost_tracking
- No JSON files allowed

### API Providers
- OpenAI: Full streaming support (primary)
- Google: Non-streaming fallback (secondary)
- Anthropic: REMOVED (broken library)

### Code Style
- Prefer editing existing files over creating new ones
- Never add unnecessary complexity
- Remove unused methods immediately
- Keep classes single-purpose

### Testing
```bash
python test_working_apis.py  # API connectivity
python run_tests.py          # Unit tests
```

### Claude Code Debug Integration
```bash
export CLAUDE_DEBUG=1
# Logs to /tmp/exploregpt_logs/exploregpt_debug.log
```

## Efficiency Checklist

When making changes, verify:
- [ ] No unused imports or methods
- [ ] Single storage system (SQLite only)
- [ ] Minimal provider complexity
- [ ] No dead code paths
- [ ] Functions have single responsibility
- [ ] Classes are focused and small

**If complexity increases, simplify immediately. This codebase must remain minimal and efficient.**