# market_brief

RSS 금융 뉴스를 수집해 SQLite에 저장하고, 감성 분석과 개인화 브리핑으로 확장하는 Python CLI 프로젝트로, 현재 개발 중입니다.

## 프로젝트 소개

`market_brief`는 자동매매 프로그램에서 뉴스 수집과 분석을 분리하기 위해 시작했습니다.
이 프로젝트는 뉴스 데이터를 수집하고 분석 결과를 저장하는 역할로, 이후 자동매매 프로그램이 필요할 때 해당 데이터를 가져가도록 만드는 것이 목표입니다.

## 현재 구현 상태

| 기능 | 상태 | 설명 |
| --- | --- | --- |
| RSS/Atom 뉴스 수집 | 완료 | 피드에서 기사 제목, URL, 발행 시각, 본문 요약을 수집합니다. |
| SQLite 저장 | 완료 | 수집한 기사를 저장하고 동일한 URL의 중복 저장을 방지합니다. |
| 최신 기사 조회 | 완료 | 저장된 기사를 최신순으로 조회합니다. |
| 기본 브리핑 | 완료 | 최신 기사의 제목, 출처, 시각, URL을 정해진 형식으로 출력합니다. |
| 감성 분석 결과 저장 | 완료 | 기사별 감성 점수와 분석기 정보를 별도 테이블에 저장합니다. |
| FinBERT 분석 어댑터 | 부분 구현 | 분류 결과의 변환과 검증은 구현했지만 실제 모델은 아직 연결하지 않았습니다. |
| 관심 종목 기반 브리핑 | 예정 | 종목 및 산업 분야 설정과 관련 기사 필터링이 필요합니다. |
| LLM 기사 요약 | 예정 | 핵심 수집·분석 흐름이 완성된 후 추가할 계획입니다. |

현재 `briefing` 명령은 AI로 기사를 요약하지 않습니다. 저장된 최신 기사를 서울 시간 기준으로 정리하는 결정론적 브리핑입니다.

## 주요 기능

### 뉴스 수집

- `httpx`를 이용한 비동기 RSS 요청
- `feedparser`를 이용한 RSS/Atom 파싱
- 필수 데이터가 없는 항목 제외
- 기사 URL을 기준으로 중복 저장 방지

### 기사 저장 및 조회

- 별도 서버 없이 사용할 수 있는 SQLite 저장소
- RSS가 제공하는 기사 요약 또는 본문 데이터와 수집·발행 시각 저장
- 발행 시각 또는 수집 시각을 기준으로 최신 기사 조회

### 감성 분석 기반

- 기사 단위 `positive`, `neutral`, `negative` 점수 표현
- 점수 범위와 합계 검증
- 분석 모델 이름과 버전 기록
- 기사와 분석 결과를 분리해 저장

## 기술 스택

- Python 3.11+
- httpx
- feedparser
- SQLite
- pytest
- Ruff
- uv


## 사용법

### 1. 뉴스 수집

수집할 RSS 주소와 출처 이름을 지정합니다.

```bash
uv run python -m market_brief collect \
  --feed-url "https://example.com/feed.xml" \
  --source "Example News"
```

기본 데이터베이스 경로는 `data/market_brief.db`입니다.

### 2. 최신 기사 조회

```bash
uv run python -m market_brief latest --limit 10
```

### 3. 브리핑 조회

```bash
uv run python -m market_brief briefing --limit 10
```

다른 데이터베이스 파일을 사용하려면 `--db-path` 옵션을 추가합니다.

```bash
uv run python -m market_brief latest \
  --limit 5 \
  --db-path data/custom.db
```

전체 명령은 도움말에서 확인할 수 있습니다.

```bash
uv run python -m market_brief --help
```

## 처리 흐름

```text
RSS/Atom feed
    -> RSSCollector
    -> Article
    -> SQLiteArticleRepository
    -> latest / briefing CLI
```

감성 분석은 기사 저장 이후 별도의 흐름으로 동작하도록 분리했습니다.

```text
Persisted Article
    -> TextSentimentAnalyzer
    -> ArticleAnalysis
    -> SQLiteArticleAnalysisRepository
```

## 프로젝트 구조

```text
src/market_brief/
├── domain/          # 기사, 분석 결과, 브리핑 모델
├── application/     # 유스케이스와 포트 인터페이스
├── infrastructure/  # RSS, SQLite, 감성 분석 어댑터
└── interfaces/      # CLI 입력과 출력
```

도메인 로직이 RSS, SQLite, AI 모델 같은 외부 기술에 직접 의존하지 않도록 Ports and Adapters 구조를 적용했습니다. 수집기, 저장소, 분석기를 인터페이스 뒤에 두어 테스트에서 대체 구현을 주입할 수 있습니다.

## 감성 분석

현재 `FinBERTAnalyzer`는 외부에서 주입받은 분류 결과를 애플리케이션의 `ArticleAnalysis`로 변환합니다.

- 기사 제목과 본문을 하나의 분석 입력으로 구성
- `positive`, `neutral`, `negative` 레이블 검증
- 각 점수의 범위와 전체 합계 검증
- 가장 높은 점수를 기사 감성으로 선택
- 분석 결과와 모델 정보를 SQLite에 저장

현재는 사전 학습된 FinBERT 모델을 사용하지 않고, `FinBERTAnalyzer`에 `fake_classifier`를 주입해 테스트하고 있습니다.


## 향후 계획

1. 실제 사전 학습 FinBERT 모델 연결
2. 저장된 기사를 분석하는 `analyze` CLI 명령 추가
3. 기사별 감성 결과를 종목과 기간 단위로 집계
4. 관심 종목과 산업 분야 설정 기능 추가
5. 동명이의어를 구분하는 기업·산업 관련성 판별
6. LLM 기반 기사 요약 추가
7. 자동매매 프로그램에서 분석 데이터를 조회할 수 있는 인터페이스 제공
