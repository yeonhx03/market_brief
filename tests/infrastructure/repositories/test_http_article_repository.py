import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from market_brief.domain.models.article import Article
from market_brief.infrastructure.repositories.http_article_repository import (
    HttpArticleRepository,
)
from market_brief.infrastructure.repositories.http_auth import (
    WRITE_API_KEY_HEADER,
)


def test_save_new_posts_articles_and_skips_spring_duplicates():
    received_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers[WRITE_API_KEY_HEADER] == "test-secret"
        payload = json.loads(request.content)
        received_payloads.append(payload)

        if payload["sourceArticleId"] == "duplicate":
            return httpx.Response(
                409,
                json={
                    "code": "ARTICLE_DUPLICATE",
                    "existingArticleId": 41,
                },
            )

        return httpx.Response(
            201,
            json={"id": 42, **payload},
        )

    articles = [
        make_article("new-article"),
        make_article("duplicate"),
    ]

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleRepository(
            "http://api.test",
            client=client,
            api_key="test-secret",
        )
        result = repository.save_new(articles)

    assert len(received_payloads) == 2
    assert received_payloads[0]["collectedAt"] == "2026-08-30T00:00:00+00:00"
    assert received_payloads[0]["publishedAt"] == "2026-08-29T23:00:00+00:00"
    assert result == [make_article("new-article", article_id=42)]


def test_get_latest_maps_spring_response_to_articles():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/articles/latest"
        assert request.url.params["limit"] == "2"
        assert WRITE_API_KEY_HEADER not in request.headers

        return httpx.Response(
            200,
            json=[
                {
                    "id": 42,
                    "source": "Reuters",
                    "sourceArticleId": "article-42",
                    "title": "Market closes higher",
                    "url": "https://example.com/articles/42",
                    "canonicalUrl": None,
                    "publishedAt": None,
                    "collectedAt": "2026-08-30T00:00:00Z",
                    "rawContent": None,
                    "cleanedContent": None,
                    "contentHash": None,
                }
            ],
        )

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleRepository(
            "http://api.test",
            client=client,
            api_key="test-secret",
        )
        result = repository.get_latest(2)

    assert result == [
        Article(
            id=42,
            source="Reuters",
            source_article_id="article-42",
            title="Market closes higher",
            url="https://example.com/articles/42",
            canonical_url=None,
            published_at=None,
            collected_at=datetime(2026, 8, 30, tzinfo=timezone.utc),
            raw_content=None,
            cleaned_content=None,
            content_hash=None,
        )
    ]


def test_get_latest_with_non_positive_limit_does_not_call_spring():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected HTTP request: {request.url}")

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleRepository("http://api.test", client=client)
        assert repository.get_latest(0) == []


def test_search_reports_unsupported_initial_api():
    repository = HttpArticleRepository(
        "http://api.test",
        client=httpx.Client(
            base_url="http://api.test",
            transport=httpx.MockTransport(
                lambda request: httpx.Response(500)
            ),
        ),
    )

    try:
        with pytest.raises(
            NotImplementedError,
            match="search is not available",
        ):
            repository.search("market")
    finally:
        repository.client.close()


def make_article(
    source_article_id: str,
    article_id: int | None = None,
) -> Article:
    seoul_timezone = timezone(timedelta(hours=9))

    return Article(
        id=article_id,
        source="Reuters",
        source_article_id=source_article_id,
        title="Market closes higher",
        url=f"https://example.com/articles/{source_article_id}",
        canonical_url=None,
        published_at=datetime(
            2026,
            8,
            30,
            8,
            0,
            tzinfo=seoul_timezone,
        ),
        collected_at=datetime(
            2026,
            8,
            30,
            9,
            0,
            tzinfo=seoul_timezone,
        ),
        raw_content=None,
        cleaned_content=None,
        content_hash=None,
    )
