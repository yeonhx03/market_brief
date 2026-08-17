from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ArticleAnalysis:
    article_id: int
    analysis_type: str
    analyzer_name: str
    analyzer_version: str
    analyzed_at: datetime
    text_sentiment: str
    positive_score: float
    neutral_score: float
    negative_score: float
    confidence: float
    id: int | None = None