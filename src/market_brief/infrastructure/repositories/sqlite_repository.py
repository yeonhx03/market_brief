import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from market_brief.domain.models.article import Article


class SQLiteArticleRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        connection = sqlite3.connect(self.db_path)

        try:
            connection.execute(
                """
                    CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_article_id TEXT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    canonical_url TEXT,
                    published_at TEXT,
                    collected_at TEXT NOT NULL,
                    raw_content TEXT,
                    cleaned_content TEXT,
                    content_hash TEXT,
                    UNIQUE(source, source_article_id),
                    UNIQUE(canonical_url),
                    UNIQUE(url)
                )
                """
            )
            connection.commit()
        finally:
            connection.close()


    def save_new(self, articles: list[Article]) -> list[Article]:
            saved_articles: list[Article] = []
            connection = sqlite3.connect(self.db_path)
    
            try:
                for article in articles:
                    cursor = connection.execute(
                        """
                        INSERT OR IGNORE INTO articles (
                        source,
                        source_article_id,
                        title,
                        url,
                        canonical_url,
                        published_at,
                        collected_at,
                        raw_content,
                        cleaned_content,
                        content_hash
                    )                    
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article.source,
                        article.source_article_id,
                        article.title,
                        article.url,
                        article.canonical_url,
                        self._datetime_to_text(article.published_at),
                        self._datetime_to_text(article.collected_at),
                        article.raw_content,
                        article.cleaned_content,
                        article.content_hash,
                    ),
                )
    
                    if cursor.rowcount == 1:
                        saved_articles.append(article)
    
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()
    
            return saved_articles

    def get_latest(self, limit: int) -> list[Article]:
        raise NotImplementedError

    def search(self, keyword: str) -> list[Article]:
        raise NotImplementedError

    @staticmethod
    def _datetime_to_text(value: datetime | None) -> str | None:
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("datetime must include timezone information")

        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _text_to_datetime(value: str | None) -> datetime | None:
        if value is None:
            return None

        return datetime.fromisoformat(value)


    







