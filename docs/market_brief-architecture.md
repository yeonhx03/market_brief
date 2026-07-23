# Market Brief Architecture

## 1. Project Goals

`market_brief` is a Python-based project for practicing Python while building a practical stock news collection and analysis tool.

The project has four main goals:

1. Practice Python through a real, long-term project.
2. Collect and organize stock market news for personal investment use.
3. Develop custom news-based indicators for market and stock analysis.
4. Prepare a future integration path with a larger personal algorithmic trading system.

The project should start as an independent application, not as a submodule inside a future trading bot. However, it should expose clean data and interfaces so that a future trading system can consume its results through an API, database, JSON export, or message queue.

Short-term integration with iOS/macOS Siri is also planned. Siri should be able to read generated news briefings through Shortcuts or a simple local API.

## 2. Core Architecture Direction

The project will begin as a modular monolith.

It should not start with microservices, Kafka, Redis, Kubernetes, or a complex deployment model. Instead, it should use a clear internal structure based on Clean Architecture / Ports and Adapters ideas.

The main architectural goal is to separate core logic from external tools.

```text
Domain
   ↑
Application
   ↑
Interfaces

Application Ports
   ↑
Infrastructure Adapters
```

This means:

- Domain models do not know about RSS, SQLite, FastAPI, Siri, or trading APIs.
- Application services coordinate workflows but do not directly depend on concrete collectors or databases.
- Infrastructure implements external adapters such as RSS collectors and SQLite repositories.
- Interfaces expose the application through CLI, API, and future UI or automation surfaces.
- Bootstrap code wires concrete implementations together.

## 3. Layer Responsibilities

### Domain Layer

The Domain layer contains the core concepts of the program.

Expected models:

```text
Article
NewsSource
AnalysisResult
Entity
Ticker
Briefing
MarketSignal
```

The Domain layer should remain pure Python as much as possible.

It should not import:

```text
RSS
Reuters
Investing.com
SQLite
PostgreSQL
FastAPI
Siri
OpenAI API
Brokerage API
```

Example:

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Article:
    source: str
    title: str
    url: str
    published_at: datetime | None
    collected_at: datetime
    raw_content: str | None = None
    cleaned_content: str | None = None
    content_hash: str | None = None
```

Analysis results should be separate from articles.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisResult:
    article_id: int
    analyzer_name: str
    analyzer_version: str
    sentiment_score: float | None = None
    importance_score: float | None = None
    event_type: str | None = None
    confidence: float | None = None
```

This separation allows the same article to be analyzed multiple times by different algorithms.

### Application Layer

The Application layer coordinates use cases.

Expected services:

```text
CollectNewsService
SearchNewsService
AnalyzeNewsService
GenerateBriefingService
ExportSignalService
```

Application services should depend on Domain models and Application Ports, not on concrete implementations.

For example, `CollectNewsService` should know that it has a `NewsCollector` and an `ArticleRepository`, but it should not know whether the collector is RSS, Reuters, Investing.com, or a paid API.

### Application Ports

Application Ports define the contracts that infrastructure adapters must satisfy.

News collection is designed as asynchronous from the beginning because it involves network I/O.

```python
from typing import Protocol

from market_brief.domain.models.article import Article


class NewsCollector(Protocol):
    async def fetch(self) -> list[Article]:
        ...
```

The repository remains synchronous for the MVP.

```python
from typing import Protocol

from market_brief.domain.models.article import Article


class ArticleRepository(Protocol):
    def save_new(self, articles: list[Article]) -> list[Article]:
        ...

    def get_latest(self, limit: int) -> list[Article]:
        ...

    def search(self, keyword: str) -> list[Article]:
        ...
```

Analyzers are also synchronous in the MVP.

```python
from typing import Protocol

from market_brief.domain.models.article import Article
from market_brief.domain.models.analysis_result import AnalysisResult


class NewsAnalyzer(Protocol):
    def analyze(self, article: Article) -> AnalysisResult:
        ...
```

### Infrastructure Layer

Infrastructure contains concrete implementations of Application Ports.

Examples:

```text
RSSCollector
ReutersCollector
InvestingCollector
NewsAPICollector

SQLiteArticleRepository
PostgreSQLArticleRepository

KeywordAnalyzer
FinBERTAnalyzer
LLMAnalyzer
PowellSpeechAnalyzer
```

Infrastructure may import Domain models and Application Ports.

Infrastructure should not import Application Services or Interface code.

### Interface Layer

The Interface layer exposes the application to users or external systems.

MVP interfaces:

```text
CLI
Siri-friendly output or HTTP API
```

Future interfaces:

```text
Web dashboard
macOS menu bar app
iOS app
Trading system API
```

Interfaces should call Application Services. They should not directly create SQLite repositories, RSS collectors, or analyzers.

### Bootstrap / Composition Root

Bootstrap is the only place that wires concrete implementations together.

Example:

```python
from market_brief.application.services.collect_news import CollectNewsService
from market_brief.infrastructure.collectors.rss_collector import RSSCollector
from market_brief.infrastructure.repositories.sqlite_repository import SQLiteArticleRepository


def build_collect_news_service() -> CollectNewsService:
    collector = RSSCollector(...)
    repository = SQLiteArticleRepository(...)

    return CollectNewsService(
        collector=collector,
        repository=repository,
    )
```

Prefer factory functions such as `build_collect_news_service()` over global service instances.

Avoid:

```python
collect_news_service = CollectNewsService(...)
```

Global instances can make testing harder, create side effects during import, and complicate configuration and resource cleanup.

## 4. Dependency Rules

To reduce circular import risk, the project follows strict dependency rules:

1. Domain imports no other project layer.
2. Application Services import only Domain and Application Ports.
3. Infrastructure imports Domain and Application Ports.
4. Interfaces call Application Services.
5. Concrete implementations are created and connected only in Bootstrap.
6. Application Services must not directly import Infrastructure classes.
7. Interface code must not directly import Infrastructure classes.
8. Common data models should not be placed in Infrastructure or Interface layers.
9. Infrastructure modules should avoid depending on each other unless there is a clear, one-way utility relationship.

This structure greatly reduces circular reference risk, but it does not make circular imports impossible. Python can still produce circular imports if modules inside the same layer are designed poorly.

Later, dependency rules can be checked automatically with tools such as `import-linter`, but this is not required for the MVP.

## 5. Async / Sync Strategy

The project will use a mixed async/sync strategy.

Use async for:

```text
HTTP requests
RSS/news source fetching
Multiple source collection
Future FastAPI route handlers
```

Use sync for the MVP:

```text
SQLite storage
Article normalization
Keyword analysis
Briefing generation
Basic CLI commands
```

The first async boundary is the news collector.

```python
class CollectNewsService:
    def __init__(
        self,
        collector: NewsCollector,
        repository: ArticleRepository,
    ):
        self.collector = collector
        self.repository = repository

    async def execute(self) -> list[Article]:
        articles = await self.collector.fetch()
        return self.repository.save_new(articles)
```

The synchronous SQLite call may briefly block the event loop. For MVP usage, this is acceptable because the app is personal, small-scale, and not serving many concurrent users.

If SQLite writes become a bottleneck later, possible upgrade paths are:

1. Use `asyncio.to_thread()` for repository calls.
2. Change the repository port to async.
3. Add an async repository implementation such as `aiosqlite`.
4. Move to PostgreSQL with an async driver such as `asyncpg`.

Important note: switching from a sync repository port to an async repository port requires changing the port and the application service call sites. It is not only an implementation swap. The current architecture limits the affected area, but it does not eliminate the work.

CPU-heavy analysis should not be solved with `asyncio`.

Use:

```text
Network I/O       -> asyncio
CPU-heavy NLP     -> worker/process
Long jobs         -> background task or task queue
```

## 6. Error Handling Strategy

News collection is expected to fail often in small ways.

Common failures:

```text
Network timeout
HTTP error
Broken RSS/XML
Missing article fields
Invalid date format
HTML structure change
Encoding issue
Database lock
```

The program should not crash because of one bad article.

Recommended behavior:

```text
Single invalid article
-> skip article, log warning, continue

One source timeout
-> log error, continue with other sources if available

Database connection failure
-> fail the operation

Missing configuration or API key
-> fail fast
```

Avoid broad silent exception handling.

Bad:

```python
try:
    run_everything()
except Exception:
    pass
```

Better:

```python
try:
    article = normalizer.normalize(raw_item)
except InvalidArticleError:
    logger.warning("Invalid article skipped: missing required field")
    continue
```

Potential custom exceptions:

```text
CollectorError
SourceUnavailableError
NormalizationError
RepositoryError
ConfigurationError
```

MVP does not need a large exception hierarchy, but it should avoid treating every failure the same way.

## 7. Logging Strategy

Use Python's standard `logging` library from the beginning.

Do not rely on `print()` for application behavior or debugging.

Example:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Collected %d articles", len(articles))
logger.warning("Skipped invalid article: %s", url)
logger.exception("RSS collection failed")
```

Suggested log levels:

```text
DEBUG    Detailed parsing and development information
INFO     Job start/end, collected count, saved count
WARNING  Invalid article skipped, optional field missing
ERROR    Source failure, DB failure, unrecoverable operation error
```

Layer-specific logging:

```text
Infrastructure
- HTTP failures
- DB failures
- external API response issues

Application
- collection job started/completed
- saved article count
- skipped article count
- partial source failure

Interface
- CLI command requested
- API request received
- user-facing operation result
```

Domain code should usually avoid logging directly. It should return results or raise meaningful exceptions, and the caller can decide how to log.

## 8. Data and Storage Principles

Raw data and processed data should be kept separate.

```text
Raw article
-> normalized article
-> analysis result
-> investment indicator
-> trading signal
```

Do not overwrite raw article content with summaries or cleaned text.

Keep separate fields such as:

```text
raw_content
cleaned_content
summary
analysis_result
market_signal
```

Analysis results should include the analyzer name and version.

Examples:

```text
keyword_v1
rule_based_sentiment_v1
finbert_v1
llm_prompt_v2
powell_speech_v1
```

This allows the same article to be re-analyzed later and compared across algorithm versions.

## 9. Deduplication Strategy

For the MVP, exact duplicate prevention should be handled by the database.

Use SQLite `UNIQUE` constraints for stable identifiers such as:

```text
source + source_article_id
canonical_url
content_hash
```

Recommended MVP table idea:

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_article_id TEXT,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    canonical_url TEXT,
    published_at TEXT,
    collected_at TEXT NOT NULL,
    raw_content TEXT,
    cleaned_content TEXT,
    content_hash TEXT,
    UNIQUE(source, source_article_id),
    UNIQUE(canonical_url)
);
```

When inserting:

```sql
INSERT OR IGNORE INTO articles (...)
VALUES (...);
```

This is simpler and safer than checking for duplicates only in Python.

`domain/rules/deduplication.py` is not needed in the MVP.

Later, semantic duplicate detection may be added for cases such as:

```text
Same story with different URLs
Tracking parameters
Mobile vs desktop URL
Syndicated articles
Slightly modified headlines
```

That future feature should be treated separately from exact database-level duplicate prevention.

## 10. Initial Database Scope

MVP uses SQLite through Python's standard `sqlite3` module.

Initial table:

```text
articles
```

Possible columns:

```text
id
source
source_article_id
title
url
canonical_url
published_at
collected_at
raw_content
cleaned_content
content_hash
```

Near-future table:

```text
analysis_results
```

Possible columns:

```text
id
article_id
analyzer_name
analyzer_version
sentiment_score
importance_score
event_type
confidence
result_json
created_at
```

Frequently queried fields should be explicit columns. Experimental or flexible analysis output can be stored in `result_json`.

## 11. MVP Scope

The MVP should complete one working loop:

```text
Fetch news
-> normalize articles
-> skip invalid items
-> save new articles
-> classify by watchlist keywords
-> generate a short briefing
-> expose the briefing for CLI or Siri
```

MVP features:

1. Article domain model.
2. Async `NewsCollector` port.
3. RSS collector for one accessible source.
4. SQLite `ArticleRepository`.
5. Database-level exact duplicate prevention.
6. Watchlist keyword matching.
7. Latest-news briefing generation.
8. CLI commands.
9. Siri-readable text or JSON output.
10. Basic tests for collector mapping, repository duplicate behavior, and briefing generation.
11. Logging and simple error handling.

Not included in MVP:

```text
AI summarization
Sentiment analysis
Automatic ticker recognition
News importance score
Stock price integration
Backtesting
Realtime push notifications
Brokerage API
Automatic trading
Web dashboard
Message queue
Microservices
```

## 12. Recommended Stack

Core stack:

```text
Python 3.11+
uv
httpx
feedparser
sqlite3
asyncio
dataclasses
typing.Protocol
logging
argparse
pytest
pytest-asyncio
ruff
```

Use `httpx` for HTTP requests because it supports both sync and async APIs.

Use `feedparser` for RSS/Atom parsing.

Use Python's built-in `sqlite3` for MVP storage.

Use Python's built-in `logging` for logs.

Use `argparse` for the first CLI version.

Use `pytest` and `pytest-asyncio` for tests.

Use `ruff` for formatting and linting.

Add later:

```text
FastAPI
Uvicorn
Pydantic
beautifulsoup4
lxml
SQLAlchemy
PostgreSQL
Pandas
NumPy
scikit-learn
Transformers or external LLM API
```

Avoid in MVP:

```text
Redis
Celery
Kafka
Docker
Kubernetes
Airflow
LangChain
Vector database
React
Swift app
```

These may become useful later, but they are unnecessary for the first working version.

## 13. Suggested Directory Structure

Long-term target structure:

```text
market_brief/
├── src/
│   └── market_brief/
│       ├── domain/
│       │   ├── models/
│       │   │   ├── article.py
│       │   │   ├── analysis_result.py
│       │   │   └── briefing.py
│       │   └── rules/
│       │       └── classification.py
│       │
│       ├── application/
│       │   ├── ports/
│       │   │   ├── news_collector.py
│       │   │   ├── article_repository.py
│       │   │   └── news_analyzer.py
│       │   └── services/
│       │       ├── collect_news.py
│       │       ├── analyze_news.py
│       │       ├── search_news.py
│       │       └── generate_briefing.py
│       │
│       ├── infrastructure/
│       │   ├── collectors/
│       │   │   └── rss_collector.py
│       │   ├── repositories/
│       │   │   └── sqlite_repository.py
│       │   ├── analyzers/
│       │   │   └── keyword_analyzer.py
│       │   └── delivery/
│       │       └── json_exporter.py
│       │
│       ├── interfaces/
│       │   ├── cli/
│       │   │   └── commands.py
│       │   └── api/
│       │       └── routes.py
│       │
│       ├── bootstrap.py
│       ├── config.py
│       └── main.py
│
├── tests/
│   ├── unit/
│   └── integration/
├── config/
│   └── watchlist.toml
├── data/
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   └── decisions/
├── pyproject.toml
├── .env.example
└── README.md
```

Do not create every file on day one.

Initial files can be limited to:

```text
src/market_brief/domain/models/article.py
src/market_brief/application/ports/news_collector.py
src/market_brief/application/ports/article_repository.py
src/market_brief/application/services/collect_news.py
src/market_brief/infrastructure/collectors/rss_collector.py
src/market_brief/infrastructure/repositories/sqlite_repository.py
src/market_brief/interfaces/cli/commands.py
src/market_brief/bootstrap.py
```

Add more files only when there is a real feature that needs them.

## 14. Future Expansion Path

### Phase 1: MVP

```text
RSS source
SQLite
CLI
Keyword watchlist
Briefing text/JSON
Logging
Basic tests
```

### Phase 2: Siri Integration

```text
FastAPI
GET /health
GET /briefings/latest
GET /articles/latest
POST /collect
iOS/macOS Shortcuts
```

### Phase 3: More Sources

```text
Multiple RSS feeds
News APIs
Better timeout/retry handling
Concurrent collection with asyncio.gather()
Source-level failure isolation
```

### Phase 4: Analysis

```text
Keyword analyzer
Rule-based sentiment
Ticker/entity extraction
Importance scoring
LLM-assisted summaries
Central bank speech analysis
```

### Phase 5: Market Data and Research

```text
Price data API
News vs price movement comparison
Backtesting
Custom indicators
Pandas/NumPy analysis workflows
```

### Phase 6: Trading System Integration

```text
Stable JSON schema
REST API
Shared database or export table
Message queue if needed
Brokerage API integration in a separate trading system
Risk management layer
Execution engine
```

The news system should provide structured outputs to a future trading system. The trading system should not depend on the internal classes or database layout of this project.

Example future signal:

```json
{
  "schema_version": "1.0",
  "article_id": 381,
  "published_at": "2026-07-17T09:30:00Z",
  "source": "reuters",
  "tickers": ["NVDA"],
  "event_type": "earnings",
  "sentiment_score": 0.72,
  "importance_score": 0.84,
  "confidence": 0.67,
  "analyzer_version": "rule_based_v1"
}
```

## 15. Current Design Decisions

This section summarizes the current architecture choices. Dated decision history belongs in `market_brief-workflow.md`.

Accepted decisions:

```text
Use modular monolith instead of microservices.
Use Application Ports to reduce coupling.
Use Bootstrap as the only composition root.
Use async collection from the beginning.
Keep SQLite repository synchronous for MVP.
Use database constraints for exact duplicate prevention.
Use logging from the start.
Handle article-level errors without stopping the full job.
Keep raw data and analysis results separate.
Start with RSS before direct HTML scraping.
```

Rejected or postponed decisions:

```text
No automatic trading in MVP.
No AI summary in MVP.
No sentiment analysis in MVP.
No SQLAlchemy in MVP.
No Redis/Celery/Kafka in MVP.
No web dashboard in MVP.
No Swift app in MVP.
No microservice split in MVP.
```

## 16. Guiding Principle

The MVP should be small enough to build and understand, but structured enough that future work does not require starting over.

The first goal is not to build a perfect trading intelligence platform.

The first goal is to build one clean, working loop:

```text
collect -> store -> classify -> brief -> read
```

Everything else should grow from that loop.
