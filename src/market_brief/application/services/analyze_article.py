from market_brief.application.ports.article_analysis_repository import (
    ArticleAnalysisRepository,
)
from market_brief.application.ports.text_sentiment_analyzer import (
    TextSentimentAnalyzer,
)
from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis


class AnalyzeArticleService:
    def __init__(
        self,
        analyzer: TextSentimentAnalyzer,
        repository: ArticleAnalysisRepository,
    ) -> None:
        self.analyzer = analyzer
        self.repository = repository

    def execute(self, article: Article) -> ArticleAnalysis:
        analysis = self.analyzer.analyze(article)
        return self.repository.save(analysis)