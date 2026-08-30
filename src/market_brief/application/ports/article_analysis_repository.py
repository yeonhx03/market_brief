from typing import Protocol

from market_brief.domain.models.article_analysis import ArticleAnalysis


class ArticleAnalysisRepository(Protocol):
    def save(self, analysis: ArticleAnalysis) -> ArticleAnalysis:
        """Persist an analysis and return it with an assigned ID."""
        ...

    def get_by_article_id(
        self,
        article_id: int,
    ) -> list[ArticleAnalysis]:
        """Return an article's analyses in newest-first order."""
        ...

    def has_analysis(
        self,
        article_id: int,
        analysis_type: str,
        analyzer_name: str,
        analyzer_version: str,
    ) -> bool:
        """Return whether the same analysis identity already exists."""
        ...