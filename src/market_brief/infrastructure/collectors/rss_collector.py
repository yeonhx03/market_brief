from datetime import datetime, timezone # collected_at, published_at

import feedparser #RSS/Atom 데이터 파싱
import httpx

from market_brief.domain.models.article import Article


class RSSCollector:
    def __init__(self, feed_url: str, source: str) -> None:
        self.feed_url = feed_url
        self.source = source

    async def fetch(self) -> list[Article]:
        # 1. RSS URL로 HTTP 요청
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 2. 응답 XML 받기
            response = await client.get(self.feed_url)
            response.raise_for_status()

        # 3. feedparser로 RSS 파싱
        feed = feedparser.parse(response.text)
        collected_at = datetime.now(timezone.utc)

        # 4. entry들을 Article로 변환
        articles: list[Article] = [] #변환한 것 저장할 리스트

        for entry in feed.entries:
            title = (entry.get("title") or "").strip()
            url = (entry.get("link") or "").strip()

            if not title or not url:  #title이나 url 없으면 데이터 저장 패스하게 early continue
                continue

            published_at = self._parse_published_at(entry)
            raw_content = entry.get("summary") or entry.get("description")

            article = Article(
                title=title,
                url=url,
                source = self.source,
                published_at=published_at,
                collected_at=collected_at,
                raw_content=raw_content,
            )

            articles.append(article)

        return articles  # 5. list Article 반환
    
    def _parse_published_at(self , entry) -> datetime | None:
        published_parsed = entry.get("published_parsed")

        if not published_parsed:
            return None

        return datetime(*published_parsed[:6], tzinfo=timezone.utc)
    