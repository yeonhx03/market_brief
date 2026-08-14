from market_brief.application.ports.article_repository import ArticleRepository
from market_brief.application.ports.news_collector import NewsCollector
from market_brief.domain.models.article import Article


class CollectNewsService:
    def __init__(
            self,
            collector: NewsCollector,
            repository: ArticleRepository
    )-> None:
        self.collector = collector
        self.repository = repository

    async def execute(self) -> list[Article]:
        articles = await self.collector.fetch()
        return self.repository.save_new(articles)
    