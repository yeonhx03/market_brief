from pathlib import Path

from market_brief.application.services.collect_news import CollectNewsService
from market_brief.application.services.get_latest_articles import (
    GetLatestArticlesService,
    )
from market_brief.infrastructure.collectors.rss_collector import RSSCollector
from market_brief.infrastructure.repositories.sqlite_repository import (
    SQLiteArticleRepository,
)


def build_collect_news_service(
    feed_url: str,
    source: str,
    db_path: str | Path,
) -> CollectNewsService:
    collector = RSSCollector(
        feed_url=feed_url,
        source=source,
    )
    repository = SQLiteArticleRepository(db_path=db_path)

    return CollectNewsService(
        collector=collector,
        repository=repository,
    )

def build_get_latest_articles_service(
    db_path: str | Path,
) -> GetLatestArticlesService:
    repository = SQLiteArticleRepository(db_path=db_path)

    return GetLatestArticlesService(repository=repository)