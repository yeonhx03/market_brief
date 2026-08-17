from typing import Protocol
from market_brief.domain.models.article import Article

class ArticleRepository(Protocol):
    def save_new(self, articles: list[Article]) -> list[Article]:
        """Save new articles and return inserted articles with assigned IDs."""
        ...

    def get_latest(self, limit: int) -> list[Article]:
        """Return persisted articles with assigned IDs."""
        ...

    def search(self, keyword: str) -> list[Article]:
        """Return matching persisted articles with assigned IDs."""
        ...

