from datetime import timezone

from market_brief.application.services.analyze_article import (
    AnalyzeArticleService,
)
from market_brief.bootstrap import build_analyze_article_service
from market_brief.infrastructure.analyzers.finbert_analyzer import (
    FinBERTAnalyzer,
)
from market_brief.infrastructure.analyzers.transformers_finbert_classifier import (
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_REVISION,
    TransformersFinBERTClassifier,
)
from market_brief.infrastructure.repositories.sqlite_article_analysis_repository import (
    SQLiteArticleAnalysisRepository,
)


def test_build_analyze_article_service_wires_real_adapter_types(
    tmp_path,
    monkeypatch,
):
    loader_calls: list[None] = []

    def fake_classifier(text: str):
        raise AssertionError(f"classifier should not run while wiring: {text}")

    def fake_from_pretrained(cls):
        loader_calls.append(None)
        return fake_classifier

    monkeypatch.setattr(
        TransformersFinBERTClassifier,
        "from_pretrained",
        classmethod(fake_from_pretrained),
    )
    db_path = tmp_path / "market_brief.db"

    service = build_analyze_article_service(db_path)

    assert loader_calls == [None]
    assert isinstance(service, AnalyzeArticleService)
    assert isinstance(service.analyzer, FinBERTAnalyzer)
    assert service.analyzer.classifier is fake_classifier
    assert service.analyzer.analyzer_name == DEFAULT_MODEL_NAME
    assert service.analyzer.analyzer_version == DEFAULT_MODEL_REVISION
    assert service.analyzer.clock().tzinfo == timezone.utc
    assert isinstance(service.repository, SQLiteArticleAnalysisRepository)
    assert service.repository.db_path == db_path
