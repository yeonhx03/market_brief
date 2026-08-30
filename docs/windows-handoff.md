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

### Current Windows Workstation

- project path: `D:\Projects\market_brief`
- working branch: `feat/finbert-integration`
- operating system: Windows 10 Home, build `19045.7663`
- CPU: Intel Core i7-10700K
- RAM: 16 GB
- GPU: NVIDIA GeForce RTX 2070 SUPER, 8 GB VRAM
- storage rule: keep the repository and Hugging Face model cache on the D drive because the C
  drive has insufficient free space

The first end-to-end inference and benchmark still use CPU so the minimum runtime path is explicit
and later Linux server sizing is not based on an available local GPU. After that path passes, the
RTX 2070 SUPER may be tested separately as an optional comparison. CUDA support must not become a
requirement for collection, deterministic briefing, or normal tests.

Recorded runtime details:

- architecture: AMD64, 64-bit Windows
- Python: `3.11.16`
- uv: `0.12.5`
- PyTorch: `2.12.1+cpu`
- Transformers: `5.15.0`
- CUDA build: none; CPU execution was used for Phase 8A
- NVIDIA driver: `591.59`; `nvidia-smi` works, but GPU inference was intentionally deferred
- selected model: `ProsusAI/finbert`
- selected revision: `4556d13015211d73dccd3fdd39d39232506f3e43`
- uv cache: `D:\Caches\uv`
- uv-managed Python directory: `D:\Tools\uv-python`
- Hugging Face cache: `D:\Caches\huggingface`
- observed Hugging Face cache size after model resolution: 835.6 MiB

The selected revision is loaded with `use_safetensors=False`. Hugging Face also created a separate
safetensors conversion revision in the cache, which explains why total cache use is larger than
the roughly 418 MiB original PyTorch weight file. Neither cache content nor model weights belong
in Git.

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

### Phase 8A Results

Phase 8A article-level implementation and technical verification completed on August 30, 2026.

- First real CPU inference downloaded/resolved the model successfully: model loading took
  16.775 s and inference took 0.063 s.
- A cached direct model load took 0.853 s and one direct inference took 0.028 s after PyTorch and
  Transformers had already been imported.
- The end-to-end standardized measurements below include lazy imports, model construction,
  inference, and SQLite persistence as separate recorded portions.

| Articles | Model load | Inference and SQLite save | Total | Peak working set | Result |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 6.163 s | 0.037 s | 6.199 s | 744.6 MiB | 1 analyzed, 0 skipped |
| 10 | 6.121 s | 0.293 s | 6.414 s | 747.4 MiB | 10 analyzed, 0 skipped |
| 50 | 5.887 s | 1.590 s | 7.477 s | 748.9 MiB | 50 analyzed, 0 skipped |

The 50-article set contained 31 BBC Business and 19 BBC Technology headlines. The second
50-article CLI run reported `Analyzed 0 articles. Skipped 50 existing analyses.` and the database
still contained exactly 50 analysis rows. Stored probabilities summed to 1 within normal
floating-point tolerance.

The ordinary `briefing` CLI was run twice with identical output. Immediately afterward,
`transformers` and `torch` were both absent from `sys.modules`, confirming that the deterministic
non-analysis path does not load the optional model runtime.

The current CLI constructs the model before it checks each selected article for an existing
analysis. Duplicate inference and storage are prevented, but an all-skipped run still pays the
model startup cost. This is a documented optimization opportunity and does not change the stored
result or Phase 8A correctness.

### Sentiment briefing

Phase 8B sentiment briefing implementation and verification completed on August 30, 2026.

- The existing deterministic `briefing` command remains unchanged.
- Separate `SentimentBriefing` models and `GenerateSentimentBriefingService` read stored results.
- The selected analysis must match the analysis type, analyzer name, and pinned model revision.
- Articles without the selected analysis are reported explicitly instead of being treated as neutral.
- Text and persistence-ready JSON outputs are deterministic for the same stored data.
- JSON retains original probabilities and omits a live generation timestamp.
- The briefing path does not construct FinBERT or load PyTorch and Transformers.
- Output describes headline-language sentiment, not expected stock movement or a trading signal.

The real 52-article BBC benchmark database produced 50 analyzed items and 2 missing items. The
selected labels were 5 positive, 34 neutral, and 11 negative. Repeated text and JSON runs were
byte-for-byte identical, and the database remained at 52 article rows and 50 analysis rows. The
full suite passed with 59 tests and Ruff reported no errors.

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

Phase 8A and Phase 8B requirements, real BBC verification, the full 59-test suite, and Ruff have
passed. The remaining Windows handoff step is to push the Phase 8B commit and verify it on the
remote branch. GPU comparison is optional and is not required to complete the handoff.

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
