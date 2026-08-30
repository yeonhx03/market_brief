import json

from market_brief.application.sentiment_briefing_payload import (
    build_sentiment_briefing_payload,
)
from market_brief.domain.models.sentiment_briefing import SentimentBriefing


def serialize_sentiment_briefing(
    briefing: SentimentBriefing,
) -> str:
    return json.dumps(
        build_sentiment_briefing_payload(briefing),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
