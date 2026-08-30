# Market Brief Workflow

## Current Status

Current phase:

```text
Phase 11 - Web-first release preparation
```

Completed:

- Python 3.11 `uv` project setup
- `Article` domain model
- asynchronous RSS collector and error handling
- SQLite article persistence and URL duplicate prevention
- `collect` and `latest` CLI commands
- deterministic `Briefing` and `briefing` CLI command
- optional persisted `Article.id`
- `ArticleAnalysis` domain model
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
- separate `SentimentBriefing` and `SentimentBriefingItem` domain contract
- stored-analysis-only `GenerateSentimentBriefingService`
- exact analysis selection by type, analyzer name, and pinned revision
- explicit missing-analysis handling
- deterministic `sentiment-briefing` text output
- persistence-ready deterministic JSON output with original probabilities
- real 52-article BBC briefing verification with 50 analyses and 2 missing results
- legacy `briefing` regression verification without loading PyTorch or Transformers
- 59 passing tests and Ruff check after the Phase 8B implementation
- Phase 8A and 8B commits merged into GitHub `main` through pull request #1
- Windows feature branch deleted after merge
- Intel Mac local `main` fast-forwarded to the merge commit
- 59 passing tests and Ruff check on the Intel Mac after handoff
- separate Spring Boot Article, ArticleAnalysis, and Briefing REST contracts implemented locally
- Spring Data JPA, Flyway V1-V4, PostgreSQL configuration, and duplicate handling implemented
- `HttpArticleRepository` and `HttpArticleAnalysisRepository` adapters implemented
- explicit CLI `--api-url` integrated mode without implicit SQLite dual writes
- 70 passing Python tests and Ruff check after HTTP repository integration
- React + TypeScript + Vite selected for the first public client
- web-first repository boundaries, security rules, and deployment sequence documented
- `HttpBriefingRepository` and shared deterministic Spring payload mapping implemented
- HTTP `sentiment-briefing` persists once through `POST /api/briefings` without SQLite dual writes
- 75 passing Python tests and Ruff check after briefing HTTP persistence
- real PostgreSQL 17 connection, Flyway V1-V4, JPA schema validation, analysis persistence, and
  briefing persistence/retrieval verified locally
- live BBC Business RSS -> Python HTTP -> Spring -> PostgreSQL path exercised
- repeated analysis identity returned the same stored analysis ID
- live RSS verification exposed a blocking duplicate defect: collecting the same 35-item feed twice
  stored 70 rows representing only 33 distinct URLs
- Spring exact-URL duplicate fallback and Flyway V5 unique index implemented
- all 36 Spring tests passed after URL duplicate regression coverage
- corrected live BBC RSS verification saved 33 unique URLs on the first run, zero on the identical
  second run, and left 33 rows with 33 distinct URLs in PostgreSQL
- Spring `prod` profile, public read/protected write API boundary, restricted CORS, and Actuator
  health endpoint implemented
- all 46 Spring tests passed after production-boundary coverage
- every Python HTTP write adapter sends `X-Market-Brief-Key` from the `WRITE_API_KEY` environment
  variable while read requests omit the secret
- 77 passing Python tests and Ruff check after write-key propagation
- production-profile verification passed: public health returned `UP`, an unauthenticated write was
  rejected with 401, and authenticated Python writes stored 33 articles, one analysis, and one
  briefing through Spring in PostgreSQL 17
- Flyway V1-V5 and the production authentication boundary were verified together

Pending:

- verify the corrected Spring -> PostgreSQL data through the future React client
- create the separate `market_brief_web` repository and implement the read-only MVP
- deploy the web, Spring, PostgreSQL, and scheduled Python worker

## Immediate Plan

### Phase 11: Web-First Release

Goal:

Publish a read-only React web experience before building the Swift clients, while keeping Spring
as the only public data API and PostgreSQL owner.

Tasks:

1. Add Python briefing HTTP persistence and keep SQLite as a separate offline mode. (complete)
2. Verify the complete local flow against real PostgreSQL. (complete)
3. Prepare Spring production profiles, health checks, CORS, and server-to-server write protection.
   (complete, including Python header propagation and production-profile E2E verification)
4. Create `market_brief_web` with React, TypeScript, and Vite in a separate repository.
5. Show the latest briefing, recent articles, sentiment metadata, loading, empty, and error states.
6. Deploy Spring and PostgreSQL, then connect and deploy the static React build over HTTPS.
7. Deploy and schedule the Python worker and verify that new results appear in the browser.

Completion criteria:

- a public URL shows the latest persisted briefing and articles
- React contains no database or worker credentials
- Python write endpoints are protected independently from CORS
- a scheduled Python run updates PostgreSQL through Spring and becomes visible on the web

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

Phase 8B verification results from August 30, 2026:

- the 52-article BBC benchmark database produced 50 analyzed items and 2 explicit missing items
- selected labels were 5 positive, 34 neutral, and 11 negative
- two text runs and two JSON runs were byte-for-byte identical for the same database
- briefing generation did not change the 52 article rows or 50 analysis rows
- `torch` and `transformers` remained absent from `sys.modules`
- the existing `briefing` command remained deterministic and did not load the model runtime
- the full suite passed with 59 tests and Ruff reported no errors

## After Windows

After Phase 8A and 8B are committed and pushed, development returns immediately to the Intel Mac.

Mac sequence:

1. Create the separate Spring Boot `market_brief_api` project.
2. Implement Article, ArticleAnalysis, and Briefing REST contracts.
3. Connect Spring Data JPA and PostgreSQL.
4. Add Python `HttpArticleRepository` and `HttpArticleAnalysisRepository` adapters.
5. Verify RSS -> Spring -> PostgreSQL and FinBERT result -> Spring -> PostgreSQL.
6. Build and publish the React web client against the Spring API.
7. Deploy and schedule the Python collection/analysis job.
8. Build macOS and iOS SwiftUI clients against the same Spring API.

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
- React is the first public client and uses read-only Spring APIs over HTTPS.
- Swift clients consume the Spring API and do not run FinBERT locally.

## Verification Commands

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
git status --short --branch
```

Update this file after either Windows phase is completed or if the scope changes.
