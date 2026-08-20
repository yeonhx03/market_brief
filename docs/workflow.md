# Market Brief Workflow

## Current Status

Current phase:

```text
Phase 8A - real article-level FinBERT runtime preparation
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
- 29 passing tests and Ruff check at the Mac handoff review

Pending:

- real PyTorch and Transformers runtime
- real `ProsusAI/finbert` classifier wrapper
- analysis bootstrap factory and CLI
- repeated-analysis prevention
- real BBC article verification and benchmark
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
