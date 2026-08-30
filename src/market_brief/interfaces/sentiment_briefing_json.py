import json
from datetime import timezone

from market_brief.domain.models.article_analysis import ArticleAnalysis
from market_brief.domain.models.sentiment_briefing import (
    SentimentBriefing,
    SentimentBriefingItem,
)


def serialize_sentiment_briefing(
    briefing: SentimentBriefing,
) -> str:
    label_counts = {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
    }
    analyzed_count = 0

    for item in briefing.items:
        if item.analysis is not None:
            analyzed_count += 1
            label_counts[item.analysis.text_sentiment] += 1

    payload = {
        "schemaVersion": 1,
        "briefingType": briefing.analysis_type,
        "analysisSelector": {
            "analysisType": briefing.analysis_type,
            "analyzerName": briefing.analyzer_name,
            "analyzerVersion": briefing.analyzer_version,
        },
        "summary": {
            "articleCount": len(briefing.items),
            "analyzedCount": analyzed_count,
            "missingAnalysisCount": len(briefing.items) - analyzed_count,
            "labelCounts": label_counts,
        },
        "items": [
            _item_to_dict(item)
            for item in briefing.items
        ],
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def _item_to_dict(
    item: SentimentBriefingItem,
) -> dict[str, object]:
    if item.analysis is None:
        analysis_status = "missing_for_selected_model"
        analysis_payload = None
    else:
        analysis_status = "available"
        analysis_payload = _analysis_to_dict(item.analysis)

    return {
        "articleId": item.article_id,
        "title": item.title,
        "source": item.source,
        "url": item.url,
        "displayTimestamp": item.timestamp.isoformat(),
        "timestampType": item.timestamp_label.lower(),
        "analysisStatus": analysis_status,
        "analysis": analysis_payload,
    }


def _analysis_to_dict(
    analysis: ArticleAnalysis,
) -> dict[str, object]:
    return {
        "analysisId": analysis.id,
        "analysisType": analysis.analysis_type,
        "analyzerName": analysis.analyzer_name,
        "analyzerVersion": analysis.analyzer_version,
        "analyzedAt": (
            analysis.analyzed_at
            .astimezone(timezone.utc)
            .isoformat()
        ),
        "textSentiment": analysis.text_sentiment,
        "confidence": analysis.confidence,
        "scores": {
            "positive": analysis.positive_score,
            "neutral": analysis.neutral_score,
            "negative": analysis.negative_score,
        },
    }