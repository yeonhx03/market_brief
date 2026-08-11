import logging
from datetime import datetime, timezone  # collected_at, published_at

import feedparser  # RSS/Atom 데이터 파싱
import httpx

from market_brief.domain.models.article import Article


logger = logging.getLogger(__name__)


class RSSCollector:
    def __init__(self, feed_url: str, source: str) -> None:
        self.feed_url = feed_url
        self.source = source

    async def fetch(self) -> list[Article]:
        # 수집 시작 로그
        logger.info(
            "RSS collection started: source=%s url=%s",
            self.source,
            self.feed_url,
        )
        try:
            # 1. RSS URL로 HTTP 요청
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 2. 응답 XML 받기
                response = await client.get(self.feed_url)
                response.raise_for_status()
        except httpx.RequestError as exc:  # 예외객체를 exc 변수로 받음
            logger.error(
                "RSS request failed: source=%s url=%s error=%s",
                self.source,
                self.feed_url,
                exc,
            )
            return []  # 수집된 기사 없음
        except httpx.HTTPStatusError as exc:
            logger.error(
                "RSS HTTP status error: source=%s url=%s status_code=%d",
                self.source,
                self.feed_url,
                exc.response.status_code,
            )
            return []
        # 3. feedparser로 RSS 파싱
        feed = feedparser.parse(response.content)

        if feed.bozo:  # feed.bozo 값이 1이면 파싱 문제 생긴 것
            logger.warning(
                "RSS parsing warning: source=%s url=%s error=%s",
                self.source,
                self.feed_url,
                feed.bozo_exception,
            )

        collected_at = datetime.now(timezone.utc)

        # 4. entry들을 Article로 변환
        articles: list[Article] = []  # 변환한 것 저장할 리스트

        for entry_index, entry in enumerate(feed.entries, start=1):
            try:
                title = (entry.get("title") or "").strip()
                url = (entry.get("link") or "").strip()

                # title이나 URL이 없으면 저장하지 않고 다음 기사로 이동
                if not title or not url:
                    logger.warning(
                        "Skipped RSS entry without required fields: source=%s title=%r url=%r",
                        self.source,
                        title,
                        url,
                    )
                    continue

                published_at = self._parse_published_at(entry)
                raw_content = entry.get("summary") or entry.get("description")

                article = Article(
                    title=title,
                    url=url,
                    source=self.source,
                    published_at=published_at,
                    collected_at=collected_at,
                    raw_content=raw_content,
                )

                articles.append(article)

            except (AttributeError, TypeError, ValueError) as exc:
                logger.warning(
                    "Skipped invalid RSS entry: source=%s entry_index=%d error=%s",
                    self.source,
                    entry_index,
                    exc,
                )
                continue

        logger.info(
            "RSS collection completed: source=%s articles=%d",
            self.source,
            len(articles),
        )

        return articles  # 5. list Article 반환

    def _parse_published_at(self, entry) -> datetime | None:
        published_parsed = entry.get("published_parsed")

        if not published_parsed:
            return None
        try:
            return datetime(*published_parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError, OverflowError) as exc:
            logger.warning(
                "Invalid RSS published date: source=%s article_url=%s value=%r error=%s",
                self.source,
                entry.get("link"),
                published_parsed,
                exc,
            )
            return None
