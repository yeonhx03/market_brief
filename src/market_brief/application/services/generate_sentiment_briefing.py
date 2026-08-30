from datetime import datetime
from zoneinfo import ZoneInfo

from market_brief.application.ports.article_analysis_repository import (
    ArticleAnalysisRepository,
)
from market_brief.application.ports.article_repository import ArticleRepository
from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.domain.models.sentiment_briefing import (
    SentimentBriefing,
    SentimentBriefingItem,
)


SEOUL_TIMEZONE = ZoneInfo("Asia/Seoul")


class GenerateSentimentBriefingService:
    def __init__(
        self,
        article_repository: ArticleRepository,
        analysis_repository: ArticleAnalysisRepository,
        analysis_type: str,
        analyzer_name: str,
        analyzer_version: str,
    ) -> None:
        self.article_repository = article_repository
        self.analysis_repository = analysis_repository
        self.analysis_type = analysis_type
        self.analyzer_name = analyzer_name
        self.analyzer_version = analyzer_version

    def execute(self, limit: int) -> SentimentBriefing:
        articles = self.article_repository.get_latest(limit)
        items: list[SentimentBriefingItem] = []

        for article in articles:
            if article.id is None:
                raise ValueError("briefing requires persisted articles")

            analyses = self.analysis_repository.get_by_article_id(article.id)
            selected_analysis = self._select_analysis(
                article_id=article.id,
                analyses=analyses,
            )

            if article.published_at is not None:
                timestamp = article.published_at
                timestamp_label = "Published"
            else:
                timestamp = article.collected_at
                timestamp_label = "Collected"

            items.append(
                SentimentBriefingItem(
                    article_id=article.id,
                    title=article.title,
                    source=article.source,
                    url=article.url,
                    timestamp=timestamp.astimezone(SEOUL_TIMEZONE),
                    timestamp_label=timestamp_label,
                    analysis=selected_analysis,
                )
            )

        return SentimentBriefing(
            analysis_type=self.analysis_type,
            analyzer_name=self.analyzer_name,
            analyzer_version=self.analyzer_version,
            items=tuple(items),
        )

    def _select_analysis(
        self,
        article_id: int,
        analyses: list[ArticleAnalysis],
    ) -> ArticleAnalysis | None:
        matching_analyses = [
            analysis
            for analysis in analyses
            if (
                analysis.article_id == article_id
                and analysis.analysis_type == self.analysis_type
                and analysis.analyzer_name == self.analyzer_name
                and analysis.analyzer_version == self.analyzer_version
            )
        ]

        return max(
            matching_analyses,
            key=self._analysis_sort_key,
            default=None,
        )

    @staticmethod
    def _analysis_sort_key(
        analysis: ArticleAnalysis,
    ) -> tuple[datetime, int]:
        analysis_id = analysis.id if analysis.id is not None else -1
        return analysis.analyzed_at, analysis_id