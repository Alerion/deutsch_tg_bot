Run with:

    uv sync
    . .venv/bin/activate
    python -m main start_bot

Install pre-commit hooks:

    uvx pre-commit install

Format and check code:

    uv run ruff format
    uv run ruff check --fix
