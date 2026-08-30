import os
from datetime import datetime, timezone
from pathlib import Path

from market_brief.application.services.collect_news import CollectNewsService
from market_brief.application.services.get_latest_articles import (
    GetLatestArticlesService,
    )
from market_brief.application.services.analyze_article import (
    AnalyzeArticleService,
)
from market_brief.application.services.generate_briefing import (
    GenerateBriefingService,
)
from market_brief.application.services.generate_sentiment_briefing import (
    GenerateSentimentBriefingService,
)

from market_brief.infrastructure.collectors.rss_collector import RSSCollector
from market_brief.infrastructure.repositories.sqlite_repository import (
    SQLiteArticleRepository,
)
from market_brief.infrastructure.analyzers.finbert_analyzer import (
    FinBERTAnalyzer,
)
from market_brief.infrastructure.analyzers.transformers_finbert_classifier import (
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_REVISION,
    TransformersFinBERTClassifier,
)
from market_brief.infrastructure.repositories.sqlite_article_analysis_repository import (
    SQLiteArticleAnalysisRepository,
)
from market_brief.infrastructure.repositories.http_article_repository import (
    HttpArticleRepository,
)
from market_brief.infrastructure.repositories.http_article_analysis_repository import (
    HttpArticleAnalysisRepository,
)
from market_brief.infrastructure.repositories.http_briefing_repository import (
    HttpBriefingRepository,
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


def build_generate_briefing_service(
        db_path: str | Path,
) -> GenerateBriefingService:
    repository = SQLiteArticleRepository(db_path=db_path)

    return GenerateBriefingService(repository=repository)


def build_generate_sentiment_briefing_service(
    db_path: str | Path,
) -> GenerateSentimentBriefingService:
    article_repository = SQLiteArticleRepository(db_path=db_path)
    analysis_repository = SQLiteArticleAnalysisRepository(db_path=db_path)

    return GenerateSentimentBriefingService(
        article_repository=article_repository,
        analysis_repository=analysis_repository,
        analysis_type="text_sentiment",
        analyzer_name=DEFAULT_MODEL_NAME,
        analyzer_version=DEFAULT_MODEL_REVISION,
    )


def build_analyze_article_service(
    db_path: str | Path,
) -> AnalyzeArticleService:
    classifier = TransformersFinBERTClassifier.from_pretrained()

    analyzer = FinBERTAnalyzer(
        classifier=classifier,
        analyzer_name=DEFAULT_MODEL_NAME,
        analyzer_version=DEFAULT_MODEL_REVISION,
        clock=lambda: datetime.now(timezone.utc),
    )

    repository = SQLiteArticleAnalysisRepository(db_path=db_path)

    return AnalyzeArticleService(
        analyzer=analyzer,
        repository=repository,
    )


def build_http_collect_news_service(
    feed_url: str,
    source: str,
    api_url: str,
) -> CollectNewsService:
    collector = RSSCollector(feed_url=feed_url, source=source)
    repository = HttpArticleRepository(
        base_url=api_url,
        api_key=_write_api_key(),
    )

    return CollectNewsService(
        collector=collector,
        repository=repository,
    )


def build_http_get_latest_articles_service(
    api_url: str,
) -> GetLatestArticlesService:
    return GetLatestArticlesService(
        repository=HttpArticleRepository(
            base_url=api_url,
            api_key=_write_api_key(),
        )
    )


def build_http_generate_briefing_service(
    api_url: str,
) -> GenerateBriefingService:
    return GenerateBriefingService(
        repository=HttpArticleRepository(
            base_url=api_url,
            api_key=_write_api_key(),
        )
    )


def build_http_generate_sentiment_briefing_service(
    api_url: str,
) -> GenerateSentimentBriefingService:
    return GenerateSentimentBriefingService(
        article_repository=HttpArticleRepository(
            base_url=api_url,
            api_key=_write_api_key(),
        ),
        analysis_repository=HttpArticleAnalysisRepository(
            base_url=api_url,
            api_key=_write_api_key(),
        ),
        analysis_type="text_sentiment",
        analyzer_name=DEFAULT_MODEL_NAME,
        analyzer_version=DEFAULT_MODEL_REVISION,
    )


def build_http_briefing_repository(
    api_url: str,
) -> HttpBriefingRepository:
    return HttpBriefingRepository(
        base_url=api_url,
        api_key=_write_api_key(),
    )


def build_http_analyze_article_service(
    api_url: str,
) -> AnalyzeArticleService:
    classifier = TransformersFinBERTClassifier.from_pretrained()
    analyzer = FinBERTAnalyzer(
        classifier=classifier,
        analyzer_name=DEFAULT_MODEL_NAME,
        analyzer_version=DEFAULT_MODEL_REVISION,
        clock=lambda: datetime.now(timezone.utc),
    )

    return AnalyzeArticleService(
        analyzer=analyzer,
        repository=HttpArticleAnalysisRepository(
            base_url=api_url,
            api_key=_write_api_key(),
        ),
    )


def _write_api_key() -> str | None:
    value = os.environ.get("WRITE_API_KEY")
    return None if value is None or value.isspace() else value
