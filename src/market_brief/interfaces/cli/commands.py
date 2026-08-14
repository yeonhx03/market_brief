import argparse
import asyncio

from market_brief.bootstrap import build_collect_news_service
from market_brief.bootstrap import build_get_latest_articles_service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="market_brief",
        description="Collect and view market news.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    collect_parser = subparsers.add_parser(
        "collect",
        help="Collect articles from an RSS feed.",
    )
    collect_parser.add_argument(
        "--feed-url",
        required=True,
        help="RSS feed URL.",
    )
    collect_parser.add_argument(
        "--source",
        required=True,
        help="News source name.",
    )
    collect_parser.add_argument(
        "--db-path",
        default="data/market_brief.db",
        help="SQLite database path.",
    )
    latest_parser = subparsers.add_parser(
        "latest",
        help="Show the latest saved articles.",
    )
    latest_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of articles to show.",
    )
    latest_parser.add_argument(
        "--db-path",
        default="data/market_brief.db",
        help="SQLite database path.",
    )
    return parser


def run_collect(args: argparse.Namespace) -> None:
    service = build_collect_news_service(
        feed_url=args.feed_url,
        source=args.source,
        db_path=args.db_path,
    )

    saved_articles = asyncio.run(service.execute())

    print(f"Saved {len(saved_articles)} new articles.")


def run_latest(args: argparse.Namespace) -> None:
    service = build_get_latest_articles_service(
        db_path=args.db_path,
    )
    articles = service.execute(limit=args.limit)

    if not articles:
        print("No articles found.")
        return

    for index, article in enumerate(articles, start=1):
        timestamp = article.published_at or article.collected_at

        print(f"{index}. {article.title}")
        print(f"   {article.source} | {timestamp.isoformat()}")
        print(f"   {article.url}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "collect":
        run_collect(args)
    elif args.command == "latest":
        run_latest(args)