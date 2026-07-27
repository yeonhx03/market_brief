from typing import Protocol
from market_brief.domain.models.article import Article

class ArticleRepository(Protocol):
    def save_new(self, articles: list[Article]) -> list[Article]:  # 기사 목록 저장
        ...

    def get_latest(self, limit: int) -> list[Article]:  #최신 기사 limit개 가져옴
        ...
        
    def search(self, keyword:str) -> list[Article]:
        ...

