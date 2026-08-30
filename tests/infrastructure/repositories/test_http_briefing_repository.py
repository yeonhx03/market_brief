import json
from datetime import datetime, timezone

import httpx
import pytest

from market_brief.domain.models.sentiment_briefing import (
    SentimentBriefing,
    SentimentBriefingItem,
)
from market_brief.infrastructure.repositories.http_briefing_repository import (
    HttpBriefingRepository,
)
from market_brief.infrastructure.repositories.http_auth import (
    WRITE_API_KEY_HEADER,
)


def make_briefing() -> SentimentBriefing:
    return SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(
            SentimentBriefingItem(
                article_id=7,
                title="Market update",
                source="Example News",
                url="https://example.com/article",
                timestamp=datetime(2026, 8, 30, 1, 0, tzinfo=timezone.utc),
                timestamp_label="Published",
                analysis=None,
            ),
        ),
    )


def test_save_posts_spring_payload_and_returns_briefing_id():
    received_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/briefings"
        assert request.headers[WRITE_API_KEY_HEADER] == "test-secret"
        received_payloads.append(json.loads(request.content))
        return httpx.Response(
            201,
            json={
                "briefingId": 31,
                "createdAt": "2026-08-30T01:05:00Z",
            },
        )

    client = httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    )
    repository = HttpBriefingRepository(
        base_url="http://api.test/",
        client=client,
        api_key="test-secret",
    )

    result = repository.save(make_briefing())

    assert result == 31
    assert received_payloads == [
        {
            "schemaVersion": 1,
            "briefingType": "text_sentiment",
            "analysisSelector": {
                "analysisType": "text_sentiment",
                "analyzerName": "ProsusAI/finbert",
                "analyzerVersion": "revision-v1",
            },
            "summary": {
                "articleCount": 1,
                "analyzedCount": 0,
                "missingAnalysisCount": 1,
                "labelCounts": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0,
                },
            },
            "items": [
                {
                    "articleId": 7,
                    "title": "Market update",
                    "source": "Example News",
                    "url": "https://example.com/article",
                    "displayTimestamp": "2026-08-30T01:00:00+00:00",
                    "timestampType": "published",
                    "analysisStatus": "missing_for_selected_model",
                    "analysis": None,
                }
            ],
        }
    ]
    client.close()


def test_save_raises_for_spring_error_response():
    client = httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(400, json={"code": "INVALID"})
        ),
    )
    repository = HttpBriefingRepository(
        base_url="http://api.test",
        client=client,
    )

    with pytest.raises(httpx.HTTPStatusError):
        repository.save(make_briefing())

    client.close()


def test_save_rejects_response_without_integer_briefing_id():
    client = httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(201, json={"briefingId": "31"})
        ),
    )
    repository = HttpBriefingRepository(
        base_url="http://api.test",
        client=client,
    )

    with pytest.raises(ValueError, match="integer briefingId"):
        repository.save(make_briefing())

    client.close()
