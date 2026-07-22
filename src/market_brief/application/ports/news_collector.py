from typing import Protocol #표준 라이브러리

from market_brief.domain.models.article import Article #Article class 가져오기

class NewsCollector(Protocol):
    async def fetch(self) -> list[Article]:
        ...