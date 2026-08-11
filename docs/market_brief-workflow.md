# Market Brief Workflow

This document tracks the working flow of the `market_brief` project.

Use this file as the project's operational map. While `market_brief-architecture.md` defines the architecture and `docs/AGENT.md` defines agent behavior, this file tracks what the project is doing now, what has been decided, and what is next.

## 1. Purpose of This File

The project will be split into multiple chats by task.

Examples:

```text
00 Project Direction
01 Environment Setup
02 Architecture Review
03 Article Domain Model
04 RSS Collector
05 SQLite Repository
06 Briefing Generator
07 Siri Integration
08 Code Review and Refactoring
```

Because task-specific chats can drift, this file should be used as the shared source of truth for:

- current project phase
- active task
- completed tasks
- next tasks
- major decisions
- known blockers
- open questions

## 2. Document Roles

Use each project document for its own purpose:

```text
docs/AGENT.md
-> agent working rules, required reading, Git/GitHub behavior

market_brief-architecture.md
-> architecture, dependency rules, MVP scope, stack, future expansion

market_brief-workflow.md
-> current progress, task roadmap, decisions, open questions, next actions
```

## 3. Current Project Status

Current phase:

```text
RSS Collector hardening after Phase 4 completion
```

Current focus:

```text
Add the deferred minimal error handling and logging to RSSCollector before starting Phase 5 CLI.
```

Current repository name:

```text
market_brief
```

Current architecture:

```text
Modular monolith
Ports and Adapters
Async news collection
Sync SQLite repository for MVP
Bootstrap as composition root
```

## 4. MVP Goal

The MVP is complete when this loop works:

```text
collect -> store -> classify -> brief -> read
```

In plain language:

1. Fetch news from one RSS source.
2. Normalize article data.
3. Skip invalid articles without crashing the entire job.
4. Save new articles to SQLite.
5. Prevent exact duplicates with database constraints.
6. Match articles against watchlist keywords.
7. Generate a short briefing.
8. Expose the briefing through CLI or Siri-friendly text/JSON.

## 5. Task Roadmap

### Phase 0: Project Setup

Status: Completed

Tasks:

- [x] Decide project name: `market_brief`
- [x] Install `uv`
- [x] Create architecture document
- [x] Create workflow document
- [x] Initialize repository with `uv`
- [x] Add `.gitignore`
- [x] Add core dependencies
- [x] Add development dependencies
- [x] Commit initial project setup

Core dependencies:

```text
httpx
feedparser
```

Development dependencies:

```text
pytest
pytest-asyncio
ruff
```

### Phase 1: Minimal Project Structure

Status: Completed

Goal:

Create only the first useful structure, not every future file.

Initial directories:

```text
src/market_brief/
tests/
docs/
config/
data/
```

Initial files:

```text
src/market_brief/domain/models/article.py
src/market_brief/application/ports/news_collector.py
src/market_brief/application/ports/article_repository.py
src/market_brief/application/services/collect_news.py
src/market_brief/bootstrap.py
```

### Phase 2: Article Model

Status: Completed

Goal:

Define the first `Article` domain model using `dataclass`.

Learning focus:

```text
dataclasses
datetime
type hints
frozen objects
domain model design
```

### Phase 2.5: Application Ports

Status: Completed

Goal:

Define the first Application Ports before writing concrete infrastructure.

Initial files:

```text
src/market_brief/application/ports/news_collector.py
src/market_brief/application/ports/article_repository.py
```

Completed ports:

```text
NewsCollector
ArticleRepository
```

Learning focus:

```text
typing.Protocol
async method contracts
repository contracts
dependency inversion
```

Decisions:

- Keep `ArticleRepository` limited to `save_new`, `get_latest`, and `search` for the MVP.
- Do not add delete or prune behavior until a storage retention policy is needed.

### Phase 3: RSS Collector

Status: Completed

Goal:

Implement one async RSS collector.

Target file:

```text
src/market_brief/infrastructure/collectors/rss_collector.py
```

Decision:

```text
RSSCollector is an Infrastructure Adapter.
Place it under src/market_brief/infrastructure/collectors/.
```

Learning focus:

```text
async/await
httpx.AsyncClient
feedparser
normalization
error handling
logging
```

Next:

```text
Add minimal error handling and logging after the SQLite repository is in place.
```

### Phase 4: SQLite Repository

Status: Completed

Goal:

Save collected articles to SQLite and prevent exact duplicates.

Learning focus:

```text
sqlite3
SQL basics
UNIQUE constraints
INSERT OR IGNORE
repository pattern
```

Completed so far:

- [x] Create the `articles` table on repository initialization.
- [x] Map all current `Article` fields, including `source_article_id` and `canonical_url`.
- [x] Store timezone-aware datetimes as UTC ISO 8601 text and restore them to `datetime`.
- [x] Prevent exact duplicates with database-level `UNIQUE` constraints and `INSERT OR IGNORE`.
- [x] Implement and verify `save_new`.
- [x] Implement and verify latest-first retrieval with `get_latest` and `limit`.
- [x] Implement and verify `search`.
- [x] Add focused pytest coverage for duplicate prevention, latest retrieval, and keyword search.

### Phase 5: CLI

Status: Not started

Goal:

Add command-line entry points for collecting and viewing latest articles.

Example commands:

```text
uv run python -m market_brief collect
uv run python -m market_brief latest --limit 10
```

Learning focus:

```text
argparse
application service wiring
bootstrap factory functions
```

### Phase 6: Briefing

Status: Not started

Goal:

Generate a simple briefing from recent or keyword-matched articles.

Learning focus:

```text
string formatting
data grouping
simple summarization rules
Siri-friendly text output
```

### Phase 7: Siri-Friendly Output

Status: Not started

Goal:

Expose briefing text or JSON so that iOS/macOS Shortcuts can read it.

First approach:

```text
local JSON or text file
```

Later approach:

```text
FastAPI endpoint
```

## 6. Chat Organization

Recommended project chats:

```text
00 Project Direction
01 Environment and Git Setup
02 Python Concepts
03 Architecture Review
04 Article Model
05 RSS Collector
06 SQLite Repository
07 CLI
08 Briefing and Siri
09 Code Review
10 Refactoring and Tests
```

Rules:

1. Use one chat per focused task.
2. At the start of a new task chat, mention the relevant phase from this workflow file.
3. Reference `docs/AGENT.md`, `market_brief-architecture.md`, and `market_brief-workflow.md` when project direction matters.
4. After a meaningful decision or completed task, update this workflow file.
5. Keep architecture decisions in `market_brief-architecture.md`; keep progress and next actions here.
6. Use the workflow coordination chat for checking current progress, deciding the next task, and keeping docs in sync.
7. If other market_brief task chats exist, review their latest progress before updating this workflow.

## 7. Decision Log

### 2026-07-17: Project Name

Decision:

```text
Use market_brief as the repository and project name.
```

Reason:

```text
The user chose this repository name after setting up the GitHub project.
```

### 2026-07-17: Architecture

Decision:

```text
Use modular monolith + Ports and Adapters.
```

Reason:

```text
This keeps the MVP understandable while leaving room for future RSS sources, analysis engines, Siri integration, and trading-system integration.
```

### 2026-07-17: Async Boundary

Decision:

```text
News collection should be async from the beginning.
SQLite repository remains sync for MVP.
```

Reason:

```text
Network I/O benefits from async. SQLite writes are small enough for MVP and simpler to learn synchronously.
```

### 2026-07-17: Duplicate Prevention

Decision:

```text
Use database-level UNIQUE constraints for exact duplicate prevention.
```

Reason:

```text
This is simpler and safer than relying only on Python-side duplicate checks.
```

### 2026-07-20: Project Setup Completed

Decision:

```text
Phase 0 is complete. The local repository has uv project files, .gitignore, core dependencies, development dependencies, and initial commits.
```

Reason:

```text
The local repository at ~/Projects/market_brief contains pyproject.toml, uv.lock, .gitignore, docs, and a clean git history with setup commits.
```

### 2026-07-20: Workflow Coordination Chat

Decision:

```text
Use this chat to check the current workflow, give the next task, and update docs only.
```

Reason:

```text
Implementation practice should stay in focused task chats or in the user's local work, while this chat keeps project state aligned.
```

### 2026-07-21: Python Version Baseline

Decision:

```text
Use Python 3.11 as the project's current baseline version.
```

Reason:

```text
The local repository now pins .python-version to 3.11 and pyproject.toml requires Python >=3.11.
```

### 2026-07-22: Package Name

Decision:

```text
Use market_brief as both the repository name and the Python package name.
```

Reason:

```text
The local source tree is src/market_brief, and architecture examples should match the actual package.
```

### 2026-07-22: Move To Application Ports

Decision:

```text
Treat the Article model as complete enough for now and start a focused NewsCollector port task.
```

Reason:

```text
The next learning step is to define the application's external contracts before implementing RSS collection.
```

### 2026-07-27: RSS Collector Skeleton Verified

Decision:

```text
Treat the first RSSCollector skeleton as complete for Phase 3.
```

Reason:

```text
The project now has a concrete infrastructure adapter that fetches RSS content asynchronously,
parses entries with feedparser, skips entries without title or URL, and maps valid entries to Article.
The collector was verified with a mocked RSS response that produced one valid Article and skipped one entry without a title.
```

### 2026-08-11: SQLite Repository Completed

Decision:

```text
Treat Phase 4 as complete. SQLiteArticleRepository now implements save_new, get_latest, and search,
with table creation, exact duplicate prevention, datetime mapping, and row-to-Article restoration.
```

Reason:

```text
The repository created an articles table in a temporary SQLite database, saved a new Article,
ignored the same Article on a second insert, restored a database row to an equal Article object,
returned multiple articles in the expected latest-first order with a working limit, and searched
title, raw content, and cleaned content while rejecting blank keywords. Three focused pytest tests pass.
```

## 8. Open Questions

Questions to resolve later:

- Which RSS source should be implemented first?
- Should configuration use TOML, YAML, or plain Python initially?
- Should first Siri integration use a local file or FastAPI?
- Which watchlist keywords and tickers should be included first?

## 9. Update Rules

Update this file when:

- a phase is completed
- a new phase starts
- a major implementation decision is made
- MVP scope changes
- dependencies are added or removed
- a task is postponed
- a blocker appears
- a GitHub issue or milestone becomes the source of truth for a task

Use short updates. This file should stay useful as a project map, not become a diary.

## 10. Next Action

Immediate next action:

```text
Add minimal error handling and logging to RSSCollector as deferred after Phase 3.
```

After that:

```text
Start Phase 5 by wiring the application service and bootstrap for the CLI.
```
