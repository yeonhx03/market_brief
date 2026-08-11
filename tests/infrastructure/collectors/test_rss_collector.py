import logging

import httpx
import pytest

from market_brief.infrastructure.collectors.rss_collector import RSSCollector


@pytest.mark.asyncio
async def test_fetch_returns_empty_list_when_request_fails(
    monkeypatch,
    caplog,
):
    async def fake_get(self, url):
        request = httpx.Request("GET", url)
        raise httpx.ConnectError(
            "Connection failed",
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    caplog.set_level(logging.ERROR)

    collector = RSSCollector(
        feed_url="https://example.com/feed.xml",
        source="Test Source",
    )

    result = await collector.fetch()

    assert result == []
    assert "RSS request failed" in caplog.text


@pytest.mark.asyncio
async def test_fetch_returns_empty_list_when_http_status_is_error(
    monkeypatch,
    caplog,
):
    async def fake_get(self, url):
        request = httpx.Request("GET", url)

        return httpx.Response(
            status_code=404,
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    caplog.set_level(logging.ERROR)

    collector = RSSCollector(
        feed_url="https://example.com/feed.xml",
        source="Test Source",
    )

    result = await collector.fetch()

    assert result == []
    assert "RSS HTTP status error" in caplog.text
    assert "status_code=404" in caplog.text


@pytest.mark.asyncio
async def test_fetch_logs_warning_and_keeps_entries_when_feed_is_malformed(
    monkeypatch,
    caplog,
):
    async def fake_get(self, url):
        request = httpx.Request("GET", url)

        malformed_rss = b"""
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test article</title>
                    <link>https://example.com/article</link>
                </item>
            </channel-broken>
        </rss>
        """

        return httpx.Response(
            status_code=200,
            content=malformed_rss,
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    caplog.set_level(logging.WARNING)

    collector = RSSCollector(
        feed_url="https://example.com/feed.xml",
        source="Test Source",
    )

    result = await collector.fetch()

    assert len(result) == 1
    assert result[0].title == "Test article"
    assert result[0].url == "https://example.com/article"
    assert "RSS parsing warning" in caplog.text


def test_parse_published_at_returns_none_when_date_is_invalid(caplog):
    collector = RSSCollector(
        feed_url="https://example.com/feed.xml",
        source="Test Source",
    )

    entry = {
        "link": "https://example.com/article",
        "published_parsed": (
            2026,
            13,
            1,
            9,
            0,
            0,
            0,
            1,
            0,
        ),
    }

    caplog.set_level(logging.WARNING)

    result = collector._parse_published_at(entry)

    assert result is None
    assert "Invalid RSS published date" in caplog.text
    assert "article_url=https://example.com/article" in caplog.text


@pytest.mark.asyncio
async def test_fetch_skips_invalid_entry_and_continues(
    monkeypatch,
    caplog,
):
    async def fake_get(self, url):
        request = httpx.Request("GET", url)

        return httpx.Response(
            status_code=200,
            content=b"<rss></rss>",
            request=request,
        )

    class FakeFeed:
        bozo = 0
        entries = [
            {
                "title": 123,
                "link": "https://example.com/invalid",
            },
            {
                "title": "Valid article",
                "link": "https://example.com/valid",
            },
        ]

    def fake_parse(content):
        return FakeFeed()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    monkeypatch.setattr(
        "market_brief.infrastructure.collectors.rss_collector.feedparser.parse",
        fake_parse,
    )
    caplog.set_level(logging.WARNING)

    collector = RSSCollector(
        feed_url="https://example.com/feed.xml",
        source="Test Source",
    )

    result = await collector.fetch()

    assert len(result) == 1
    assert result[0].title == "Valid article"
    assert result[0].url == "https://example.com/valid"
    assert "Skipped invalid RSS entry" in caplog.text
    assert "entry_index=1" in caplog.text
