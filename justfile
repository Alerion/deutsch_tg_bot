check-code:
    pre-commit run --all-files

commit:
    superclaude commit

start:
    uv run python -m main start_bot

count_tokens:
    uv run python -m main count_tokens
