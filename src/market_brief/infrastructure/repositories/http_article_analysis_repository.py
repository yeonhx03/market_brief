from datetime import datetime, timezone

import httpx

from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.infrastructure.repositories.http_auth import (
    build_write_headers,
)


class HttpArticleAnalysisRepository:
    def __init__(
        self,
        base_url: str,
        client: httpx.Client | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.write_headers = build_write_headers(api_key)
        self.client = client or httpx.Client(
            base_url=self.base_url,
            timeout=10.0,
        )

    def save(self, analysis: ArticleAnalysis) -> ArticleAnalysis:
        if analysis.id is not None:
            raise ValueError("analysis id must be None before save")

        response = self.client.post(
            f"/api/articles/{analysis.article_id}/analyses",
            json=self._analysis_to_payload(analysis),
            headers=self.write_headers,
        )

        if response.status_code == 409:
            existing = self._find_existing_analysis(analysis)

            if existing is not None:
                return existing

        response.raise_for_status()
        return self._payload_to_analysis(response.json())

    def get_by_article_id(self, article_id: int) -> list[ArticleAnalysis]:
        response = self.client.get(f"/api/articles/{article_id}/analyses")
        response.raise_for_status()

        return [
            self._payload_to_analysis(payload)
            for payload in response.json()
        ]

    def has_analysis(
        self,
        article_id: int,
        analysis_type: str,
        analyzer_name: str,
        analyzer_version: str,
    ) -> bool:
        return any(
            analysis.analysis_type == analysis_type
            and analysis.analyzer_name == analyzer_name
            and analysis.analyzer_version == analyzer_version
            for analysis in self.get_by_article_id(article_id)
        )

    def _find_existing_analysis(
        self,
        expected: ArticleAnalysis,
    ) -> ArticleAnalysis | None:
        return next(
            (
                analysis
                for analysis in self.get_by_article_id(expected.article_id)
                if analysis.analysis_type == expected.analysis_type
                and analysis.analyzer_name == expected.analyzer_name
                and analysis.analyzer_version == expected.analyzer_version
            ),
            None,
        )

    @staticmethod
    def _analysis_to_payload(analysis: ArticleAnalysis) -> dict[str, object]:
        return {
            "analysisType": analysis.analysis_type,
            "analyzerName": analysis.analyzer_name,
            "analyzerVersion": analysis.analyzer_version,
            "analyzedAt": HttpArticleAnalysisRepository._datetime_to_text(
                analysis.analyzed_at
            ),
            "textSentiment": analysis.text_sentiment,
            "positiveScore": analysis.positive_score,
            "neutralScore": analysis.neutral_score,
            "negativeScore": analysis.negative_score,
            "confidence": analysis.confidence,
        }

    @staticmethod
    def _payload_to_analysis(payload: dict[str, object]) -> ArticleAnalysis:
        analysis_id = payload.get("analysisId")
        article_id = payload.get("articleId")

        if not isinstance(analysis_id, int):
            raise ValueError("Spring analysis response requires an integer analysisId")

        if not isinstance(article_id, int):
            raise ValueError("Spring analysis response requires an integer articleId")

        return ArticleAnalysis(
            id=analysis_id,
            article_id=article_id,
            analysis_type=str(payload["analysisType"]),
            analyzer_name=str(payload["analyzerName"]),
            analyzer_version=str(payload["analyzerVersion"]),
            analyzed_at=HttpArticleAnalysisRepository._text_to_datetime(
                payload.get("analyzedAt")
            ),
            text_sentiment=str(payload["textSentiment"]),
            positive_score=float(payload["positiveScore"]),
            neutral_score=float(payload["neutralScore"]),
            negative_score=float(payload["negativeScore"]),
            confidence=float(payload["confidence"]),
        )

    @staticmethod
    def _datetime_to_text(value: datetime) -> str:
        if value.tzinfo is None:
            raise ValueError("datetime must include timezone information")

        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _text_to_datetime(value: object) -> datetime:
        if not isinstance(value, str):
            raise ValueError("Spring analysis response requires analyzedAt")

        return datetime.fromisoformat(value.replace("Z", "+00:00"))
