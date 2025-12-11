check-code:
    uv run ruff format
    uv run ruff check --fix
    mypy

commit:
    superclaude commit

start:
    uv run python -m main start_bot

count_tokens:
    uv run python -m main count_tokens
