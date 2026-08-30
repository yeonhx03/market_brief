from typing import Protocol

from market_brief.domain.models.sentiment_briefing import SentimentBriefing


class BriefingRepository(Protocol):
    def save(self, briefing: SentimentBriefing) -> int:
        """Persist a briefing and return its assigned identifier."""
        ...
