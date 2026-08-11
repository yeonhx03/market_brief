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
        if limit <= 0:
            return []

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM articles
                ORDER BY COALESCE(published_at, collected_at) DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            connection.close()

        return [self._row_to_article(row) for row in rows]

    def search(self, keyword: str) -> list[Article]:
        keyword = keyword.strip()

        if not keyword:
            return []

        pattern = f"%{keyword}%"

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                """
                SELECT *
                FROM articles
                WHERE title LIKE ?
                OR raw_content LIKE ?
                OR cleaned_content LIKE ?
                ORDER BY COALESCE(published_at, collected_at) DESC, id DESC
                """,
                (pattern, pattern, pattern),
            ).fetchall()
        finally:
            connection.close()
        return [self._row_to_article(row) for row in rows]

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

    def _row_to_article(self, row: sqlite3.Row) -> Article:
        collected_at = self._text_to_datetime(row["collected_at"])

        if collected_at is None:
            raise ValueError("collected_at must not be NULL")

        return Article(
            title=row["title"],
            url=row["url"],
            source=row["source"],
            published_at=self._text_to_datetime(row["published_at"]),
            collected_at=collected_at,
            raw_content=row["raw_content"],
            cleaned_content=row["cleaned_content"],
            content_hash=row["content_hash"],
            source_article_id=row["source_article_id"],
            canonical_url=row["canonical_url"],
        )
