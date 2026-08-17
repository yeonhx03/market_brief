from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Article:
    title: str
    url: str
    source: str
    published_at: datetime | None
    collected_at: datetime 
    raw_content: str | None = None #넘어오는 raw data
    cleaned_content: str | None = None #가공
    content_hash: str | None = None #기사 내용 중복방지 
    source_article_id: str | None = None # 언론사에서 부여한 기사 고유번호, 중복방지용
    canonical_url: str | None = None # 정규화 한 대표 URL, 중복방지용
    id: int | None = None