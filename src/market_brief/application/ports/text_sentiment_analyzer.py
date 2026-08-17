from typing import Protocol

from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis


class TextSentimentAnalyzer(Protocol):
    def analyze(self, article: Article) -> ArticleAnalysis:
        ...