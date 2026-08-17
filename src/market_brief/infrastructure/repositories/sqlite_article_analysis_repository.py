import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from market_brief.domain.models.article_analysis import ArticleAnalysis


class SQLiteArticleAnalysisRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = db_path
        self._create_table()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _create_table(self) -> None:
        connection = self._connect()

        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS article_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    analysis_type TEXT NOT NULL,
                    analyzer_name TEXT NOT NULL,
                    analyzer_version TEXT NOT NULL,
                    analyzed_at TEXT NOT NULL,
                    text_sentiment TEXT NOT NULL,
                    positive_score REAL NOT NULL,
                    neutral_score REAL NOT NULL,
                    negative_score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    FOREIGN KEY (article_id) REFERENCES articles(id)
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def save(self, analysis: ArticleAnalysis) -> ArticleAnalysis:
        if analysis.id is not None:
            raise ValueError("analysis id must be None before save")

        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                INSERT INTO article_analyses (
                    article_id,
                    analysis_type,
                    analyzer_name,
                    analyzer_version,
                    analyzed_at,
                    text_sentiment,
                    positive_score,
                    neutral_score,
                    negative_score,
                    confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.article_id,
                    analysis.analysis_type,
                    analysis.analyzer_name,
                    analysis.analyzer_version,
                    self._datetime_to_text(analysis.analyzed_at),
                    analysis.text_sentiment,
                    analysis.positive_score,
                    analysis.neutral_score,
                    analysis.negative_score,
                    analysis.confidence,
                ),
            )

            analysis_id = cursor.lastrowid

            if analysis_id is None:
                raise RuntimeError("saved analysis must have an id")

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

        return replace(analysis, id=analysis_id)


    def get_by_article_id(
        self,
        article_id: int,
    ) -> list[ArticleAnalysis]:
        connection = self._connect()
        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM article_analyses
                WHERE article_id = ?
                ORDER BY analyzed_at DESC, id DESC
                """,
                (article_id,),
            ).fetchall()
        finally:
            connection.close()

        return [self._row_to_analysis(row) for row in rows]


    @staticmethod
    def _datetime_to_text(value: datetime) -> str:
        if value.tzinfo is None:
            raise ValueError("datetime must include timezone information")

        return value.astimezone(timezone.utc).isoformat()


    @staticmethod
    def _text_to_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value)


    def _row_to_analysis(
        self,
        row: sqlite3.Row,
    ) -> ArticleAnalysis:
        return ArticleAnalysis(
            article_id=row["article_id"],
            analysis_type=row["analysis_type"],
            analyzer_name=row["analyzer_name"],
            analyzer_version=row["analyzer_version"],
            analyzed_at=self._text_to_datetime(row["analyzed_at"]),
            text_sentiment=row["text_sentiment"],
            positive_score=float(row["positive_score"]),
            neutral_score=float(row["neutral_score"]),
            negative_score=float(row["negative_score"]),
            confidence=float(row["confidence"]),
            id=row["id"],
        )
