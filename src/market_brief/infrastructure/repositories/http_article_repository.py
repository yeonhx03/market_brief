from datetime import datetime, timezone

import httpx

from market_brief.domain.models.article import Article
from market_brief.infrastructure.repositories.http_auth import (
    build_write_headers,
)


class HttpArticleRepository:
    def __init__(
        self,
        base_url: str,
        client: httpx.Client | None = None,
        api_key: str | None = None,
        ticker: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.write_headers = build_write_headers(api_key)
        self.ticker = ticker
        self.client = client or httpx.Client(
            base_url=self.base_url,
            timeout=10.0,
        )

    def save_new(self, articles: list[Article]) -> list[Article]:
        saved_articles: list[Article] = []

        for article in articles:
            response = self.client.post(
                "/api/articles",
                json=self._article_to_payload(article),
                headers=self.write_headers,
            )

            if response.status_code == 409:
                if self.ticker is not None:
                    self._link_ticker(
                        self._duplicate_article_id(response),
                        self.ticker,
                    )
                continue

            response.raise_for_status()
            saved_article = self._payload_to_article(response.json())

            if self.ticker is not None:
                self._link_ticker(saved_article.id, self.ticker)

            saved_articles.append(saved_article)

        return saved_articles

    def get_latest(self, limit: int) -> list[Article]:
        if limit <= 0:
            return []

        response = self.client.get(
            "/api/articles/latest",
            params={"limit": limit},
        )
        response.raise_for_status()

        return [
            self._payload_to_article(payload)
            for payload in response.json()
        ]

    def search(self, keyword: str) -> list[Article]:
        raise NotImplementedError(
            "Article search is not available in the initial Spring API"
        )

    def _link_ticker(self, article_id: int | None, ticker: str) -> None:
        if article_id is None:
            raise RuntimeError("persisted article must have an id")

        response = self.client.post(
            f"/api/articles/{article_id}/tickers",
            json={"ticker": ticker},
            headers=self.write_headers,
        )
        response.raise_for_status()

    @staticmethod
    def _duplicate_article_id(response: httpx.Response) -> int:
        try:
            article_id = response.json().get("existingArticleId")
        except (AttributeError, ValueError) as error:
            raise RuntimeError(
                "Spring duplicate response requires existingArticleId "
                "when ticker linking is enabled"
            ) from error

        if isinstance(article_id, bool) or not isinstance(article_id, int):
            raise RuntimeError(
                "Spring duplicate response requires existingArticleId "
                "when ticker linking is enabled"
            )

        return article_id

    @staticmethod
    def _article_to_payload(article: Article) -> dict[str, object]:
        return {
            "source": article.source,
            "sourceArticleId": article.source_article_id,
            "title": article.title,
            "url": article.url,
            "canonicalUrl": article.canonical_url,
            "publishedAt": HttpArticleRepository._datetime_to_text(
                article.published_at
            ),
            "collectedAt": HttpArticleRepository._datetime_to_text(
                article.collected_at
            ),
            "rawContent": article.raw_content,
            "cleanedContent": article.cleaned_content,
            "contentHash": article.content_hash,
        }

    @staticmethod
    def _payload_to_article(payload: dict[str, object]) -> Article:
        collected_at = HttpArticleRepository._text_to_datetime(
            payload.get("collectedAt")
        )

        if collected_at is None:
            raise ValueError("Spring article response requires collectedAt")

        article_id = payload.get("id")

        if not isinstance(article_id, int):
            raise ValueError("Spring article response requires an integer id")

        return Article(
            id=article_id,
            source=str(payload["source"]),
            source_article_id=HttpArticleRepository._optional_text(
                payload.get("sourceArticleId")
            ),
            title=str(payload["title"]),
            url=str(payload["url"]),
            canonical_url=HttpArticleRepository._optional_text(
                payload.get("canonicalUrl")
            ),
            published_at=HttpArticleRepository._text_to_datetime(
                payload.get("publishedAt")
            ),
            collected_at=collected_at,
            raw_content=HttpArticleRepository._optional_text(
                payload.get("rawContent")
            ),
            cleaned_content=HttpArticleRepository._optional_text(
                payload.get("cleanedContent")
            ),
            content_hash=HttpArticleRepository._optional_text(
                payload.get("contentHash")
            ),
        )

    @staticmethod
    def _datetime_to_text(value: datetime | None) -> str | None:
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("datetime must include timezone information")

        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _text_to_datetime(value: object) -> datetime | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError("Spring datetime value must be a string")

        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _optional_text(value: object) -> str | None:
        return None if value is None else str(value)
