from market_brief.application.ports.article_repository import ArticleRepository
from market_brief.domain.models.article import Article


class GetLatestArticlesService:
    def __init__(self, repository: ArticleRepository) -> None:
        self.repository = repository

    def execute(self, limit: int) -> list[Article]:
        return self.repository.get_latest(limit)