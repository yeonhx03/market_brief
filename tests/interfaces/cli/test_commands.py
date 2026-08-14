import argparse
from datetime import datetime, timezone

from market_brief.domain.models.article import Article
from market_brief.interfaces.cli import commands


class FakeCollectNewsService:
    async def execute(self) -> list[Article]:
        article = Article(
            title="Test article",
            url="https://example.com/article",
            source="Test Source",
            published_at=None,
            collected_at=datetime.now(timezone.utc),
        )
        return [article]


class FakeGetLatestArticlesService:
    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles
        self.requested_limit: int | None = None

    def execute(self, limit: int) -> list[Article]:
        self.requested_limit = limit
        return self.articles


def test_run_collect_builds_service_and_prints_saved_count(
    monkeypatch,
    capsys,
):
    factory_arguments = {}

    def fake_build_collect_news_service(
        feed_url,
        source,
        db_path,
    ):
        factory_arguments["feed_url"] = feed_url
        factory_arguments["source"] = source
        factory_arguments["db_path"] = db_path
        return FakeCollectNewsService()

    monkeypatch.setattr(
        commands,
        "build_collect_news_service",
        fake_build_collect_news_service,
    )

    args = argparse.Namespace(
        command="collect",
        feed_url="https://example.com/feed.xml",
        source="Test Source",
        db_path="test.db",
    )

    commands.run_collect(args)

    assert factory_arguments == {
        "feed_url": "https://example.com/feed.xml",
        "source": "Test Source",
        "db_path": "test.db",
    }
    assert capsys.readouterr().out == "Saved 1 new articles.\n"

def test_run_latest_builds_service_and_prints_articles(
    monkeypatch,
    capsys,
):
    article = Article(
        title="Latest article",
        url="https://example.com/latest",
        source="Test Source",
        published_at=None,
        collected_at=datetime(
            2026,
            8,
            14,
            9,
            0,
            tzinfo=timezone.utc,
        ),
    )
    fake_service = FakeGetLatestArticlesService([article])
    factory_arguments = {}

    def fake_build_get_latest_articles_service(db_path):
        factory_arguments["db_path"] = db_path
        return fake_service

    monkeypatch.setattr(
        commands,
        "build_get_latest_articles_service",
        fake_build_get_latest_articles_service,
    )

    args = argparse.Namespace(
        command="latest",
        limit=3,
        db_path="test.db",
    )

    commands.run_latest(args)

    assert factory_arguments == {
        "db_path": "test.db",
    }
    assert fake_service.requested_limit == 3
    assert capsys.readouterr().out == (
        "1. Latest article\n"
        "   Test Source | 2026-08-14T09:00:00+00:00\n"
        "   https://example.com/latest\n"
    )