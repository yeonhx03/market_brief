from typing import Protocol

from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis


class TextSentimentAnalyzer(Protocol):
    analysis_type: str
    analyzer_name: str
    analyzer_version: str

    def analyze(self, article: Article) -> ArticleAnalysis:
        ...