from datetime import datetime, timezone

from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.domain.models.sentiment_briefing import (
    SentimentBriefing,
    SentimentBriefingItem,
)


def test_sentiment_briefing_keeps_selected_analysis_identity_and_items():
    timestamp = datetime(2026, 8, 30, 8, 2, 28, tzinfo=timezone.utc)
    analysis = ArticleAnalysis(
        id=7,
        article_id=36,
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        analyzed_at=datetime(2026, 8, 30, 9, 0, tzinfo=timezone.utc),
        text_sentiment="neutral",
        positive_score=0.08,
        neutral_score=0.89,
        negative_score=0.03,
        confidence=0.89,
    )
    item = SentimentBriefingItem(
        article_id=36,
        title="Games industry update",
        source="BBC Technology",
        url="https://example.com/games",
        timestamp=timestamp,
        timestamp_label="Published",
        analysis=analysis,
    )

    result = SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(item,),
    )

    assert result.analysis_type == "text_sentiment"
    assert result.analyzer_name == "ProsusAI/finbert"
    assert result.analyzer_version == "revision-v1"
    assert result.items == (item,)
    assert result.items[0].analysis is analysis


def test_sentiment_briefing_item_represents_missing_analysis_explicitly():
    item = SentimentBriefingItem(
        article_id=52,
        title="Article without selected analysis",
        source="BBC Business",
        url="https://example.com/missing",
        timestamp=datetime(2026, 8, 29, 18, 0, tzinfo=timezone.utc),
        timestamp_label="Collected",
        analysis=None,
    )

    result = SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(item,),
    )

    assert result.items[0].analysis is None


def test_sentiment_briefing_can_be_empty():
    result = SentimentBriefing(
        analysis_type="text_sentiment",
        analyzer_name="ProsusAI/finbert",
        analyzer_version="revision-v1",
        items=(),
    )

    assert result.items == ()
