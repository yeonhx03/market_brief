from dataclasses import replace
from datetime import datetime, timezone

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
    assert calls == ["analyze", "save"]