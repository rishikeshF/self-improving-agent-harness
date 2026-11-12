.PHONY: test eval eval-smoke lint

test:            ## fast, deterministic, fake LLM, no network
	uv run pytest -q

eval:            ## behaviour evals with the real model (needs ANTHROPIC_API_KEY)
	uv run python -m evals.run_evals

eval-smoke:      ## eval pipeline with the fake LLM (checks the harness, not quality)
	uv run python -m evals.run_evals --fake

lint:
	uv run ruff check .
