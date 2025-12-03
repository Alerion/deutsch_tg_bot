check-code:
    @echo "Checking code style and formatting..."
    uv run ruff format
    uv run ruff check --fix

commit:
    superclaude commit

start:
    uv run python -m main start_bot
