# CLAUDE.md

## Project Overview

**deutsch_tg_bot** is a Telegram bot for learning German, targeting Ukrainian speakers. It uses Google Gemini AI to provide:

1. **Translation Training**: Users translate Ukrainian sentences to German with AI evaluation
2. **Situation Roleplay**: Interactive roleplay scenarios (restaurant, doctor, hotel, etc.) with real-time grammar feedback

## Tech Stack

- **Python 3.14+** with strict mypy type checking
- **python-telegram-bot**: Telegram bot framework with ConversationHandler pattern
- **google-genai**: Google Gemini AI for sentence generation, translation evaluation, and roleplay
- **pydantic / pydantic-settings**: Data validation and configuration
- **cyclopts**: CLI argument parsing
- **uv**: Package manager
- **just**: Task runner

## Commands

```bash
# Run the bot
just start
# or: uv run python -m main start_bot

# Check and format code
just check-code
# or manually:
uv run ruff format
uv run ruff check --fix
mypy

# Type checking only
mypy
```

## Code Style

- **Line length**: 100 (ruff), 120 max
- **Type hints**: Required everywhere (mypy strict mode)
- **Imports**: Sorted with isort via ruff
- **Formatting**: ruff format
- Don't generate docstings if it is not really necessary for undertanding what is going on.

## Architecture Patterns

### Conversation Handlers
Uses nested `ConversationHandler` state machines:
- Main handler (`training.py`): START → STORE_LEVEL → SELECT_TRAINING_TYPE → TRAINING_SESSION
- Exercise handler (`excercise.py`): CHECK_TRANSLATION ↔ ANSWER_QUESTION
- Situation handler: SELECT_SITUATION → ROLEPLAY_CONVERSATION

### User Session
`UserSession` dataclass holds all conversation state: level, training type, sentence history, AI chat sessions, async tasks.

### AI Integration
All AI calls follow: load prompt template → replace placeholders → call Gemini with JSON schema → validate with Pydantic.

### Async Patterns
- Background sentence prefetching with `asyncio.Task`
- Parallel grammar check + character response with `asyncio.gather()`

## Environment Variables

Required in `.env`:
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `GOOGLE_API_KEY`: Google Gemini API key

Optional:
- `SHOW_FULL_AI_RESPONSE`: Debug AI responses (default: True)
- `SHOW_TOCKENS_USAGE`: Show token usage stats
- `DEV_SKIP_SENTENCE_CONSTRAINT`: Skip constraint input for testing
