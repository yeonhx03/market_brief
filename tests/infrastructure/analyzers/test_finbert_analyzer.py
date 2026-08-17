from datetime import datetime, timezone
import pytest

from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.infrastructure.analyzers.finbert_analyzer import (
    FinBERTAnalyzer,
)


def test_analyze_maps_controlled_response_to_article_analysis():
    def fake_classifier(
        text: str,
    ) -> list[dict[str, str | float]]:
        return [
            {"label": "negative", "score": 0.1},
            {"label": "positive", "score": 0.7},
            {"label": "neutral", "score": 0.2},
        ]

    analyzed_at = datetime(
        2026,
        8,
        17,
        6,
        0,
        tzinfo=timezone.utc,
    )

    analyzer = FinBERTAnalyzer(
        classifier=fake_classifier,
        analyzer_name="controlled-finbert",
        analyzer_version="test-v1",
        clock=lambda: analyzed_at,
    )

    article = Article(
        id=42,
        title="Company reports strong earnings",
        url="https://example.com/article",
        source="Test",
        published_at=analyzed_at,
        collected_at=analyzed_at,
        raw_content="Revenue and profit increased.",
    )

    result = analyzer.analyze(article)

    assert result == ArticleAnalysis(
        article_id=42,
        analysis_type="text_sentiment",
        analyzer_name="controlled-finbert",
        analyzer_version="test-v1",
        analyzed_at=analyzed_at,
        text_sentiment="positive",
        positive_score=0.7,
        neutral_score=0.2,
        negative_score=0.1,
        confidence=0.7,
    )


def test_analyze_rejects_article_without_id():
    def fake_classifier(
        text: str,
    ) -> list[dict[str, str | float]]:
        raise AssertionError("classifier must not be called")

    analyzer = FinBERTAnalyzer(
        classifier=fake_classifier,
        analyzer_name="controlled-finbert",
        analyzer_version="test-v1",
        clock=lambda: datetime.now(timezone.utc),
    )

    article = Article(
        title="Unsaved article",
        url="https://example.com/unsaved",
        source="Test",
        published_at=None,
        collected_at=datetime.now(timezone.utc),
    )

    with pytest.raises(
        ValueError,
        match="article must be persisted before analysis",
    ):
        analyzer.analyze(article)


def test_analyze_rejects_response_with_missing_label():
    def fake_classifier(
        text: str,
    ) -> list[dict[str, str | float]]:
        return [
            {"label": "positive", "score": 0.8},
            {"label": "negative", "score": 0.2},
        ]

    analyzed_at = datetime(
        2026,
        8,
        17,
        6,
        0,
        tzinfo=timezone.utc,
    )

    analyzer = FinBERTAnalyzer(
        classifier=fake_classifier,
        analyzer_name="controlled-finbert",
        analyzer_version="test-v1",
        clock=lambda: analyzed_at,
    )

    article = Article(
        id=42,
        title="Company reports earnings",
        url="https://example.com/article",
        source="Test",
        published_at=analyzed_at,
        collected_at=analyzed_at,
    )

    with pytest.raises(
        ValueError,
        match="classifier must return exactly three sentiment labels",
    ):
        analyzer.analyze(article)


def test_analyze_rejects_score_outside_probability_range():
    def fake_classifier(
        text: str,
    ) -> list[dict[str, str | float]]:
        return [
            {"label": "positive", "score": 1.1},
            {"label": "neutral", "score": 0.0},
            {"label": "negative", "score": -0.1},
        ]

    analyzed_at = datetime(
        2026,
        8,
        17,
        6,
        0,
        tzinfo=timezone.utc,
    )

    analyzer = FinBERTAnalyzer(
        classifier=fake_classifier,
        analyzer_name="controlled-finbert",
        analyzer_version="test-v1",
        clock=lambda: analyzed_at,
    )

    article = Article(
        id=42,
        title="Company reports earnings",
        url="https://example.com/article",
        source="Test",
        published_at=analyzed_at,
        collected_at=analyzed_at,
    )

    with pytest.raises(
        ValueError,
        match="sentiment scores must be between 0 and 1",
    ):
        analyzer.analyze(article)


def test_analyze_rejects_scores_that_do_not_sum_to_one():
    def fake_classifier(
        text: str,
    ) -> list[dict[str, str | float]]:
        return [
            {"label": "positive", "score": 0.6},
            {"label": "neutral", "score": 0.4},
            {"label": "negative", "score": 0.2},
        ]

    analyzed_at = datetime(
        2026,
        8,
        17,
        6,
        0,
        tzinfo=timezone.utc,
    )

    analyzer = FinBERTAnalyzer(
        classifier=fake_classifier,
        analyzer_name="controlled-finbert",
        analyzer_version="test-v1",
        clock=lambda: analyzed_at,
    )

    article = Article(
        id=42,
        title="Company reports earnings",
        url="https://example.com/article",
        source="Test",
        published_at=analyzed_at,
        collected_at=analyzed_at,
    )

    with pytest.raises(
        ValueError,
        match="sentiment scores must sum to 1",
    ):
        analyzer.analyze(article)