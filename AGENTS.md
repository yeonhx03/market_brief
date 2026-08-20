# Market Brief Agent Instructions

These instructions apply to the entire repository.

## Read First

Before making architectural, workflow, or implementation decisions, read:

1. `README.md`
2. `docs/architecture.md`
3. `docs/workflow.md`
4. `docs/windows-handoff.md` when working on Windows or on the FinBERT runtime

Verify the documents against the actual code before acting. Report a mismatch before changing
behavior or expanding scope.

## Current Direction

- Python owns RSS collection, FinBERT inference, and briefing generation.
- A separate Spring Boot application will own the REST persistence API and PostgreSQL.
- Future macOS and iOS clients will be written with Swift/SwiftUI and will call Spring over HTTPS.
- SQLite remains the local/offline Python persistence adapter.
- Integrated mode will use HTTP repository adapters; one run must not write implicitly to both
  SQLite and PostgreSQL.
- The current focused task is the temporary Windows FinBERT phase described in
  `docs/windows-handoff.md`.

## Working With The User

- The user is learning Python and backend development by writing code directly.
- Explain concepts and review user-written code before taking over implementation.
- If the user says only "코드 써줘", do not edit files. Provide the path, location, code, and
  verification commands in chat.
- Edit repository files only when the user clearly asks for the files to be modified directly.
- Do not block work for formatting differences. Point out syntax or functional errors.
- Prefer small, focused changes over broad rewrites.

## Architecture Rules

- Domain imports no project infrastructure or interface code.
- Application services depend on domain models and application ports.
- Infrastructure implements external adapters such as RSS, SQLite, HTTP, and FinBERT.
- Interfaces call application services.
- Bootstrap is the composition root for concrete implementations.
- FinBERT text sentiment is not stock-price impact or a BUY/SELL signal.
- Keep deterministic briefing behavior independent from optional model availability.
- Do not add watchlists, LLM summaries, entity impact, brokerage integration, or broad
  microservices during the Windows FinBERT task.

## Project Conventions

- Repository and Python package name: `market_brief`
- Python baseline: 3.11
- Package path: `application`, not `applications`
- Dependency and command manager: `uv`
- Tests: `uv run pytest -q`
- Lint: `uv run ruff check .`
- Never commit virtual environments, model caches, downloaded model weights, secrets, or local
  SQLite databases.

## Documentation And Git

- `README.md`, `AGENTS.md`, and the concise files under `docs/` are shared project documentation
  and should be committed when intentionally changed.
- `.local-docs/` contains optional detailed local history and is intentionally ignored by Git.
- Keep `docs/workflow.md` current after a phase or meaningful task is completed.
- Preserve user changes and do not revert unrelated work.
- Before moving between computers, run tests and Ruff, commit the intended files, push, and verify
  that the remote branch contains the commit.
