# Market Brief Architecture

## 1. System Goal

`market_brief` collects financial news, analyzes the stored articles, and produces readable
briefings. It is the news-intelligence part of a larger personal trading ecosystem.

It does not own:

- BUY/SELL decisions
- position sizing or portfolio risk
- brokerage authentication or order execution
- price-impact prediction in the current scope

Human-readable briefings and future machine-readable news indicators must remain separate
outputs. FinBERT sentiment is metadata about financial language, not a trading instruction.

## 2. Target System

```text
RSS/Atom sources
      |
      v
Python market_brief
  - news collection
  - FinBERT inference
  - briefing generation
      |
      | HTTP/JSON
      v
Spring Boot market_brief_api
  - REST API
  - request validation
  - duplicate handling
  - transactions
  - PostgreSQL ownership
      |
      v
PostgreSQL

React web (first public client) ---- HTTPS ----> Spring Boot API
macOS/iOS Swift apps (later) ------- HTTPS ----> Spring Boot API
```

The Python and Spring applications communicate through an explicit HTTP/JSON contract. Python
does not receive PostgreSQL credentials and does not depend on Spring's internal JPA entities or
database schema.

Spring is an intentional learning and portfolio boundary. Direct database access would be simpler
for one process, but the API demonstrates a real cross-language backend integration and becomes a
stable interface for the React web, future Swift clients, and other programs.

## 3. Python Internal Architecture

The Python application remains a modular monolith using Ports and Adapters.

```text
Domain
  ^
Application services and ports
  ^
Infrastructure adapters / Interfaces / Bootstrap
```

Responsibilities:

- `domain`: `Article`, `ArticleAnalysis`, `Briefing`, and future pure models
- `application/ports`: collector, article repository, analysis repository, analyzer contracts
- `application/services`: collect, query, analyze, and briefing use cases
- `infrastructure`: RSS, SQLite, HTTP repositories, and FinBERT runtime adapters
- `interfaces`: CLI and future external entry points
- `bootstrap.py`: concrete dependency construction only

Dependency rules:

1. Domain imports no infrastructure or interface code.
2. Application services import domain models and application ports.
3. Infrastructure implements ports and may import domain models.
4. Interfaces call application services.
5. Bootstrap wires concrete implementations.

## 4. Persistence Modes

### Local/offline mode

```text
Python -> SQLiteArticleRepository
       -> SQLiteArticleAnalysisRepository
```

SQLite remains available for learning, tests, local development, and offline operation.

### Integrated mode

```text
Python -> HttpArticleRepository         -> Spring Boot -> PostgreSQL
       -> HttpArticleAnalysisRepository -> Spring Boot -> PostgreSQL
```

Each run selects one persistence path. The application must not silently write the same operation
to SQLite and PostgreSQL.

## 5. Collection And Analysis Lifecycle

The integrated lifecycle stores the raw article before inference.

```text
1. Python fetches an RSS batch.
2. Python sends each article to Spring.
3. Spring stores or identifies the duplicate and returns its ID.
4. Python analyzes only newly stored articles.
5. Python sends complete ArticleAnalysis results to Spring.
6. Python generates a briefing from stored article and analysis data.
7. Python sends the generated briefing to Spring for Swift clients.
```

Storing the article first prevents model failure from losing collected news. It also gives every
analysis a stable article ID and allows an unfinished analysis to be retried.

The intended initial Spring API surface is:

```text
POST /api/articles
GET  /api/articles/latest?limit=10
POST /api/articles/{articleId}/analyses
GET  /api/articles/{articleId}/analyses
POST /api/briefings
GET  /api/briefings/latest
```

These request and response schemas are implemented in the Spring repository and remain the shared
contract for Python, React, and future Swift clients.

## 6. Analysis Boundaries

`ArticleAnalysis` stores one complete article-level sentiment result:

- internal article ID
- analysis type
- analyzer name and version
- analyzed timestamp
- positive, neutral, and negative probabilities
- selected text-sentiment label
- confidence

The same article may be re-analyzed with a different model version. The same article and model
version should not be inserted repeatedly by scheduled runs.

The urgent FinBERT slice does not include:

- watchlist or automatic entity matching
- LLM summaries
- entity-specific stock impact
- price direction prediction
- trading signals

The first real FinBERT input should be the English headline. RSS summaries may contain HTML and
long text, so title-plus-content analysis must wait for explicit cleaning and input-length rules.

## 7. Briefing Boundaries

The existing `Briefing` is deterministic and continues to work without FinBERT. It contains recent
article titles, sources, timestamps, and links.

Sentiment output uses the separate `SentimentBriefing` model and
`GenerateSentimentBriefingService`; the existing deterministic briefing does not depend on model
availability. The service reads stored articles and analyses through repository ports and selects
an exact analysis type, analyzer name, and analyzer version. Missing selected-version analyses are
represented explicitly instead of being treated as neutral.

The `sentiment-briefing` CLI produces deterministic text or persistence-ready JSON. The JSON keeps
the stored probabilities, selected model identity, per-article analysis status, and summary counts.
It omits a live generation timestamp so the same stored data produces the same payload. Spring may
assign persistence metadata when it accepts a future briefing request. Neither output is described
as expected stock-price direction or a trading signal.

Because the scheduled Python process exits after work, a briefing intended for Swift clients must
be stored through Spring and exposed through `GET /api/briefings/latest`.

## 8. Runtime And Deployment

Development environments:

- Intel Mac: normal Python work, Spring Boot, PostgreSQL integration, Xcode, Swift/SwiftUI
- Windows x86-64: temporary real FinBERT/PyTorch implementation and CPU benchmark

Production target:

```text
Static web host
  - React + TypeScript + Vite production build

Application and data services
  - Spring Boot: always running
  - PostgreSQL: managed persistent database
  - Python collection/FinBERT job: scheduled, runs, then exits
```

The React application is read-only in the first public release. It calls Spring over HTTPS and
never receives database credentials or the Python worker's write credential. Public read APIs and
protected server-to-server write APIs are separate security concerns; CORS does not replace
authentication.

Source code is shared through Git. Virtual environments, downloaded models, caches, databases,
secrets, Java build output, and Swift build output are recreated or configured per operating
system and must not be committed.

Server sizing is decided only after the Windows FinBERT benchmark records model size, load time,
peak memory, and processing time for representative batches.

## 9. Future Order

```text
1. Real article-level FinBERT on Windows (complete)
2. Sentiment briefing completion on Windows (complete)
3. Return to Intel Mac
4. Spring Boot REST API, JPA, and Flyway (implemented locally)
5. Python article and analysis HTTP repository adapters (implemented locally)
6. Briefing HTTP persistence and live PostgreSQL end-to-end verification
7. React + TypeScript + Vite first public client
8. Web, Spring, PostgreSQL deployment and Python scheduling
9. macOS and iOS SwiftUI clients
10. Post-MVP expansion review
```
