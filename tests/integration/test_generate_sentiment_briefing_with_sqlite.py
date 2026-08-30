from datetime import datetime, timezone

from market_brief.application.services.generate_sentiment_briefing import (
    GenerateSentimentBriefingService,
)
from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.infrastructure.repositories.sqlite_article_analysis_repository import (
    SQLiteArticleAnalysisRepository,
)
from market_brief.infrastructure.repositories.sqlite_repository import (
    SQLiteArticleRepository,
)


def test_generate_sentiment_briefing_reads_stored_sqlite_analyses(tmp_path):
    db_path = tmp_path / "market_brief.db"
    article_repository = SQLiteArticleRepository(db_path)
    analysis_repository = SQLiteArticleAnalysisRepository(db_path)
    older_article, latest_article = article_repository.save_new(
        [
            Article(
                title="Older article",
                url="https://example.com/older",
                source="BBC Business",
                published_at=datetime(
                    2026,
                    8,
                    29,
                    8,
                    0,
                    tzinfo=timezone.utc,
                ),
                collected_at=datetime(
                    2026,
                    8,
                    29,
                    9,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            Article(
                title="Latest article",
                url="https://example.com/latest",
                source="BBC Technology",
                published_at=datetime(
                    2026,
                    8,
                    30,
                    8,
                    0,
                    tzinfo=timezone.utc,
                ),
                collected_at=datetime(
                    2026,
                    8,
                    30,
                    9,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ]
    )

    assert older_article.id is not None
    assert latest_article.id is not None

    stored_analysis = analysis_repository.save(
        ArticleAnalysis(
            article_id=latest_article.id,
            analysis_type="text_sentiment",
            analyzer_name="ProsusAI/finbert",
            analyzer_version="revision-v1",
            analyzed_at=datetime(
                2026,
                8,
                30,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            text_sentiment="negative",
            positive_score=0.05,
            neutral_score=0.15,
            negative_score=0.80,
            confidence=0.80,
        )
    )
    analysis_repository.save(
        ArticleAnalysis(
            article_id=older_article.id,
            analysis_type="text_sentiment",
            analyzer_name="ProsusAI/finbert",
            analyzer_version="revision-v2",
            analyzed_at=datetime(
                2026,
                8,
                30,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            text_sentiment="positive",
            positive_score=0.80,
            neutral_score=0.15,
            negative_score=0.05,
            confidence=0.80,
        )
    )
    service = GenerateSentimentBriefingService(
        article_repository=article_repository,
        analysis_repository=analysis_repository,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
    )

    result = service.execute(limit=2)

    assert [item.article_id for item in result.items] == [
        latest_article.id,
        older_article.id,
    ]
    assert result.items[0].analysis == stored_analysis
    assert result.items[1].analysis is None
    assert len(
        analysis_repository.get_by_article_id(latest_article.id)
    ) == 1
    assert len(
        analysis_repository.get_by_article_id(older_article.id)
    ) == 1
