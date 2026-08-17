from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from market_brief.application.services.generate_briefing import (
    GenerateBriefingService,
)
from market_brief.domain.models.article import Article
from market_brief.domain.models.briefing import Briefing, BriefingItem


class FakeRepository:
    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles
        self.requested_limit: int | None = None

    def get_latest(self, limit: int) -> list[Article]:
        self.requested_limit = limit
        return self.articles


def test_execute_passes_limit_and_returns_briefing_items():
    published_at = datetime(
        2026,
        8,
        17,
        9,
        0,
        tzinfo=ZoneInfo("Asia/Seoul"),
    )
    article = Article(
        title="Market update",
        url="https://example.com/market-update",
        source="Test Source",
        published_at=published_at,
        collected_at=published_at,
    )
    repository = FakeRepository([article])
    service = GenerateBriefingService(repository=repository)

    result = service.execute(limit=3)

    assert repository.requested_limit == 3
    assert result == Briefing(
        items=(
            BriefingItem(
                title="Market update",
                source="Test Source",
                url="https://example.com/market-update",
                timestamp=published_at,
                timestamp_label="Published",
            ),
        )
    )


def test_execute_uses_published_at_and_converts_utc_to_kst():
    article = Article(
        title="Published article",
        url="https://example.com/published",
        source="Test Source",
        published_at=datetime(
            2026,
            8,
            17,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        collected_at=datetime(
            2026,
            8,
            17,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )
    repository = FakeRepository([article])
    service = GenerateBriefingService(repository=repository)

    result = service.execute(limit=1)

    item = result.items[0]
    assert item.timestamp_label == "Published"
    assert item.timestamp.isoformat() == "2026-08-17T18:00:00+09:00"


def test_execute_uses_collected_at_when_published_at_is_missing():
    article = Article(
        title="Collected article",
        url="https://example.com/collected",
        source="Test Source",
        published_at=None,
        collected_at=datetime(
            2026,
            8,
            17,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )
    repository = FakeRepository([article])
    service = GenerateBriefingService(repository=repository)

    result = service.execute(limit=1)

    item = result.items[0]
    assert item.timestamp_label == "Collected"
    assert item.timestamp.isoformat() == "2026-08-17T19:00:00+09:00"


def test_execute_returns_empty_briefing_when_no_articles():
    repository = FakeRepository([])
    service = GenerateBriefingService(repository=repository)

    result = service.execute(limit=10)

    assert result == Briefing(items=())