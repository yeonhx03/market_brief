from typing import Protocol

from market_brief.infrastructure.analyzers.finbert_analyzer import ClassifierResult


DEFAULT_MODEL_NAME = "ProsusAI/finbert"
DEFAULT_MODEL_REVISION = "4556d13015211d73dccd3fdd39d39232506f3e43"
DEFAULT_MAX_LENGTH = 512


class TextClassificationPipeline(Protocol):
    def __call__(
            self,
            text: str,
            *,
            top_k: None,
            truncation: bool,
            max_length: int,
    ) -> list[ClassifierResult]:
        ...


class TransformersFinBERTClassifier:
    def __init__(
            self,
            classifier: TextClassificationPipeline,
            max_length: int = DEFAULT_MAX_LENGTH,
    ) -> None:
        self.classifier = classifier
        self.max_length = max_length

    @classmethod
    def from_pretrained(
            cls,
            model_name: str = DEFAULT_MODEL_NAME,
            revision: str = DEFAULT_MODEL_REVISION,
            max_length: int = DEFAULT_MAX_LENGTH,
    ) -> "TransformersFinBERTClassifier":
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            pipeline,
        )

        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            revision=revision,
            )
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            revision=revision,
            use_safetensors=False,
        )
        model.to("cpu")
        model.eval()

        classifier = pipeline(
            task="text-classification",
            model=model,
            tokenizer=tokenizer,
            device=-1,
        )

        return cls(
            classifier=classifier,
            max_length=max_length,
        )

    def __call__(self, text: str) -> list[ClassifierResult]:
        return self.classifier(
            text,
            top_k=None,
            truncation=True,
            max_length=self.max_length,
        )

        