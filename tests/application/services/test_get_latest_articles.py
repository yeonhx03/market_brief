from datetime import datetime, timezone

from market_brief.application.services.get_latest_articles import (
    GetLatestArticlesService,
)
from market_brief.domain.models.article import Article


class FakeRepository:
    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles
        self.requested_limit: int | None = None

    def get_latest(self, limit: int) -> list[Article]:
        self.requested_limit = limit
        return self.articles


def test_execute_passes_limit_and_returns_latest_articles():
    article = Article(
        title="Latest article",
        url="https://example.com/latest",
        source="Test",
        published_at=None,
        collected_at=datetime.now(timezone.utc),
    )
    repository = FakeRepository([article])
    service = GetLatestArticlesService(repository=repository)

    result = service.execute(limit=10)

    assert repository.requested_limit == 10
    assert result == [article]