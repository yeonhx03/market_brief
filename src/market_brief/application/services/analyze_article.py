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

    def execute(
        self,
        article: Article,
    ) -> ArticleAnalysis | None:
        if article.id is None:
            raise ValueError("article must be persisted before analysis")

        if self.repository.has_analysis(
            article_id=article.id,
            analysis_type=self.analyzer.analysis_type,
            analyzer_name=self.analyzer.analyzer_name,
            analyzer_version=self.analyzer.analyzer_version,
        ):
            return None

        analysis = self.analyzer.analyze(article)
        return self.repository.save(analysis)