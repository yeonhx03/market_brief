import json
from datetime import datetime, timezone

import httpx

from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.infrastructure.repositories.http_article_analysis_repository import (
    HttpArticleAnalysisRepository,
)
from market_brief.infrastructure.repositories.http_auth import (
    WRITE_API_KEY_HEADER,
)


def test_save_posts_analysis_and_maps_assigned_id():
    received_payload: dict[str, object] | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal received_payload
        assert request.headers[WRITE_API_KEY_HEADER] == "test-secret"
        received_payload = json.loads(request.content)
        return httpx.Response(
            201,
            json={
                "analysisId": 7,
                "articleId": 42,
                **received_payload,
            },
        )

    analysis = make_analysis()

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleAnalysisRepository(
            "http://api.test",
            client=client,
            api_key="test-secret",
        )
        result = repository.save(analysis)

    assert received_payload is not None
    assert received_payload["analyzedAt"] == "2026-08-30T09:00:00+00:00"
    assert received_payload["neutralScore"] == 0.89
    assert result == make_analysis(analysis_id=7)


def test_get_and_has_analysis_use_spring_results():
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        assert WRITE_API_KEY_HEADER not in request.headers
        request_count += 1
        return httpx.Response(200, json=[analysis_payload()])

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleAnalysisRepository(
            "http://api.test",
            client=client,
            api_key="test-secret",
        )

        assert repository.get_by_article_id(42) == [
            make_analysis(analysis_id=7)
        ]
        assert repository.has_analysis(
            article_id=42,
            analysis_type="text_sentiment",
            analyzer_name="ProsusAI/finbert",
            analyzer_version="revision-1",
        )
        assert not repository.has_analysis(
            article_id=42,
            analysis_type="text_sentiment",
            analyzer_name="ProsusAI/finbert",
            analyzer_version="revision-2",
        )

    assert request_count == 3


def test_save_returns_existing_analysis_when_spring_reports_duplicate():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            assert request.headers[WRITE_API_KEY_HEADER] == "test-secret"
            return httpx.Response(
                409,
                json={
                    "code": "ARTICLE_ANALYSIS_DUPLICATE",
                    "existingAnalysisId": 7,
                },
            )

        assert WRITE_API_KEY_HEADER not in request.headers
        return httpx.Response(200, json=[analysis_payload()])

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleAnalysisRepository(
            "http://api.test",
            client=client,
            api_key="test-secret",
        )
        result = repository.save(make_analysis())

    assert result == make_analysis(analysis_id=7)


def make_analysis(analysis_id: int | None = None) -> ArticleAnalysis:
    return ArticleAnalysis(
        id=analysis_id,
        article_id=42,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-1",
        analyzed_at=datetime(2026, 8, 30, 9, 0, tzinfo=timezone.utc),
        text_sentiment="neutral",
        positive_score=0.08,
        neutral_score=0.89,
        negative_score=0.03,
        confidence=0.89,
    )


def analysis_payload() -> dict[str, object]:
    return {
        "analysisId": 7,
        "articleId": 42,
        "analysisType": "text_sentiment",
        "analyzerName": "ProsusAI/finbert",
        "analyzerVersion": "revision-1",
        "analyzedAt": "2026-08-30T09:00:00Z",
        "textSentiment": "neutral",
        "positiveScore": 0.08,
        "neutralScore": 0.89,
        "negativeScore": 0.03,
        "confidence": 0.89,
    }
