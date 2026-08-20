# Windows FinBERT Handoff

## Why This Project Is Moving To Windows

The primary development computer is an Intel Mac. The project is moving temporarily to a Windows
x86-64 computer for one reason: to install and verify the selected PyTorch/Transformers path for
the pretrained `ProsusAI/finbert` checkpoint without forcing an unsupported or fragile modern
runtime onto the Intel Mac.

This is not a decision to make Windows the permanent development or production platform. FinBERT
is not inherently Windows-only. Windows is the supported local machine currently available for
this specific inference task.

## Temporary Environment Rule

Windows is used only until these outcomes are complete:

1. Real `ProsusAI/finbert` inference runs on CPU.
2. Article-level results are stored and verified.
3. Repeated analysis is idempotent for the same model version.
4. Representative memory and timing benchmarks are recorded.
5. A real FinBERT-backed sentiment briefing is implemented and tested.
6. All changes are committed and pushed to GitHub.

Immediately after those outcomes, development moves back to the Intel Mac. Spring Boot,
PostgreSQL integration, Linux deployment work, Xcode, macOS, and iOS development will be done from
the Mac unless a later measured requirement proves otherwise.

## What Git Transfers

Git transfers portable project inputs:

- Python source code
- tests
- `pyproject.toml`
- `uv.lock`
- README and project documentation
- configuration examples that contain no secrets

Git does not transfer machine-specific runtime output:

- `.venv/`
- PyTorch native binaries from another operating system
- Hugging Face model cache or downloaded weights
- `__pycache__/`
- local SQLite databases under `data/*.db`
- `.env` or API keys
- benchmark temporary files
- Java `build/` or `target/`
- Xcode `DerivedData/`

Each operating system recreates its own virtual environment and native dependencies from the
tracked project metadata. Never copy `.venv` between macOS, Windows, and Linux.

## Before Leaving The Mac

1. Ensure the fresh-clone database directory issue is fixed and tested.
2. Add the Windows timezone-data dependency needed by `ZoneInfo("Asia/Seoul")`.
3. Run all tests and Ruff.
4. Review the diff and commit only intended files.
5. Push the current branch.
6. Verify the commit on GitHub.
7. Do not commit `data/market_brief.db`; plan to collect BBC articles again on Windows.

Suggested checks:

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
git status --short --branch
git log -3 --oneline
```

## First Windows Setup

Use PowerShell from the desired projects directory.

```powershell
git clone https://github.com/yeonhx03/market_brief.git
cd market_brief
uv sync --locked
uv run pytest -q
uv run ruff check .
```

Do not install or copy the Mac `.venv`. Let `uv` create a Windows environment.
The first `--locked` sync verifies that the committed lock file is portable without silently
rewriting it. Update `pyproject.toml` and `uv.lock` deliberately only when adding the optional
FinBERT dependencies.

Before adding model dependencies, record:

- Windows edition and architecture
- CPU and RAM
- Python version from `uv run python --version`
- exact PyTorch CPU build
- exact Transformers version
- selected `ProsusAI/finbert` model revision
- model cache location and size

## Windows Implementation Scope

### Real classifier

- Load `ProsusAI/finbert` through Transformers.
- Return positive, neutral, and negative probabilities, not only the top label.
- Configure the runtime explicitly for CPU first.
- Use headline-only input for the first working slice.
- Enable explicit truncation and record the maximum input length.
- Store the model name and pinned revision or meaningful version with every analysis.
- Keep imports lazy or isolated so non-analysis CLI commands do not require model loading.

### Application connection

- Reuse the existing `FinBERTAnalyzer` mapping boundary.
- Build the real classifier outside the domain and application layers.
- Add an analysis bootstrap factory.
- Add a CLI path for analyzing persisted articles.
- Skip results already stored for the same article and analyzer version.
- Preserve the ability to store a new result when the model version changes.

### Real verification

1. Collect BBC Business articles again on Windows.
2. Analyze one headline and inspect all three probabilities.
3. Analyze 10 headlines.
4. Analyze 50 headlines.
5. Repeat the command and confirm no duplicate same-version analyses.
6. Confirm `collect`, `latest`, and deterministic `briefing` work without loading the model.

Record for 1, 10, and 50 articles:

- first model download size
- cold model-load time
- warm inference time
- total elapsed time
- peak process memory
- success and failure counts

### Sentiment briefing

- Keep the existing deterministic briefing unchanged.
- Add a separate sentiment-aware contract and application service.
- Use stored results rather than invoking FinBERT during formatting.
- Handle articles without analysis explicitly.
- Produce deterministic text and a persistence-ready JSON representation.
- Do not call the result expected stock movement or a trading signal.

## Windows Completion Gate

Do not return to the Mac until:

- real FinBERT inference succeeds
- stored probabilities round-trip correctly
- duplicate inference/storage behavior is controlled
- 1/10/50 article measurements are documented
- real BBC sentiment briefing output is verified
- the full test suite passes
- Ruff passes
- the working tree contains only intentional changes
- commits are pushed and visible on GitHub

## Returning To The Intel Mac

On the Mac, use the existing clone or clone a clean copy, then fetch the Windows changes.

```bash
git status --short --branch
git pull --ff-only
uv sync --locked
uv run pytest -q
uv run ruff check .
```

`uv sync` recreates the Mac-compatible environment from project metadata. Windows `.venv`, native
PyTorch files, and Hugging Face caches must not be copied back.

The Mac may keep the optional FinBERT runtime uninstalled or unavailable. Collection,
deterministic briefing, Spring integration, and most tests must still work because the model
dependency is isolated from the normal application path.

The next task after returning is Spring Boot and PostgreSQL, not additional Windows-specific
development.
