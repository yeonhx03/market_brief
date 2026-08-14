from datetime import datetime, timezone

import pytest

from market_brief.application.services.collect_news import CollectNewsService
from market_brief.domain.models.article import Article


class FakeCollector:
    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles

    async def fetch(self) -> list[Article]:
        return self.articles


class FakeRepository:
    def __init__(self, saved_articles: list[Article]) -> None:
        self.saved_articles = saved_articles
        self.received_articles: list[Article] | None = None

    def save_new(self, articles: list[Article]) -> list[Article]:
        self.received_articles = articles
        return self.saved_articles


@pytest.mark.asyncio
async def test_execute_saves_collected_articles_and_returns_saved_articles():
    article = Article(
        title="Test article",
        url="https://example.com/article",
        source="Test",
        published_at=None,
        collected_at=datetime.now(timezone.utc),
    )

    collector = FakeCollector([article])
    repository = FakeRepository([])
    service = CollectNewsService(
        collector=collector,
        repository=repository,
    )

    result = await service.execute()

    assert repository.received_articles == [article]
    assert result == []