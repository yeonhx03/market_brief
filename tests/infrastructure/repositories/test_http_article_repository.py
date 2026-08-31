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


def test_save_new_links_ticker_for_created_and_existing_articles():
    linked_article_ids: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers[WRITE_API_KEY_HEADER] == "test-secret"

        if request.url.path.endswith("/tickers"):
            linked_article_ids.append(int(request.url.path.split("/")[3]))
            assert json.loads(request.content) == {"ticker": "AAPL"}
            return httpx.Response(204)

        payload = json.loads(request.content)

        if payload["sourceArticleId"] == "duplicate":
            return httpx.Response(
                409,
                json={
                    "code": "ARTICLE_DUPLICATE",
                    "existingArticleId": 41,
                },
            )

        return httpx.Response(201, json={"id": 42, **payload})

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleRepository(
            "http://api.test",
            client=client,
            api_key="test-secret",
            ticker="AAPL",
        )
        result = repository.save_new(
            [make_article("new-article"), make_article("duplicate")]
        )

    assert result == [make_article("new-article", article_id=42)]
    assert linked_article_ids == [42, 41]


def test_save_new_rejects_duplicate_without_id_when_linking_ticker():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "code": "ARTICLE_DUPLICATE",
                "existingArticleId": None,
            },
        )

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleRepository(
            "http://api.test",
            client=client,
            ticker="AAPL",
        )

        with pytest.raises(
            RuntimeError,
            match="duplicate response requires existingArticleId",
        ):
            repository.save_new([make_article("duplicate")])


@pytest.mark.parametrize("status_code", [400, 401, 404])
def test_save_new_propagates_ticker_link_errors(status_code):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/tickers"):
            return httpx.Response(status_code)

        payload = json.loads(request.content)
        return httpx.Response(201, json={"id": 42, **payload})

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        repository = HttpArticleRepository(
            "http://api.test",
            client=client,
            ticker="AAPL",
        )

        with pytest.raises(httpx.HTTPStatusError):
            repository.save_new([make_article("new-article")])


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
