# CLAUDE_INSTRUCTIONS.md - Custom Instructions for ExploreGPT

## Project-Specific Instructions for Claude

### 🎯 Project Context
When working on ExploreGPT, Claude should always understand:
- This is a Flask-based multi-LLM chat application
- Primary goal: Enable simultaneous conversations with multiple AI providers
- Current working providers: OpenAI, Google Gemini
- Anthropic Claude is disabled due to library compatibility issues

### 🔧 Technical Requirements

#### **API Key Management**
- ✅ ALWAYS use environment variables (`~/.zshrc`)
- ❌ NEVER create `.env` files or store keys in code
- ✅ Reference `API_KEYS_SETUP.md` for key configuration
- ✅ Use `os.getenv()` for all API key access

#### **Port Configuration**
- ✅ ALWAYS use port 5001 (not 5000)
- ✅ Reason: Port 5000 conflicts with macOS AirPlay Receiver

#### **Code Style Guidelines**
- ✅ Server-side rendering only (no JavaScript)
- ✅ Use Flask templates with Jinja2
- ✅ Type hints where beneficial but not required
- ✅ Comprehensive error handling for all API calls
- ✅ Follow existing patterns in `models/` directory

#### **Testing Requirements**
- ✅ Maintain 100% pass rate on unit tests
- ✅ Use existing test structure in `tests/unit/`
- ✅ Test API integrations with mocking
- ✅ Reference `TESTING_INSTRUCTIONS.md` for procedures

### 🚫 What NOT to Do

#### **Security**
- ❌ Never commit API keys to repository
- ❌ Never suggest storing keys in files
- ❌ Never create `.env` files (project uses environment variables)
- ❌ Never expose API keys in error messages or logs

#### **Dependencies**
- ❌ Never add `python-dotenv` (removed from project)
- ❌ Never suggest Anthropic API fixes (known library issue)
- ❌ Never use port 5000 (macOS conflict)

#### **Code Changes**
- ❌ Never add JavaScript (server-side only)
- ❌ Never remove error handling from API calls
- ❌ Never change the SQLite schema without migration

### 🎨 UI/UX Guidelines

#### **Dark Mode**
- ✅ Theme controlled via `ui_settings.theme` in settings
- ✅ CSS classes: `theme-light`, `theme-dark` on body tag
- ✅ Settings passed via `ui_classes` to all templates

#### **Forms and Settings**
- ✅ All settings persist to `user_settings.json`
- ✅ Use Flask form handling (no AJAX)
- ✅ Comprehensive validation on all inputs

### 📁 File Organization Rules

#### **When Adding Features**
- ✅ Model logic goes in `models/` directory
- ✅ Templates go in `templates/` directory
- ✅ Tests go in `tests/unit/` directory
- ✅ Update `CLAUDE.md` for developer info
- ✅ Update `README.md` for user-facing changes

#### **Documentation Updates**
- ✅ `README.md` - User-facing information only
- ✅ `CLAUDE.md` - Developer/architecture information
- ✅ `API_KEYS_SETUP.md` - Security setup only
- ✅ `TESTING_INSTRUCTIONS.md` - Testing procedures only

### 🧪 Testing Philosophy
- ✅ Mock all external API calls in tests
- ✅ Test both success and failure scenarios
- ✅ Maintain existing test structure and naming
- ✅ 64 tests should remain passing at 100% rate

### 🔄 Development Workflow
1. **Read existing code** to understand patterns
2. **Follow established conventions** in the codebase
3. **Test changes** with `python run_tests.py`
4. **Update documentation** if adding features
5. **Never break** the existing functionality

### 💡 Helpful Context
- **User is Felix** - the project creator
- **Environment**: macOS with zsh shell
- **Python version**: 3.13 with virtual environment
- **Development**: Uses Claude Code CLI for assistance

### 🎯 Success Criteria
- All existing tests continue to pass
- New features follow established patterns
- API keys remain secure (environment variables only)
- Documentation stays current and non-overlapping
- Application runs on port 5001 without issues

---
*This file ensures Claude maintains consistency and follows project-specific best practices when working on ExploreGPT.*