import sqlite3
from pathlib import Path

from market_brief.domain.models.article import Article


class SQLiteArticleRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        pass

    def save_new(self, articles: list[Article]) -> list[Article]:
        raise NotImplementedError

    def get_latest(self, limit: int) -> list[Article]:
        raise NotImplementedError

    def search(self, keyword: str) -> list[Article]:
        raise NotImplementedError