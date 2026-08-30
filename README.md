# market_brief

RSS 금융 뉴스를 수집하고 FinBERT로 분석해 브리핑을 생성하는 Python 프로젝트입니다. 로컬에서는
SQLite를 사용하고, 통합 환경에서는 Spring Boot REST API를 통해 PostgreSQL에 저장합니다.

## 프로젝트 소개

`market_brief`는 자동매매 프로그램에서 뉴스 수집과 분석을 분리하기 위해 시작했습니다.
Python은 뉴스 수집, FinBERT 분석, 브리핑 생성을 담당하고, 별도 Spring Boot API와
PostgreSQL을 통해 React 웹과 향후 macOS/iOS 앱에 결과를 제공하는 것이 목표입니다.

## 현재 구현 상태

| 기능 | 상태 | 설명 |
| --- | --- | --- |
| RSS/Atom 뉴스 수집 | 완료 | 피드에서 기사 제목, URL, 발행 시각, 본문 요약을 수집합니다. |
| SQLite 저장 | 완료 | 수집한 기사를 저장하고 동일한 URL의 중복 저장을 방지합니다. |
| 최신 기사 조회 | 완료 | 저장된 기사를 최신순으로 조회합니다. |
| 기본 브리핑 | 완료 | 최신 기사의 제목, 출처, 시각, URL을 정해진 형식으로 출력합니다. |
| 감성 분석 결과 저장 | 완료 | 기사별 감성 점수와 분석기 정보를 별도 테이블에 저장합니다. |
| FinBERT 기사 분석 | 완료 | 실제 `ProsusAI/finbert` CPU 모델로 저장된 기사 제목을 분석하고 결과를 SQLite에 저장합니다. |
| 감성 브리핑 | 완료 | 저장된 기사와 선택한 FinBERT 리비전의 결과를 읽어 결정론적 텍스트와 JSON을 생성합니다. |
| Spring HTTP 기사·분석 저장 | 완료 | `--api-url` 통합 모드에서 Spring API를 사용하고 SQLite와 동시에 쓰지 않습니다. |
| Spring 브리핑 저장 | 완료 | 생성한 브리핑 JSON을 `POST /api/briefings`로 전송합니다. |
| React 웹 | 설계 완료 | 별도 React + TypeScript + Vite 저장소에서 읽기 전용 첫 화면을 구현할 예정입니다. |
| 관심 종목 기반 브리핑 | 예정 | 종목 및 산업 분야 설정과 관련 기사 필터링이 필요합니다. |
| LLM 기사 요약 | 예정 | 핵심 수집·분석 흐름이 완성된 후 추가할 계획입니다. |

Windows x86-64 환경에서 실제 `ProsusAI/finbert` CPU 런타임 연결, 기사 단위 분석, 저장된
분석 결과 기반 감성 브리핑까지 검증했습니다. Intel Mac에서는 Spring REST 계약과 Python
HTTP 기사·분석·브리핑 어댑터, 실제 PostgreSQL 실통신, 운영 쓰기 API 키
전달까지 검증했습니다. 다음 단계는 별도 `market_brief_web` 저장소에서 React 조회
화면을 구현하는 것입니다.

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
- PyTorch와 Transformers(선택적 FinBERT 런타임)
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

### 4. 저장된 기사 감성 분석

FinBERT 의존성은 선택 항목입니다. 분석할 때만 `finbert` extra를 활성화합니다.

```bash
uv run --extra finbert python -m market_brief analyze --limit 10
```

현재 분석 경로는 CPU를 명시적으로 사용하며 저장된 기사의 제목만 입력합니다. 같은 기사,
분석 유형, 모델 이름, 모델 리비전의 결과가 이미 있으면 새 분석 결과를 저장하지 않습니다.

### 5. 저장된 분석 결과 기반 감성 브리핑

텍스트 형식은 선택한 고정 모델 리비전의 저장 결과와 전체 확률을 표시합니다. 분석이 없는
기사는 `unavailable`로 명시하며 이 명령은 FinBERT 추론을 다시 실행하지 않습니다.

```bash
uv run python -m market_brief sentiment-briefing --limit 10
```

결정론적 JSON도 생성할 수 있습니다. `--api-url`을 함께 지정하면 같은 payload가 Spring에
저장됩니다.

```bash
uv run python -m market_brief sentiment-briefing \
  --limit 10 \
  --format json
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

### Spring 통합 모드

`--api-url`을 지정하면 해당 실행은 SQLite 대신 Spring 저장소만 사용합니다.
Spring에 설정한 값과 같은 `WRITE_API_KEY`를 Python 실행 환경에도 주입합니다.

```bash
WRITE_API_KEY="local-development-secret" \
uv run python -m market_brief collect \
  --feed-url "https://example.com/feed.xml" \
  --source "Example News" \
  --api-url "http://localhost:8080"

WRITE_API_KEY="local-development-secret" \
uv run --extra finbert python -m market_brief analyze \
  --limit 10 \
  --api-url "http://localhost:8080"

WRITE_API_KEY="local-development-secret" \
uv run python -m market_brief sentiment-briefing \
  --limit 10 \
  --api-url "http://localhost:8080"
```

키는 명령행 옵션으로 받지 않고 환경변수에서 읽습니다. HTTP 어댑터는 Spring의 상태를
바꾸는 `POST` 요청에만 `X-Market-Brief-Key` 헤더를 보내고, 공개 조회인 `GET`에는 비밀키를
보내지 않습니다. 운영에서는 키를 소스·`.env`·쉘 히스토리에 저장하지 말고 배포 환경의
secret 기능으로 주입합니다.

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
    -> TransformersFinBERTClassifier
    -> FinBERTAnalyzer
    -> ArticleAnalysis
    -> SQLiteArticleAnalysisRepository
    -> analyze CLI
```

감성 브리핑은 추론 경로와 분리되어 저장된 결과만 읽습니다.

```text
Persisted Article + ArticleAnalysis
    -> GenerateSentimentBriefingService
    -> SentimentBriefing
    -> deterministic text / persistence-ready JSON
```

장기 통합 구조는 다음과 같습니다.

```text
Python market_brief
  -> RSS collection
  -> FinBERT inference
  -> briefing generation
  -> HTTP/JSON
Spring Boot market_brief_api
  -> validation / duplicate handling / REST API
  -> PostgreSQL
  -> React web over HTTPS
  -> future macOS/iOS Swift clients
```

SQLite는 로컬·오프라인 어댑터로 유지합니다. 통합 실행에서는 Python이 PostgreSQL에 직접
접속하지 않고 Spring Boot API를 사용하며 SQLite와 PostgreSQL에 암묵적으로 동시에 쓰지
않습니다.

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

`TransformersFinBERTClassifier`는 실제 `ProsusAI/finbert` 모델을 CPU에서 실행하고,
`FinBERTAnalyzer`는 그 분류 결과를 애플리케이션의 `ArticleAnalysis`로 변환합니다.

- 기사 제목만 분석 입력으로 사용
- 최대 입력 길이 512와 명시적 truncation 적용
- `positive`, `neutral`, `negative` 레이블 검증
- 각 점수의 범위와 전체 합계 검증
- 가장 높은 점수를 기사 감성으로 선택
- 모델 이름과 고정 리비전을 분석 결과와 함께 SQLite에 저장
- 같은 모델 리비전의 중복 분석 결과 저장 방지
- 비분석 명령에서는 PyTorch와 Transformers를 로드하지 않도록 지연 import 유지

현재 고정 모델 리비전은 `4556d13015211d73dccd3fdd39d39232506f3e43`입니다. FinBERT 감성은
금융 문장의 정서 분류이며 주가 영향 예측이나 매수·매도 신호가 아닙니다.

## 감성 브리핑

`sentiment-briefing`은 기존 `briefing`과 별도 모델 및 서비스로 동작합니다.

- 저장된 기사와 `ArticleAnalysis`만 조회
- `analysis_type`, 모델 이름, 고정 리비전이 모두 일치하는 결과 선택
- 같은 분석 결과가 여러 개면 분석 시각과 저장 ID로 결정적으로 선택
- 선택한 리비전의 분석이 없으면 명시적인 미분석 상태 제공
- 텍스트에서는 읽기 좋은 백분율, JSON에서는 저장된 원래 확률 유지
- JSON에 실행 시각을 넣지 않아 같은 저장 데이터에서 동일한 결과 유지
- 감성을 주가 방향이나 거래 신호로 표현하지 않음


## 향후 계획

1. 로컬 PostgreSQL에서 Python과 Spring의 전체 실통신 검증
2. Spring 운영 설정, 쓰기 API 보호, CORS와 상태 확인
3. 별도 React + TypeScript + Vite 웹 구현
4. 웹, Spring, PostgreSQL 공개 배포와 Python 정기 실행
5. macOS/iOS SwiftUI 앱 구현
6. 초기 공개 범위 이후 확장 기능 재검토

## 프로젝트 문서

- [`AGENTS.md`](AGENTS.md): Codex와 작업할 때 지켜야 할 저장소 규칙
- [`docs/architecture.md`](docs/architecture.md): 시스템 책임과 장기 아키텍처
- [`docs/workflow.md`](docs/workflow.md): 현재 단계, 완료 상태, 다음 작업
- [`docs/windows-handoff.md`](docs/windows-handoff.md): 임시 Windows FinBERT 작업 인계서
