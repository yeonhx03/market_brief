# 금융 뉴스 브리핑 Market Brief

## 프로젝트 소개

- Market Brief는 RSS 금융 뉴스를 수집하고 FinBERT로 분석해 브리핑을 생성하는 프로젝트입니다.
- 자동매매 프로그램에서 뉴스 수집과 분석을 분리하기 위해 제작했습니다.
- 로컬에서는 SQLite에 저장하고, 통합 환경에서는 Spring Boot REST API를 통해 PostgreSQL에 저장합니다.
- FinBERT 분석 결과는 금융 문장의 감성이며 주가 영향 예측이나 매수·매도 신호가 아닙니다.


## 개발 환경

- Core: Python 3.11, httpx, feedparser
- AI: PyTorch, Transformers, ProsusAI/finbert
- Storage: SQLite, Spring Boot REST API, PostgreSQL
- Test: pytest, Ruff
- Package Manager: uv


## 기능별 소개

### [뉴스 수집]

- RSS/Atom 피드에서 기사 제목, URL, 발행 시각, 본문 요약을 수집합니다.
- 필수 데이터가 없는 항목은 제외하고, 기사 URL을 기준으로 중복 저장을 방지합니다.


### [기사 저장 및 조회]

- 로컬 환경에서는 SQLite에 기사를 저장합니다.
- 통합 환경에서는 Spring Boot REST API를 통해 PostgreSQL에 저장하고 최신 기사를 조회합니다.
- 사용자가 종목을 지정하면 수집한 기사와 해당 종목을 연결합니다.


### [감성 분석]

- 저장된 기사 제목을 FinBERT로 분석합니다.
- `positive`, `neutral`, `negative` 점수와 분석 모델 정보를 저장합니다.
- 같은 기사와 모델 버전의 분석 결과는 중복 저장하지 않습니다.


### [브리핑]

- 최신 기사의 제목, 출처, 시각, URL을 정해진 형식으로 생성합니다.
- 모델 사용 여부와 관계없이 같은 저장 데이터에서 동일한 결과를 생성합니다.


### [감성 브리핑]

- 저장된 기사와 FinBERT 분석 결과를 읽어 텍스트 또는 JSON 브리핑을 생성합니다.
- 분석 결과가 없는 기사는 미분석 상태로 표시합니다.
- 통합 환경에서는 생성한 브리핑을 Spring Boot REST API에 저장합니다.
