# Market Brief Workflow

## Current Status

Current phase:

```text
Phase 8A technical verification complete; Phase 8B sentiment briefing next
```

Completed:

- Python 3.11 `uv` project setup
- `Article` domain model
- asynchronous RSS collector and error handling
- SQLite article persistence and URL duplicate prevention
- `collect` and `latest` CLI commands
- deterministic `Briefing` and `briefing` CLI command
- optional persisted `Article.id`
- strict `ArticleAnalysis` domain model
- SQLite analysis persistence and foreign-key verification
- `TextSentimentAnalyzer` and `ArticleAnalysisRepository` ports
- controlled `FinBERTAnalyzer` mapping and validation
- `AnalyzeArticleService`
- fake-classifier-to-SQLite integration test
- SQLite repositories create missing database parent directories on a fresh clone
- nested SQLite database files under `data/` are ignored by Git
- Windows installs `tzdata` conditionally for `ZoneInfo("Asia/Seoul")`
- optional PyTorch `2.12.1+cpu` and Transformers `5.15.0` runtime
- real `ProsusAI/finbert` classifier wrapper pinned to a model revision
- headline-only CPU inference with explicit truncation and maximum length 512
- analysis bootstrap factory and `analyze` CLI command
- repeated-analysis prevention by article, analysis type, analyzer, and version
- real BBC article persistence and 1/10/50-article CPU benchmarks
- non-analysis CLI verification without loading PyTorch or Transformers
- 42 passing tests and Ruff check after the Phase 8A implementation

Pending:

- sentiment briefing contract, service, CLI, and persistence-ready JSON shape

## Immediate Plan

### Phase 8A: Windows Article-Level FinBERT

Goal:

Run the pretrained `ProsusAI/finbert` model over stored English headlines and persist complete
article-level `ArticleAnalysis` records.

Tasks:

1. Verify Windows x86-64, Python 3.11, `uv`, CPU PyTorch, and Transformers compatibility.
2. Record exact dependency versions, model revision, cache path, and downloaded size.
3. Keep model dependencies optional so collection and deterministic briefing work without them.
4. Build a real classifier callable that returns all three labels.
5. Use headline-only input initially and enable explicit truncation.
6. Inject the real classifier into the existing `FinBERTAnalyzer` boundary.
7. Add bootstrap and an `analyze` CLI path over persisted articles.
8. Skip an analysis already stored for the same article, type, analyzer, and version.
9. Verify one stored BBC Business article.
10. Benchmark 1, 10, and 50 articles on CPU, recording model load time, total time, and peak memory.

Completion criteria:

- real model inference succeeds on Windows
- all three probabilities and final label are persisted
- repeated execution does not duplicate the same model-version result
- collection, latest, and deterministic briefing still work without loading FinBERT
- tests and Ruff pass

Phase 8A verification environment:

- Windows 10 Home build `19045.7663`, x86-64
- Intel Core i7-10700K, 16 GB RAM
- Python `3.11.16`
- PyTorch `2.12.1+cpu`, Transformers `5.15.0`
- model `ProsusAI/finbert`
- revision `4556d13015211d73dccd3fdd39d39232506f3e43`
- CPU execution; CUDA was intentionally not used

Cached-model benchmark results from August 30, 2026:

| Articles | Model load | Inference and SQLite save | Total | Peak working set |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 6.163 s | 0.037 s | 6.199 s | 744.6 MiB |
| 10 | 6.121 s | 0.293 s | 6.414 s | 747.4 MiB |
| 50 | 5.887 s | 1.590 s | 7.477 s | 748.9 MiB |

The 1- and 10-article measurements used BBC Business headlines. The 50-article measurement used
31 BBC Business and 19 BBC Technology headlines because the live Business feed contained only 33
items. All selected articles were analyzed once and stored. Repeating the 50-article CLI command
reported zero new analyses and 50 skipped existing analyses.

Model loading dominates the CPU runtime. After loading, inference and persistence averaged about
30 ms per headline. The current CLI still loads the model before discovering that every selected
article already has the same-version result; it prevents duplicate inference and storage, but this
startup cost is a possible later optimization rather than a Phase 8A correctness blocker.

### Phase 8B: Sentiment Briefing

Goal:

Produce a readable briefing that uses stored article-level sentiment without describing it as
stock-price impact.

Tasks:

1. Decide the smallest separate sentiment briefing contract.
2. Keep the existing deterministic `briefing` behavior intact.
3. Read persisted articles and analyses through ports.
4. Add a focused application service and CLI output.
5. Define a JSON shape that can later be posted to Spring.
6. Test empty data, missing analyses, ordering, labels, probabilities, and deterministic output.

Completion criteria:

- a real FinBERT-backed briefing runs against stored BBC articles
- output remains deterministic for the same stored data
- the result is structured for later Spring persistence
- tests and Ruff pass

## After Windows

After Phase 8A and 8B are committed and pushed, development returns immediately to the Intel Mac.

Mac sequence:

1. Create the separate Spring Boot `market_brief_api` project.
2. Implement Article, ArticleAnalysis, and Briefing REST contracts.
3. Connect Spring Data JPA and PostgreSQL.
4. Add Python `HttpArticleRepository` and `HttpArticleAnalysisRepository` adapters.
5. Verify RSS -> Spring -> PostgreSQL and FinBERT result -> Spring -> PostgreSQL.
6. Deploy Python, Spring, and PostgreSQL to a Linux server.
7. Schedule the Python collection/analysis job on the server.
8. Build macOS and iOS SwiftUI clients against the Spring API.

## Deferred Scope

Do not add during the Windows handoff:

- watchlists
- automatic company/ticker entity matching
- LLM summaries or LangChain agents
- entity-specific impact or price prediction
- brokerage APIs or order execution
- Redis, Kafka, Kubernetes, or broad microservice decomposition

## Decisions To Preserve

- FinBERT sentiment is financial-text sentiment, not a trading signal.
- Raw articles are stored before analysis.
- Newly stored articles are analyzed; duplicate collection does not trigger duplicate inference.
- Complete label probabilities are stored so aggregation rules can change without re-running the
  model.
- SQLite remains a valid local adapter.
- Integrated mode uses Spring HTTP APIs and PostgreSQL without implicit dual writes.
- Python owns collection, inference, and briefing generation.
- Spring owns public REST contracts and PostgreSQL.
- Swift clients consume the Spring API and do not run FinBERT locally.

## Verification Commands

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
git status --short --branch
```

Update this file after either Windows phase is completed or if the scope changes.
