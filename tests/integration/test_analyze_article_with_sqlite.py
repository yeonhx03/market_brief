from datetime import datetime, timezone

from market_brief.application.services.analyze_article import (
    AnalyzeArticleService,
)
from market_brief.domain.models.article import Article
from market_brief.infrastructure.analyzers.finbert_analyzer import (
    FinBERTAnalyzer,
)
from market_brief.infrastructure.repositories.sqlite_article_analysis_repository import (
    SQLiteArticleAnalysisRepository,
)
from market_brief.infrastructure.repositories.sqlite_repository import (
    SQLiteArticleRepository,
)


def test_analyze_persisted_article_and_store_result_in_sqlite(
    tmp_path,
):
    db_path = tmp_path / "test.db"

    article_repository = SQLiteArticleRepository(db_path)
    analysis_repository = SQLiteArticleAnalysisRepository(db_path)

    collected_at = datetime(
        2026,
        8,
        17,
        6,
        0,
        tzinfo=timezone.utc,
    )

    article = Article(
        title="Company reports strong earnings",
        url="https://example.com/earnings",
        source="Test",
        published_at=None,
        collected_at=collected_at,
        raw_content="Revenue and profit increased.",
    )

    saved_article = article_repository.save_new([article])[0]

    assert saved_article.id is not None

    def fake_classifier(
        text: str,
    ) -> list[dict[str, str | float]]:
        return [
            {"label": "positive", "score": 0.7},
            {"label": "neutral", "score": 0.2},
            {"label": "negative", "score": 0.1},
        ]

    analyzer = FinBERTAnalyzer(
        classifier=fake_classifier,
        analyzer_name="controlled-finbert",
        analyzer_version="test-v1",
        clock=lambda: collected_at,
    )

    service = AnalyzeArticleService(
        analyzer=analyzer,
        repository=analysis_repository,
    )

    saved_analysis = service.execute(saved_article)

    assert saved_analysis.id is not None
    assert saved_analysis.article_id == saved_article.id

    assert analysis_repository.get_by_article_id(
        saved_article.id
    ) == [saved_analysis]