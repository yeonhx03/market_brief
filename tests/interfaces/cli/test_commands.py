import argparse
import json
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.domain.models.briefing import Briefing, BriefingItem
from market_brief.domain.models.sentiment_briefing import (
    SentimentBriefing,
    SentimentBriefingItem,
)
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


class FakeGenerateSentimentBriefingService:
    def __init__(self, briefing: SentimentBriefing) -> None:
        self.briefing = briefing
        self.requested_limit: int | None = None

    def execute(self, limit: int) -> SentimentBriefing:
        self.requested_limit = limit
        return self.briefing


class FakeBriefingRepository:
    def __init__(self) -> None:
        self.saved_briefings: list[SentimentBriefing] = []

    def save(self, briefing: SentimentBriefing) -> int:
        self.saved_briefings.append(briefing)
        return 31


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


def test_parser_accepts_sentiment_briefing_arguments():
    args = commands.build_parser().parse_args(
        [
            "sentiment-briefing",
            "--limit",
            "3",
            "--db-path",
            "test.db",
        ]
    )

    assert args.command == "sentiment-briefing"
    assert args.limit == 3
    assert args.db_path == "test.db"
    assert args.format == "text"


def test_parser_accepts_sentiment_briefing_json_format():
    args = commands.build_parser().parse_args(
        [
            "sentiment-briefing",
            "--format",
            "json",
        ]
    )

    assert args.command == "sentiment-briefing"
    assert args.format == "json"


def test_run_sentiment_briefing_prints_analyzed_and_missing_items(
    monkeypatch,
    capsys,
):
    timestamp = datetime(
        2026,
        8,
        30,
        10,
        0,
        tzinfo=ZoneInfo("Asia/Seoul"),
    )
    analysis = ArticleAnalysis(
        id=7,
        article_id=1,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        analyzed_at=datetime(2026, 8, 30, 1, 0, tzinfo=timezone.utc),
        text_sentiment="neutral",
        positive_score=0.1,
        neutral_score=0.8,
        negative_score=0.1,
        confidence=0.8,
    )
    briefing = SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(
            SentimentBriefingItem(
                article_id=1,
                title="Analyzed article",
                source="BBC Business",
                url="https://example.com/analyzed",
                timestamp=timestamp,
                timestamp_label="Published",
                analysis=analysis,
            ),
            SentimentBriefingItem(
                article_id=2,
                title="Missing analysis",
                source="BBC Technology",
                url="https://example.com/missing",
                timestamp=timestamp,
                timestamp_label="Collected",
                analysis=None,
            ),
        ),
    )
    fake_service = FakeGenerateSentimentBriefingService(briefing)
    factory_paths: list[str] = []

    def fake_build_generate_sentiment_briefing_service(db_path):
        factory_paths.append(db_path)
        return fake_service

    monkeypatch.setattr(
        commands,
        "build_generate_sentiment_briefing_service",
        fake_build_generate_sentiment_briefing_service,
    )
    args = argparse.Namespace(
        command="sentiment-briefing",
        limit=2,
        db_path="test.db",
        format="text",
    )

    commands.run_sentiment_briefing(args)

    assert factory_paths == ["test.db"]
    assert fake_service.requested_limit == 2
    assert capsys.readouterr().out == (
        "Sentiment Briefing\n"
        "Model: ProsusAI/finbert\n"
        "Revision: revision-v1\n"
        "Note: Sentiment describes headline language, not price direction "
        "or a trading signal.\n"
        "\n"
        "1. Analyzed article\n"
        "   BBC Business | Published: 2026-08-30T10:00:00+09:00\n"
        "   Text sentiment: neutral | Confidence: 80.00%\n"
        "   Probabilities: positive 10.00% | neutral 80.00% | "
        "negative 10.00%\n"
        "   https://example.com/analyzed\n"
        "2. Missing analysis\n"
        "   BBC Technology | Collected: 2026-08-30T10:00:00+09:00\n"
        "   Text sentiment: unavailable\n"
        "   No stored analysis for the selected model revision.\n"
        "   https://example.com/missing\n"
    )


def test_run_sentiment_briefing_prints_no_articles(monkeypatch, capsys):
    briefing = SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(),
    )
    fake_service = FakeGenerateSentimentBriefingService(briefing)
    monkeypatch.setattr(
        commands,
        "build_generate_sentiment_briefing_service",
        lambda db_path: fake_service,
    )
    args = argparse.Namespace(
        command="sentiment-briefing",
        limit=10,
        db_path="test.db",
        format="text",
    )

    commands.run_sentiment_briefing(args)

    assert fake_service.requested_limit == 10
    assert capsys.readouterr().out == "No articles found.\n"


def test_run_sentiment_briefing_prints_json_even_when_empty(
    monkeypatch,
    capsys,
):
    briefing = SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(),
    )
    fake_service = FakeGenerateSentimentBriefingService(briefing)
    serialized_briefings: list[SentimentBriefing] = []

    def fake_serialize_sentiment_briefing(value):
        serialized_briefings.append(value)
        return '{"briefingType":"text_sentiment","items":[]}'

    monkeypatch.setattr(
        commands,
        "build_generate_sentiment_briefing_service",
        lambda db_path: fake_service,
    )
    monkeypatch.setattr(
        commands,
        "serialize_sentiment_briefing",
        fake_serialize_sentiment_briefing,
    )
    args = argparse.Namespace(
        command="sentiment-briefing",
        limit=10,
        db_path="test.db",
        format="json",
    )

    commands.run_sentiment_briefing(args)

    assert serialized_briefings == [briefing]
    assert capsys.readouterr().out == (
        '{"briefingType":"text_sentiment","items":[]}\n'
    )


def test_main_dispatches_sentiment_briefing_command(monkeypatch):
    received_args: list[argparse.Namespace] = []
    monkeypatch.setattr(
        commands,
        "run_sentiment_briefing",
        received_args.append,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "market_brief",
            "sentiment-briefing",
            "--limit",
            "4",
            "--db-path",
            "test.db",
        ],
    )

    commands.main()

    assert len(received_args) == 1
    assert received_args[0].command == "sentiment-briefing"
    assert received_args[0].limit == 4
    assert received_args[0].db_path == "test.db"
    assert received_args[0].format == "text"


def test_parser_accepts_http_persistence_mode():
    args = commands.build_parser().parse_args(
        [
            "latest",
            "--limit",
            "3",
            "--api-url",
            "http://localhost:8080",
        ]
    )

    assert args.command == "latest"
    assert args.limit == 3
    assert args.api_url == "http://localhost:8080"


def test_run_latest_selects_http_builder_without_sqlite(
    monkeypatch,
    capsys,
):
    fake_service = FakeGetLatestArticlesService([])
    received_api_urls: list[str] = []

    def fake_http_builder(api_url):
        received_api_urls.append(api_url)
        return fake_service

    monkeypatch.setattr(
        commands,
        "build_http_get_latest_articles_service",
        fake_http_builder,
    )
    monkeypatch.setattr(
        commands,
        "build_get_latest_articles_service",
        lambda db_path: (_ for _ in ()).throw(
            AssertionError("HTTP mode must not build SQLite")
        ),
    )

    commands.run_latest(
        argparse.Namespace(
            command="latest",
            limit=3,
            db_path="unused.db",
            api_url="http://localhost:8080",
        )
    )

    assert received_api_urls == ["http://localhost:8080"]
    assert capsys.readouterr().out == "No articles found.\n"


def test_run_http_sentiment_briefing_persists_and_keeps_json_output(
    monkeypatch,
    capsys,
):
    briefing = SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(),
    )
    fake_service = FakeGenerateSentimentBriefingService(briefing)
    fake_repository = FakeBriefingRepository()
    service_api_urls: list[str] = []
    repository_api_urls: list[str] = []

    def fake_service_builder(api_url):
        service_api_urls.append(api_url)
        return fake_service

    def fake_repository_builder(api_url):
        repository_api_urls.append(api_url)
        return fake_repository

    monkeypatch.setattr(
        commands,
        "build_http_generate_sentiment_briefing_service",
        fake_service_builder,
    )
    monkeypatch.setattr(
        commands,
        "build_http_briefing_repository",
        fake_repository_builder,
    )
    monkeypatch.setattr(
        commands,
        "build_generate_sentiment_briefing_service",
        lambda db_path: (_ for _ in ()).throw(
            AssertionError("HTTP mode must not build SQLite")
        ),
    )

    commands.run_sentiment_briefing(
        argparse.Namespace(
            command="sentiment-briefing",
            limit=3,
            db_path="unused.db",
            api_url="http://localhost:8080",
            format="json",
        )
    )

    assert service_api_urls == ["http://localhost:8080"]
    assert repository_api_urls == ["http://localhost:8080"]
    assert fake_service.requested_limit == 3
    assert fake_repository.saved_briefings == [briefing]
    output = json.loads(capsys.readouterr().out)
    assert output["briefingType"] == "text_sentiment"
    assert output["items"] == []
