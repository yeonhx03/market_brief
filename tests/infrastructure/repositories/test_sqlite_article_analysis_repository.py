from dataclasses import replace
from datetime import datetime, timezone
import sqlite3
import pytest

from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.infrastructure.repositories.sqlite_article_analysis_repository import (
    SQLiteArticleAnalysisRepository,
)
from market_brief.infrastructure.repositories.sqlite_repository import (
    SQLiteArticleRepository,
)


def test_save_returns_analysis_with_assigned_id_and_restores_it(tmp_path):
    db_path = tmp_path / "test.db"
    article_repository = SQLiteArticleRepository(db_path)
    analysis_repository = SQLiteArticleAnalysisRepository(db_path)

    article = Article(
        title="Apple reports quarterly earnings",
        url="https://example.com/apple-earnings",
        source="Test",
        published_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        source_article_id="apple-earnings",
        canonical_url="https://example.com/apple-earnings",
    )
    saved_article = article_repository.save_new([article])[0]

    assert saved_article.id is not None

    analysis = ArticleAnalysis(
        article_id=saved_article.id,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="v1",
        analyzed_at=datetime(
            2026,
            8,
            17,
            12,
            30,
            tzinfo=timezone.utc,
        ),
        text_sentiment="positive",
        positive_score=0.72,
        neutral_score=0.21,
        negative_score=0.07,
        confidence=0.72,
    )

    saved_analysis = analysis_repository.save(analysis)

    assert saved_analysis.id == 1
    assert replace(saved_analysis, id=None) == analysis
    assert analysis_repository.get_by_article_id(saved_article.id) == [
        saved_analysis
    ]


def test_get_by_article_id_returns_empty_then_newest_first(tmp_path):
    db_path = tmp_path / "test.db"
    article_repository = SQLiteArticleRepository(db_path)
    analysis_repository = SQLiteArticleAnalysisRepository(db_path)

    article = Article(
        title="Apple market update",
        url="https://example.com/apple-update",
        source="Test",
        published_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        source_article_id="apple-update",
        canonical_url="https://example.com/apple-update",
    )
    saved_article = article_repository.save_new([article])[0]

    assert saved_article.id is not None
    assert analysis_repository.get_by_article_id(saved_article.id) == []

    old_analysis = ArticleAnalysis(
        article_id=saved_article.id,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="v1",
        analyzed_at=datetime(
            2026,
            8,
            17,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        text_sentiment="neutral",
        positive_score=0.20,
        neutral_score=0.60,
        negative_score=0.20,
        confidence=0.60,
    )
    latest_analysis = replace(
        old_analysis,
        analyzed_at=datetime(
            2026,
            8,
            17,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        text_sentiment="positive",
        positive_score=0.70,
        neutral_score=0.20,
        negative_score=0.10,
        confidence=0.70,
    )
    latest_saved_later = replace(
        latest_analysis,
        text_sentiment="negative",
        positive_score=0.10,
        neutral_score=0.20,
        negative_score=0.70,
        confidence=0.70,
    )

    saved_old = analysis_repository.save(old_analysis)
    saved_latest = analysis_repository.save(latest_analysis)
    saved_latest_later = analysis_repository.save(latest_saved_later)

    result = analysis_repository.get_by_article_id(saved_article.id)

    assert result == [
        saved_latest_later,
        saved_latest,
        saved_old,
    ]


def test_save_rejects_unknown_article_id(tmp_path):
    db_path = tmp_path / "test.db"

    SQLiteArticleRepository(db_path)
    analysis_repository = SQLiteArticleAnalysisRepository(db_path)

    analysis = ArticleAnalysis(
        article_id=999,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="v1",
        analyzed_at=datetime(
            2026,
            8,
            17,
            12,
            30,
            tzinfo=timezone.utc,
        ),
        text_sentiment="positive",
        positive_score=0.72,
        neutral_score=0.21,
        negative_score=0.07,
        confidence=0.72,
    )

    with pytest.raises(sqlite3.IntegrityError):
        analysis_repository.save(analysis)

    assert analysis_repository.get_by_article_id(999) == []