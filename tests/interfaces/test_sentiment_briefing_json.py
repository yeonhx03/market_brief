import json
from datetime import datetime
from zoneinfo import ZoneInfo

from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.domain.models.sentiment_briefing import (
    SentimentBriefing,
    SentimentBriefingItem,
)
from market_brief.interfaces.sentiment_briefing_json import (
    serialize_sentiment_briefing,
)


def make_briefing() -> SentimentBriefing:
    analysis = ArticleAnalysis(
        id=7,
        article_id=1,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        analyzed_at=datetime(
            2026,
            8,
            30,
            10,
            0,
            tzinfo=ZoneInfo("Asia/Seoul"),
        ),
        text_sentiment="neutral",
        positive_score=0.1,
        neutral_score=0.8,
        negative_score=0.1,
        confidence=0.8,
    )
    timestamp = datetime(
        2026,
        8,
        30,
        10,
        0,
        tzinfo=ZoneInfo("Asia/Seoul"),
    )

    return SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(
            SentimentBriefingItem(
                article_id=1,
                title="시장 뉴스",
                source="BBC Business",
                url="https://example.com/analyzed",
                timestamp=timestamp,
                timestamp_label="Published",
                analysis=analysis,
            ),
            SentimentBriefingItem(
                article_id=2,
                title="Missing analysis",
                source="BBC Technology",
                url="https://example.com/missing",
                timestamp=timestamp,
                timestamp_label="Collected",
                analysis=None,
            ),
        ),
    )


def test_serialize_sentiment_briefing_returns_persistence_ready_json():
    result = serialize_sentiment_briefing(make_briefing())

    assert json.loads(result) == {
        "schemaVersion": 1,
        "briefingType": "text_sentiment",
        "analysisSelector": {
            "analysisType": "text_sentiment",
            "analyzerName": "ProsusAI/finbert",
            "analyzerVersion": "revision-v1",
        },
        "summary": {
            "articleCount": 2,
            "analyzedCount": 1,
            "missingAnalysisCount": 1,
            "labelCounts": {
                "positive": 0,
                "neutral": 1,
                "negative": 0,
            },
        },
        "items": [
            {
                "articleId": 1,
                "title": "시장 뉴스",
                "source": "BBC Business",
                "url": "https://example.com/analyzed",
                "displayTimestamp": "2026-08-30T10:00:00+09:00",
                "timestampType": "published",
                "analysisStatus": "available",
                "analysis": {
                    "analysisId": 7,
                    "analysisType": "text_sentiment",
                    "analyzerName": "ProsusAI/finbert",
                    "analyzerVersion": "revision-v1",
                    "analyzedAt": "2026-08-30T01:00:00+00:00",
                    "textSentiment": "neutral",
                    "confidence": 0.8,
                    "scores": {
                        "positive": 0.1,
                        "neutral": 0.8,
                        "negative": 0.1,
                    },
                },
            },
            {
                "articleId": 2,
                "title": "Missing analysis",
                "source": "BBC Technology",
                "url": "https://example.com/missing",
                "displayTimestamp": "2026-08-30T10:00:00+09:00",
                "timestampType": "collected",
                "analysisStatus": "missing_for_selected_model",
                "analysis": None,
            },
        ],
    }


def test_serialize_sentiment_briefing_is_deterministic_and_keeps_unicode():
    briefing = make_briefing()

    first = serialize_sentiment_briefing(briefing)
    second = serialize_sentiment_briefing(briefing)

    assert first == second
    assert "시장 뉴스" in first
    assert "generatedAt" not in first
