# CLAUDE.md - ExploreGPT Developer Guide

## Architecture Overview
Flask application with modular design using SQLite for persistence and environment-based configuration.

## Project Structure
```
exploregpt/
├── app.py              # Main Flask application (port 5001)
├── start.py            # Launcher with environment validation
├── models/
│   ├── llm_clients.py  # LLM orchestration logic
│   ├── settings.py     # Settings management
│   └── cost_tracker.py # API cost calculations
├── templates/          # Jinja2 HTML templates
└── tests/unit/         # Comprehensive test suite
```

## Development Guidelines

### API Keys
- ✅ Keys stored in `~/.zshrc` as environment variables
- ❌ Never commit API keys to the repository
- 📖 See `API_KEYS_SETUP.md` for configuration

### Testing
- 64 unit tests with 100% pass rate
- See `TESTING_INSTRUCTIONS.md` for complete procedures

### Technical Notes
- **Port**: 5001 (5000 conflicts with macOS AirPlay)
- **Anthropic**: See `ANTHROPIC_ISSUE.md` for library compatibility details

### Code Style
- Server-side rendering only (no JavaScript)
- Type hints where beneficial
- Comprehensive error handling
- 100% test coverage on critical paths

## Common Tasks

### Add New LLM Provider
1. Update `models/llm_clients.py` with new provider class
2. Add provider settings to `models/settings.py`
3. Update cost tracking in `models/cost_tracker.py`
4. Add provider to settings template

### Modify Dark Mode
- CSS styles in `templates/base.html`
- Theme class applied via `ui_classes.theme_class`
- Settings stored in `user_settings.json`

### Debug API Issues
```bash
# Test individual APIs
python test_working_apis.py

# Check environment variables
python start.py  # Will show missing vars
```

## Production Considerations
- Change `SECRET_KEY` from development default
- Disable Flask debug mode
- Consider rate limiting for API calls
- Add proper logging infrastructure

## Repository
https://github.com/mrfelixwong/ExploreGPT