from datetime import datetime, timezone

from market_brief.domain.models.article import Article
from market_brief.infrastructure.repositories.sqlite_repository import (
    SQLiteArticleRepository,
)


def test_save_new_prevents_duplicates(tmp_path):
    db_path = tmp_path / "test.db"
    repository = SQLiteArticleRepository(db_path)

    article = Article(
        title="Test article",
        url="https://example.com/article/1",
        source="Test",
        published_at=None,
        collected_at=datetime.now(timezone.utc),
        source_article_id="article-1",
        canonical_url="https://example.com/article/1",
    )

    first_result = repository.save_new([article])
    second_result = repository.save_new([article])

    assert first_result == [article]
    assert second_result == []


def test_get_latest_returns_articles_in_latest_first_order(tmp_path):
    db_path = tmp_path / "test.db"
    repository = SQLiteArticleRepository(db_path)

    old_article = Article(
        title="Old article",
        url="https://example.com/articles/old",
        source="Test",
        published_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        source_article_id="old",
        canonical_url="https://example.com/articles/old",
    )
    middle_article = Article(
        title="Middle article",
        url="https://example.com/articles/middle",
        source="Test",
        published_at=datetime(2026, 8, 2, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 2, tzinfo=timezone.utc),
        source_article_id="middle",
        canonical_url="https://example.com/articles/middle",
    )
    new_article = Article(
        title="New article",
        url="https://example.com/articles/new",
        source="Test",
        published_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
        source_article_id="new",
        canonical_url="https://example.com/articles/new",
    )

    repository.save_new([old_article, new_article, middle_article])

    result = repository.get_latest(2)

    assert result == [new_article, middle_article]


def test_search_keyword_with_apple(tmp_path):
    db_path = tmp_path / "test.db"
    repository = SQLiteArticleRepository(db_path)

    article_with_apple_in_title = Article(
        title="Apple Pay is coming soon",
        url="https://example.com/articles/apple/title",
        source="Test",
        published_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
        source_article_id="title",
        canonical_url="https://example.com/articles/apple/title",
    )

    article_with_apple_in_raw_content = Article(
        title="Quarterly earnings report",
        url="https://example.com/articles/apple/raw-content",
        source="Test",
        published_at=datetime(2026, 8, 2, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 2, tzinfo=timezone.utc),
        raw_content="Apple reported record quarterly earnings.",
        source_article_id="raw-content",
        canonical_url="https://example.com/articles/apple/raw-content",
    )

    article_with_apple_in_cleaned_content = Article(
        title="Technology company update",
        url="https://example.com/articles/apple/cleaned-content",
        source="Test",
        published_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        cleaned_content="Apple announced a new payment feature.",
        source_article_id="cleaned-content",
        canonical_url="https://example.com/articles/apple/cleaned-content",
    )

    unrelated_article = Article(
        title="Oil prices rise",
        url="https://example.com/articles/oil-prices",
        source="Test",
        published_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
        collected_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
        raw_content="Energy markets moved higher during trading.",
        cleaned_content="Oil prices increased.",
        source_article_id="oil-prices",
        canonical_url="https://example.com/articles/oil-prices",
    )

    repository.save_new(
        [
            article_with_apple_in_title,
            article_with_apple_in_raw_content,
            article_with_apple_in_cleaned_content,
            unrelated_article,
        ]
    )

    result = repository.search("Apple")

    assert result == [
        article_with_apple_in_title,
        article_with_apple_in_raw_content,
        article_with_apple_in_cleaned_content,
    ]

    assert repository.search("   ") == []
