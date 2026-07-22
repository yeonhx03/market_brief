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
    content_hash: str | None = None #중복방지
