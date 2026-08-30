import sys
from types import ModuleType

from market_brief.infrastructure.analyzers.finbert_analyzer import (
    ClassifierResult,
)
from market_brief.infrastructure.analyzers.transformers_finbert_classifier import (
    DEFAULT_MAX_LENGTH,
    TransformersFinBERTClassifier,
)


class FakeTextClassificationPipeline:
    def __init__(self, results: list[ClassifierResult]) -> None:
        self.results = results
        self.calls: list[dict[str, str | bool | int | None]] = []

    def __call__(
        self,
        text: str,
        *,
        top_k: None,
        truncation: bool,
        max_length: int,
    ) -> list[ClassifierResult]:
        self.calls.append(
            {
                "text": text,
                "top_k": top_k,
                "truncation": truncation,
                "max_length": max_length,
            }
        )
        return self.results


def test_classifier_requests_all_labels_with_explicit_truncation():
    expected_results: list[ClassifierResult] = [
        {"label": "positive", "score": 0.7},
        {"label": "neutral", "score": 0.2},
        {"label": "negative", "score": 0.1},
    ]
    pipeline = FakeTextClassificationPipeline(expected_results)
    classifier = TransformersFinBERTClassifier(pipeline)

    results = classifier("Company reports record profits.")

    assert results == expected_results
    assert pipeline.calls == [
        {
            "text": "Company reports record profits.",
            "top_k": None,
            "truncation": True,
            "max_length": DEFAULT_MAX_LENGTH,
        }
    ]


def test_classifier_uses_configured_max_length():
    pipeline = FakeTextClassificationPipeline([])
    classifier = TransformersFinBERTClassifier(
        pipeline,
        max_length=128,
    )

    classifier("Short headline")

    assert pipeline.calls[0]["max_length"] == 128


def test_from_pretrained_builds_cpu_pipeline_with_pinned_revision(
    monkeypatch,
):
    calls: dict[str, object] = {}
    tokenizer = object()

    class FakeModel:
        def to(self, device: str) -> None:
            calls["model_device"] = device

        def eval(self) -> None:
            calls["model_eval"] = True

    model = FakeModel()

    class FakeAutoTokenizer:
        @classmethod
        def from_pretrained(
            cls,
            model_name: str,
            *,
            revision: str,
        ) -> object:
            calls["tokenizer"] = {
                "model_name": model_name,
                "revision": revision,
            }
            return tokenizer

    class FakeAutoModelForSequenceClassification:
        @classmethod
        def from_pretrained(
            cls,
            model_name: str,
            *,
            revision: str,
            use_safetensors: bool,
        ) -> FakeModel:
            calls["model"] = {
                "model_name": model_name,
                "revision": revision,
                "use_safetensors": use_safetensors,
            }
            return model

    pipeline = FakeTextClassificationPipeline([])

    def fake_pipeline(**kwargs: object) -> FakeTextClassificationPipeline:
        calls["pipeline"] = kwargs
        return pipeline

    transformers = ModuleType("transformers")
    transformers.AutoTokenizer = FakeAutoTokenizer
    transformers.AutoModelForSequenceClassification = (
        FakeAutoModelForSequenceClassification
    )
    transformers.pipeline = fake_pipeline
    monkeypatch.setitem(sys.modules, "transformers", transformers)

    classifier = TransformersFinBERTClassifier.from_pretrained(
        model_name="test-model",
        revision="test-revision",
        max_length=128,
    )

    assert calls["tokenizer"] == {
        "model_name": "test-model",
        "revision": "test-revision",
    }
    assert calls["model"] == {
        "model_name": "test-model",
        "revision": "test-revision",
        "use_safetensors": False,
    }
    assert calls["model_device"] == "cpu"
    assert calls["model_eval"] is True
    assert calls["pipeline"] == {
        "task": "text-classification",
        "model": model,
        "tokenizer": tokenizer,
        "device": -1,
    }
    assert classifier.classifier is pipeline
    assert classifier.max_length == 128
