from collections.abc import Callable
from datetime import datetime
from math import isclose

from market_brief.domain.models.article import Article
from market_brief.domain.models.article_analysis import ArticleAnalysis


ClassifierResult = dict[str, str | float]
Classifier = Callable[[str], list[ClassifierResult]]
Clock = Callable[[], datetime]


class FinBERTAnalyzer:
    def __init__(
        self,
        classifier: Classifier,
        analyzer_name: str,
        analyzer_version: str,
        clock: Clock,
    ) -> None:
        self.classifier = classifier
        self.analyzer_name = analyzer_name
        self.analyzer_version = analyzer_version
        self.clock = clock

    def analyze(self, article: Article) -> ArticleAnalysis:
        if article.id is None:
            raise ValueError("article must be persisted before analysis")

        content = article.cleaned_content or article.raw_content
        text = article.title

        if content:
            text = f"{article.title}\n\n{content}"

        response = self.classifier(text)

        scores = {
            str(item["label"]).lower(): float(item["score"])
            for item in response
        }

        expected_labels = {
            "positive",
            "neutral",
            "negative",
        }

        # score 범위 검증
        if (
            len(response) != len(expected_labels)
            or set(scores) != expected_labels
        ):
            raise ValueError(
                "classifier must return exactly three sentiment labels"
            )

        if not all(
            0.0 <= score <= 1.0
            for score in scores.values()
        ):
            raise ValueError(
                "sentiment scores must be between 0 and 1"
            )

        text_sentiment = max(
            ("positive", "neutral", "negative"),
            key=lambda label: scores[label],
        )

        # 확률 합 검증
        if not isclose(
            sum(scores.values()),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-6,
        ):
            raise ValueError("sentiment scores must sum to 1")

        return ArticleAnalysis(
            article_id=article.id,
            analysis_type="text_sentiment",
            analyzer_name=self.analyzer_name,
            analyzer_version=self.analyzer_version,
            analyzed_at=self.clock(),
            text_sentiment=text_sentiment,
            positive_score=scores["positive"],
            neutral_score=scores["neutral"],
            negative_score=scores["negative"],
            confidence=scores[text_sentiment],
        )
