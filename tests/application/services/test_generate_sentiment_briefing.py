from datetime import datetime, timezone

from market_brief.application.services.generate_sentiment_briefing import (
    GenerateSentimentBriefingService,
)
from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis


class FakeArticleRepository:
    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles
        self.requested_limit: int | None = None

    def get_latest(self, limit: int) -> list[Article]:
        self.requested_limit = limit
        return self.articles


class FakeArticleAnalysisRepository:
    def __init__(
        self,
        analyses_by_article_id: dict[int, list[ArticleAnalysis]],
    ) -> None:
        self.analyses_by_article_id = analyses_by_article_id
        self.requested_article_ids: list[int] = []

    def get_by_article_id(self, article_id: int) -> list[ArticleAnalysis]:
        self.requested_article_ids.append(article_id)
        return self.analyses_by_article_id.get(article_id, [])


def make_article(
    article_id: int,
    *,
    published_at: datetime | None,
    collected_at: datetime,
) -> Article:
    return Article(
        id=article_id,
        title=f"Article {article_id}",
        url=f"https://example.com/{article_id}",
        source="BBC Business",
        published_at=published_at,
        collected_at=collected_at,
    )


def make_analysis(
    *,
    analysis_id: int,
    article_id: int,
    analyzer_version: str,
    analyzed_at: datetime,
    analysis_type: str = "text_sentiment",
    analyzer_name: str = "ProsusAI/finbert",
) -> ArticleAnalysis:
    return ArticleAnalysis(
        id=analysis_id,
        article_id=article_id,
        analysis_type=analysis_type,
        analyzer_name=analyzer_name,
        analyzer_version=analyzer_version,
        analyzed_at=analyzed_at,
        text_sentiment="neutral",
        positive_score=0.1,
        neutral_score=0.8,
        negative_score=0.1,
        confidence=0.8,
    )


def build_service(
    article_repository: FakeArticleRepository,
    analysis_repository: FakeArticleAnalysisRepository,
) -> GenerateSentimentBriefingService:
    return GenerateSentimentBriefingService(
        article_repository=article_repository,
        analysis_repository=analysis_repository,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
    )


def test_execute_selects_latest_exact_model_analysis_deterministically():
    article = make_article(
        1,
        published_at=datetime(2026, 8, 30, 1, 0, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 30, 2, 0, tzinfo=timezone.utc),
    )
    older = make_analysis(
        analysis_id=1,
        article_id=1,
        analyzer_version="revision-v1",
        analyzed_at=datetime(2026, 8, 30, 3, 0, tzinfo=timezone.utc),
    )
    latest = make_analysis(
        analysis_id=2,
        article_id=1,
        analyzer_version="revision-v1",
        analyzed_at=datetime(2026, 8, 30, 4, 0, tzinfo=timezone.utc),
    )
    latest_saved_later = make_analysis(
        analysis_id=3,
        article_id=1,
        analyzer_version="revision-v1",
        analyzed_at=latest.analyzed_at,
    )
    different_version = make_analysis(
        analysis_id=4,
        article_id=1,
        analyzer_version="revision-v2",
        analyzed_at=datetime(2026, 8, 30, 5, 0, tzinfo=timezone.utc),
    )
    different_analyzer = make_analysis(
        analysis_id=5,
        article_id=1,
        analyzer_version="revision-v1",
        analyzed_at=datetime(2026, 8, 30, 6, 0, tzinfo=timezone.utc),
        analyzer_name="another-analyzer",
    )
    different_type = make_analysis(
        analysis_id=6,
        article_id=1,
        analyzer_version="revision-v1",
        analyzed_at=datetime(2026, 8, 30, 7, 0, tzinfo=timezone.utc),
        analysis_type="another-analysis",
    )
    article_repository = FakeArticleRepository([article])
    analysis_repository = FakeArticleAnalysisRepository(
        {
            1: [
                different_type,
                older,
                different_version,
                latest_saved_later,
                different_analyzer,
                latest,
            ],
        }
    )
    service = build_service(article_repository, analysis_repository)

    result = service.execute(limit=10)

    assert article_repository.requested_limit == 10
    assert analysis_repository.requested_article_ids == [1]
    assert result.analysis_type == "text_sentiment"
    assert result.analyzer_name == "ProsusAI/finbert"
    assert result.analyzer_version == "revision-v1"
    assert result.items[0].analysis == latest_saved_later


def test_execute_marks_article_missing_when_selected_model_has_no_analysis():
    article = make_article(
        2,
        published_at=None,
        collected_at=datetime(2026, 8, 29, 9, 0, tzinfo=timezone.utc),
    )
    different_version = make_analysis(
        analysis_id=5,
        article_id=2,
        analyzer_version="revision-v2",
        analyzed_at=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )
    article_repository = FakeArticleRepository([article])
    analysis_repository = FakeArticleAnalysisRepository(
        {2: [different_version]}
    )
    service = build_service(article_repository, analysis_repository)

    result = service.execute(limit=1)

    assert result.items[0].analysis is None


def test_execute_preserves_article_order_and_converts_timestamps_to_kst():
    first = make_article(
        1,
        published_at=datetime(2026, 8, 30, 1, 0, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 30, 2, 0, tzinfo=timezone.utc),
    )
    second = make_article(
        2,
        published_at=None,
        collected_at=datetime(2026, 8, 29, 9, 0, tzinfo=timezone.utc),
    )
    article_repository = FakeArticleRepository([first, second])
    analysis_repository = FakeArticleAnalysisRepository({})
    service = build_service(article_repository, analysis_repository)

    result = service.execute(limit=2)

    assert [item.article_id for item in result.items] == [1, 2]
    assert result.items[0].timestamp_label == "Published"
    assert result.items[0].timestamp.isoformat() == "2026-08-30T10:00:00+09:00"
    assert result.items[1].timestamp_label == "Collected"
    assert result.items[1].timestamp.isoformat() == "2026-08-29T18:00:00+09:00"


def test_execute_returns_empty_briefing_without_analysis_queries():
    article_repository = FakeArticleRepository([])
    analysis_repository = FakeArticleAnalysisRepository({})
    service = build_service(article_repository, analysis_repository)

    result = service.execute(limit=10)

    assert result.items == ()
    assert analysis_repository.requested_article_ids == []
