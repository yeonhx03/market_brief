# Geronimo Workflow

This document tracks the working flow of the `geronimo` project.

Use this file as the project's operational map. While `geronimo-architecture.md` defines the architecture, this file tracks what the project is doing now, what has been decided, what is next, and how separate ChatGPT/Codex chats should stay aligned.

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
- files or documents that should be referenced
- rules for how ChatGPT and Codex should help

## 2. Core Reference Files

Always consider these files before making architectural or workflow decisions:

```text
geronimo-architecture.md
geronimo-workflow.md
```

Roles:

```text
geronimo-architecture.md
-> architecture, dependency rules, MVP scope, stack, future expansion

geronimo-workflow.md
-> current progress, task flow, decisions, next actions, chat organization
```

## 3. Current Project Status

Current phase:

```text
Project setup
```

Current focus:

```text
Initialize the repository, project documents, uv environment, and first commit.
```

Current repository name:

```text
geronimo
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

Status: In progress

Tasks:

- [x] Decide project name: `geronimo`
- [x] Install `uv`
- [x] Create architecture document
- [x] Create workflow document
- [ ] Initialize repository with `uv`
- [ ] Add `.gitignore`
- [ ] Add core dependencies
- [ ] Add development dependencies
- [ ] Commit initial project setup

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

Status: Not started

Goal:

Create only the first useful structure, not every future file.

Initial directories:

```text
src/geronimo/
tests/
docs/
config/
data/
```

Initial files:

```text
src/geronimo/domain/models/article.py
src/geronimo/application/ports/news_collector.py
src/geronimo/application/ports/article_repository.py
src/geronimo/application/services/collect_news.py
src/geronimo/bootstrap.py
```

### Phase 2: Article Model

Status: Not started

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

### Phase 3: RSS Collector

Status: Not started

Goal:

Implement one async RSS collector.

Learning focus:

```text
async/await
httpx.AsyncClient
feedparser
normalization
error handling
logging
```

### Phase 4: SQLite Repository

Status: Not started

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

### Phase 5: CLI

Status: Not started

Goal:

Add command-line entry points for collecting and viewing latest articles.

Example commands:

```text
uv run python -m geronimo collect
uv run python -m geronimo latest --limit 10
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
3. Ask ChatGPT to reference both `geronimo-architecture.md` and `geronimo-workflow.md`.
4. After a meaningful decision or completed task, update this workflow file.
5. Keep architecture decisions in `geronimo-architecture.md`; keep progress and next actions here.

## 7. How ChatGPT Should Help

Default behavior:

```text
Explain concepts.
Ask clarifying questions when needed.
Give implementation steps.
Give hints before full code.
Review user-written code.
Point out design risks.
Keep the MVP small.
Avoid unnecessary tools and abstractions.
```

ChatGPT should not:

```text
Jump straight to full implementation unless asked.
Expand scope beyond MVP without explaining why.
Introduce major new dependencies casually.
Mix future trading-system concerns into MVP code.
Ignore the architecture document.
Ignore this workflow file.
```

When the user is stuck:

```text
1. Identify the exact failing point.
2. Explain the concept.
3. Give a small hint.
4. If still blocked, provide a focused example.
5. Only provide full code when explicitly requested.
```

## 8. How Codex Should Help

Default behavior:

```text
Inspect the repository.
Explain what existing code does.
Suggest small next steps.
Run tests when requested.
Review diffs.
Make minimal changes only when explicitly asked.
```

Because the project is for Python practice, Codex should avoid taking over implementation unless the user asks for direct edits.

When Codex edits files:

```text
1. Explain which files will change and why.
2. Keep changes small.
3. Preserve the agreed architecture.
4. Run relevant checks if possible.
5. Summarize what changed.
```

## 9. Decision Log

### 2026-07-17: Project Name

Decision:

```text
Use geronimo as the repository and project name.
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

## 10. Open Questions

Questions to resolve later:

- Which RSS source should be implemented first?
- Should the package name be `geronimo` or a more descriptive internal name?
- Should configuration use TOML, YAML, or plain Python initially?
- Should first Siri integration use a local file or FastAPI?
- Which watchlist keywords and tickers should be included first?

## 11. Update Rules

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

## 12. Next Action

Immediate next action:

```text
Finish repository initialization with uv, dependencies, .gitignore, and first commit.
```

After that:

```text
Create the minimal src/geronimo structure and implement the Article domain model.
```
