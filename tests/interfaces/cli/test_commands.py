import argparse
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from market_brief.domain.models.article import Article
from market_brief.domain.models.briefing import Briefing, BriefingItem
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


class FakeGenerateBriefingService:
    def __init__(self, briefing: Briefing) -> None:
        self.briefing = briefing
        self.requested_limit: int | None = None

    def execute(self, limit: int) -> Briefing:
        self.requested_limit = limit
        return self.briefing


class FakeAnalyzeArticleService:
    def __init__(self, results: list[object | None]) -> None:
        self.results = results
        self.received_articles: list[Article] = []

    def execute(self, article: Article) -> object | None:
        self.received_articles.append(article)
        return self.results[len(self.received_articles) - 1]


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


def test_main_builds_briefing_service_and_prints_items(
    monkeypatch,
    capsys,
):
    briefing = Briefing(
        items=(
            BriefingItem(
                title="Market update",
                source="Test Source",
                url="https://example.com/market-update",
                timestamp=datetime(
                    2026,
                    8,
                    17,
                    18,
                    0,
                    tzinfo=ZoneInfo("Asia/Seoul"),
                ),
                timestamp_label="Published",
            ),
        )
    )
    fake_service = FakeGenerateBriefingService(briefing)
    factory_arguments = {}

    def fake_build_generate_briefing_service(db_path):
        factory_arguments["db_path"] = db_path
        return fake_service

    monkeypatch.setattr(
        commands,
        "build_generate_briefing_service",
        fake_build_generate_briefing_service,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "market_brief",
            "briefing",
            "--limit",
            "3",
            "--db-path",
            "test.db",
        ],
    )

    commands.main()

    assert factory_arguments == {
        "db_path": "test.db",
    }
    assert fake_service.requested_limit == 3
    assert capsys.readouterr().out == (
        "1. Market update\n"
        "   Test Source | Published: 2026-08-17T18:00:00+09:00\n"
        "   https://example.com/market-update\n"
    )


def test_parser_accepts_analyze_arguments():
    args = commands.build_parser().parse_args(
        [
            "analyze",
            "--limit",
            "3",
            "--db-path",
            "test.db",
        ]
    )

    assert args.command == "analyze"
    assert args.limit == 3
    assert args.db_path == "test.db"


def test_run_analyze_counts_new_and_existing_analyses(
    monkeypatch,
    capsys,
):
    collected_at = datetime(2026, 8, 17, tzinfo=timezone.utc)
    articles = [
        Article(
            id=1,
            title="New analysis",
            url="https://example.com/new",
            source="Test",
            published_at=None,
            collected_at=collected_at,
        ),
        Article(
            id=2,
            title="Existing analysis",
            url="https://example.com/existing",
            source="Test",
            published_at=None,
            collected_at=collected_at,
        ),
    ]
    article_service = FakeGetLatestArticlesService(articles)
    analysis_service = FakeAnalyzeArticleService([object(), None])
    factory_paths: dict[str, str] = {}

    def fake_build_get_latest_articles_service(db_path):
        factory_paths["articles"] = db_path
        return article_service

    def fake_build_analyze_article_service(db_path):
        factory_paths["analyses"] = db_path
        return analysis_service

    monkeypatch.setattr(
        commands,
        "build_get_latest_articles_service",
        fake_build_get_latest_articles_service,
    )
    monkeypatch.setattr(
        commands,
        "build_analyze_article_service",
        fake_build_analyze_article_service,
    )
    args = argparse.Namespace(
        command="analyze",
        limit=2,
        db_path="test.db",
    )

    commands.run_analyze(args)

    assert factory_paths == {
        "articles": "test.db",
        "analyses": "test.db",
    }
    assert article_service.requested_limit == 2
    assert analysis_service.received_articles == articles
    assert capsys.readouterr().out == (
        "Analyzed 1 articles. Skipped 1 existing analyses.\n"
    )


def test_run_analyze_does_not_build_model_when_no_articles(
    monkeypatch,
    capsys,
):
    article_service = FakeGetLatestArticlesService([])
    monkeypatch.setattr(
        commands,
        "build_get_latest_articles_service",
        lambda db_path: article_service,
    )

    def fail_if_model_is_built(db_path):
        raise AssertionError("empty article list must not build FinBERT")

    monkeypatch.setattr(
        commands,
        "build_analyze_article_service",
        fail_if_model_is_built,
    )
    args = argparse.Namespace(
        command="analyze",
        limit=10,
        db_path="test.db",
    )

    commands.run_analyze(args)

    assert article_service.requested_limit == 10
    assert capsys.readouterr().out == "No articles found.\n"


def test_main_dispatches_analyze_command(monkeypatch):
    received_args: list[argparse.Namespace] = []
    monkeypatch.setattr(
        commands,
        "run_analyze",
        received_args.append,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "market_brief",
            "analyze",
            "--limit",
            "4",
            "--db-path",
            "test.db",
        ],
    )

    commands.main()

    assert len(received_args) == 1
    assert received_args[0].command == "analyze"
    assert received_args[0].limit == 4
    assert received_args[0].db_path == "test.db"
