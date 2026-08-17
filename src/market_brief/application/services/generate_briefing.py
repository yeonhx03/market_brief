from zoneinfo import ZoneInfo
from market_brief.application.ports.article_repository import ArticleRepository
from market_brief.domain.models.briefing import Briefing, BriefingItem


SEOUL_TIMEZONE = ZoneInfo("Asia/Seoul")


class GenerateBriefingService:
    def __init__(self, repository: ArticleRepository) -> None:
        self.repository = repository

    def execute(self, limit: int) -> Briefing:
        articles = self.repository.get_latest(limit)
        items: list[BriefingItem] = []

        for article in articles:
            if article.published_at is not None:
                timestamp = article.published_at
                timestamp_label = "Published"
            else:
                timestamp = article.collected_at
                timestamp_label = "Collected"

            items.append(
                BriefingItem(
                    title=article.title,
                    source=article.source,
                    url=article.url,
                    timestamp=timestamp.astimezone(SEOUL_TIMEZONE),
                    timestamp_label=timestamp_label,
                )
            )

        return Briefing(items=tuple(items))