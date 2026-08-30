from dataclasses import replace
from datetime import datetime, timezone

import pytest

from market_brief.application.services.analyze_article import (
    AnalyzeArticleService,
)
from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis


def test_execute_analyzes_article_then_saves_result():
    calls: list[str] = []

    article = Article(
        id=42,
        title="Company reports strong earnings",
        url="https://example.com/article",
        source="Test",
        published_at=None,
        collected_at=datetime(
            2026,
            8,
            17,
            tzinfo=timezone.utc,
        ),
    )

    analysis = ArticleAnalysis(
        article_id=42,
        analysis_type="text_sentiment",
        analyzer_name="controlled-finbert",
        analyzer_version="test-v1",
        analyzed_at=datetime(
            2026,
            8,
            17,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        text_sentiment="positive",
        positive_score=0.7,
        neutral_score=0.2,
        negative_score=0.1,
        confidence=0.7,
    )
    saved_analysis = replace(analysis, id=7)

    class FakeAnalyzer:
        analysis_type = "text_sentiment"
        analyzer_name = "controlled-finbert"
        analyzer_version = "test-v1"

        def analyze(
            self,
            received_article: Article,
        ) -> ArticleAnalysis:
            calls.append("analyze")
            assert received_article == article
            return analysis

    class FakeRepository:
        def save(
            self,
            received_analysis: ArticleAnalysis,
        ) -> ArticleAnalysis:
            calls.append("save")
            assert received_analysis == analysis
            return saved_analysis

        def has_analysis(
            self,
            article_id: int,
            analysis_type: str,
            analyzer_name: str,
            analyzer_version: str,
        ) -> bool:
            calls.append("has_analysis")
            assert article_id == 42
            assert analysis_type == "text_sentiment"
            assert analyzer_name == "controlled-finbert"
            assert analyzer_version == "test-v1"
            return False

        def get_by_article_id(
            self,
            article_id: int,
        ) -> list[ArticleAnalysis]:
            return []

    service = AnalyzeArticleService(
        analyzer=FakeAnalyzer(),
        repository=FakeRepository(),
    )

    result = service.execute(article)

    assert result == saved_analysis
    assert calls == ["has_analysis", "analyze", "save"]


def test_execute_skips_existing_analysis_without_running_analyzer():
    calls: list[str] = []
    article = Article(
        id=42,
        title="Previously analyzed article",
        url="https://example.com/article",
        source="Test",
        published_at=None,
        collected_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
    )

    class FakeAnalyzer:
        analysis_type = "text_sentiment"
        analyzer_name = "controlled-finbert"
        analyzer_version = "test-v1"

        def analyze(self, received_article: Article) -> ArticleAnalysis:
            raise AssertionError("existing analysis must skip inference")

    class FakeRepository:
        def has_analysis(
            self,
            article_id: int,
            analysis_type: str,
            analyzer_name: str,
            analyzer_version: str,
        ) -> bool:
            calls.append("has_analysis")
            return True

        def save(self, analysis: ArticleAnalysis) -> ArticleAnalysis:
            raise AssertionError("existing analysis must not be saved")

        def get_by_article_id(
            self,
            article_id: int,
        ) -> list[ArticleAnalysis]:
            return []

    service = AnalyzeArticleService(
        analyzer=FakeAnalyzer(),
        repository=FakeRepository(),
    )

    result = service.execute(article)

    assert result is None
    assert calls == ["has_analysis"]


def test_execute_rejects_unpersisted_article_before_repository_lookup():
    article = Article(
        title="Unpersisted article",
        url="https://example.com/unpersisted",
        source="Test",
        published_at=None,
        collected_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
    )

    class FakeAnalyzer:
        analysis_type = "text_sentiment"
        analyzer_name = "controlled-finbert"
        analyzer_version = "test-v1"

        def analyze(self, received_article: Article) -> ArticleAnalysis:
            raise AssertionError("unpersisted article must skip inference")

    class FakeRepository:
        def has_analysis(self, *args, **kwargs) -> bool:
            raise AssertionError("unpersisted article must skip lookup")

        def save(self, analysis: ArticleAnalysis) -> ArticleAnalysis:
            raise AssertionError("unpersisted article must not be saved")

        def get_by_article_id(
            self,
            article_id: int,
        ) -> list[ArticleAnalysis]:
            return []

    service = AnalyzeArticleService(
        analyzer=FakeAnalyzer(),
        repository=FakeRepository(),
    )

    with pytest.raises(
        ValueError,
        match="article must be persisted before analysis",
    ):
        service.execute(article)
