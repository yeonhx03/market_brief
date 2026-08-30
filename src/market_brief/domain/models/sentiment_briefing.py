from dataclasses import dataclass
from datetime import datetime

from market_brief.domain.models.article_analysis import ArticleAnalysis


@dataclass(frozen=True)
class SentimentBriefingItem:
    article_id: int
    title: str
    source: str
    url: str
    timestamp: datetime
    timestamp_label: str
    analysis: ArticleAnalysis | None


@dataclass(frozen=True)
class SentimentBriefing:
    analysis_type: str
    analyzer_name: str
    analyzer_version: str
    items: tuple[SentimentBriefingItem, ...]