from datetime import timezone

from market_brief.application.services.analyze_article import (
    AnalyzeArticleService,
)
from market_brief.application.services.generate_sentiment_briefing import (
    GenerateSentimentBriefingService,
)
from market_brief.bootstrap import (
    build_analyze_article_service,
    build_generate_sentiment_briefing_service,
    build_http_analyze_article_service,
    build_http_briefing_repository,
    build_http_collect_news_service,
    build_http_generate_sentiment_briefing_service,
    build_http_get_latest_articles_service,
)
from market_brief.infrastructure.analyzers.finbert_analyzer import (
    FinBERTAnalyzer,
)
from market_brief.infrastructure.analyzers.transformers_finbert_classifier import (
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_REVISION,
    TransformersFinBERTClassifier,
)
from market_brief.infrastructure.repositories.sqlite_article_analysis_repository import (
    SQLiteArticleAnalysisRepository,
)
from market_brief.infrastructure.repositories.sqlite_repository import (
    SQLiteArticleRepository,
)
from market_brief.infrastructure.repositories.http_article_repository import (
    HttpArticleRepository,
)
from market_brief.infrastructure.repositories.http_article_analysis_repository import (
    HttpArticleAnalysisRepository,
)
from market_brief.infrastructure.repositories.http_briefing_repository import (
    HttpBriefingRepository,
)
from market_brief.infrastructure.repositories.http_auth import (
    WRITE_API_KEY_HEADER,
)


def test_build_analyze_article_service_wires_real_adapter_types(
    tmp_path,
    monkeypatch,
):
    loader_calls: list[None] = []

    def fake_classifier(text: str):
        raise AssertionError(f"classifier should not run while wiring: {text}")

    def fake_from_pretrained(cls):
        loader_calls.append(None)
        return fake_classifier

    monkeypatch.setattr(
        TransformersFinBERTClassifier,
        "from_pretrained",
        classmethod(fake_from_pretrained),
    )
    db_path = tmp_path / "market_brief.db"

    service = build_analyze_article_service(db_path)

    assert loader_calls == [None]
    assert isinstance(service, AnalyzeArticleService)
    assert isinstance(service.analyzer, FinBERTAnalyzer)
    assert service.analyzer.classifier is fake_classifier
    assert service.analyzer.analyzer_name == DEFAULT_MODEL_NAME
    assert service.analyzer.analyzer_version == DEFAULT_MODEL_REVISION
    assert service.analyzer.clock().tzinfo == timezone.utc
    assert isinstance(service.repository, SQLiteArticleAnalysisRepository)
    assert service.repository.db_path == db_path


def test_build_generate_sentiment_briefing_service_wires_repositories_only(
    tmp_path,
    monkeypatch,
):
    def fail_if_model_is_loaded(cls, *args, **kwargs):
        raise AssertionError("sentiment briefing must not load FinBERT")

    monkeypatch.setattr(
        TransformersFinBERTClassifier,
        "from_pretrained",
        classmethod(fail_if_model_is_loaded),
    )
    db_path = tmp_path / "market_brief.db"

    service = build_generate_sentiment_briefing_service(db_path)

    assert isinstance(service, GenerateSentimentBriefingService)
    assert isinstance(service.article_repository, SQLiteArticleRepository)
    assert service.article_repository.db_path == db_path
    assert isinstance(
        service.analysis_repository,
        SQLiteArticleAnalysisRepository,
    )
    assert service.analysis_repository.db_path == db_path
    assert service.analysis_type == "text_sentiment"
    assert service.analyzer_name == DEFAULT_MODEL_NAME
    assert service.analyzer_version == DEFAULT_MODEL_REVISION


def test_build_http_latest_service_selects_only_http_repository(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("WRITE_API_KEY", "test-secret")
    db_path = tmp_path / "must-not-exist.db"

    service = build_http_get_latest_articles_service("http://api.test/")

    assert isinstance(service.repository, HttpArticleRepository)
    assert service.repository.base_url == "http://api.test"
    assert service.repository.write_headers == {
        WRITE_API_KEY_HEADER: "test-secret"
    }
    assert not db_path.exists()
    service.repository.client.close()


def test_build_http_sentiment_briefing_wires_both_http_repositories(
    monkeypatch,
):
    monkeypatch.setenv("WRITE_API_KEY", "test-secret")
    service = build_http_generate_sentiment_briefing_service(
        "http://api.test"
    )

    assert isinstance(service.article_repository, HttpArticleRepository)
    assert isinstance(
        service.analysis_repository,
        HttpArticleAnalysisRepository,
    )
    assert service.article_repository.base_url == "http://api.test"
    assert service.analysis_repository.base_url == "http://api.test"
    assert service.article_repository.write_headers == {
        WRITE_API_KEY_HEADER: "test-secret"
    }
    assert service.analysis_repository.write_headers == {
        WRITE_API_KEY_HEADER: "test-secret"
    }
    service.article_repository.client.close()
    service.analysis_repository.client.close()


def test_build_http_briefing_repository_uses_normalized_api_url(monkeypatch):
    monkeypatch.setenv("WRITE_API_KEY", "test-secret")
    repository = build_http_briefing_repository("http://api.test/")

    assert isinstance(repository, HttpBriefingRepository)
    assert repository.base_url == "http://api.test"
    assert repository.write_headers == {
        WRITE_API_KEY_HEADER: "test-secret"
    }
    repository.client.close()


def test_build_http_collect_service_propagates_write_api_key(monkeypatch):
    monkeypatch.setenv("WRITE_API_KEY", "test-secret")

    service = build_http_collect_news_service(
        feed_url="https://example.com/feed.xml",
        source="Example News",
        api_url="http://api.test",
    )

    assert service.repository.write_headers == {
        WRITE_API_KEY_HEADER: "test-secret"
    }
    service.repository.client.close()


def test_build_http_analyze_service_propagates_write_api_key(
    monkeypatch,
):
    monkeypatch.setenv("WRITE_API_KEY", "test-secret")
    monkeypatch.setattr(
        TransformersFinBERTClassifier,
        "from_pretrained",
        classmethod(lambda cls: lambda text: None),
    )

    service = build_http_analyze_article_service("http://api.test")

    assert service.repository.write_headers == {
        WRITE_API_KEY_HEADER: "test-secret"
    }
    service.repository.client.close()
