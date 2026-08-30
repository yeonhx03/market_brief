import httpx

from market_brief.application.sentiment_briefing_payload import (
    build_sentiment_briefing_payload,
)
from market_brief.domain.models.sentiment_briefing import SentimentBriefing
from market_brief.infrastructure.repositories.http_auth import (
    build_write_headers,
)


class HttpBriefingRepository:
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

    def save(self, briefing: SentimentBriefing) -> int:
        response = self.client.post(
            "/api/briefings",
            json=build_sentiment_briefing_payload(briefing),
            headers=self.write_headers,
        )
        response.raise_for_status()

        briefing_id = response.json().get("briefingId")

        if not isinstance(briefing_id, int):
            raise ValueError(
                "Spring briefing response requires an integer briefingId"
            )

        return briefing_id
