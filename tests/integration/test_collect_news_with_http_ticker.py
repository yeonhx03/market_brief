import json
from datetime import datetime, timezone

import httpx
import pytest

from market_brief.application.services.collect_news import CollectNewsService
from market_brief.domain.models.article import Article
from market_brief.infrastructure.repositories.http_article_repository import (
    HttpArticleRepository,
)
from market_brief.infrastructure.repositories.http_auth import (
    WRITE_API_KEY_HEADER,
)


class FakeCollector:
    def __init__(self, article: Article) -> None:
        self.article = article

    async def fetch(self) -> list[Article]:
        return [self.article]


@pytest.mark.asyncio
async def test_collect_saves_article_then_links_explicit_ticker():
    request_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        request_paths.append(request.url.path)
        assert request.headers[WRITE_API_KEY_HEADER] == "test-secret"

        if request.url.path == "/api/articles":
            payload = json.loads(request.content)
            return httpx.Response(201, json={"id": 42, **payload})

        assert json.loads(request.content) == {"ticker": "AAPL"}
        return httpx.Response(204)

    article = Article(
        source="Example News",
        title="Apple market update",
        url="https://example.com/apple-market-update",
        published_at=None,
        collected_at=datetime(2026, 8, 31, tzinfo=timezone.utc),
    )

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        service = CollectNewsService(
            collector=FakeCollector(article),
            repository=HttpArticleRepository(
                base_url="http://api.test",
                client=client,
                api_key="test-secret",
                ticker="AAPL",
            ),
        )

        saved_articles = await service.execute()

    assert [saved.id for saved in saved_articles] == [42]
    assert request_paths == [
        "/api/articles",
        "/api/articles/42/tickers",
    ]
