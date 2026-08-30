import argparse
import asyncio
from market_brief.bootstrap import (
    build_generate_sentiment_briefing_service,
)
from market_brief.bootstrap import build_collect_news_service
from market_brief.bootstrap import build_analyze_article_service
from market_brief.bootstrap import build_get_latest_articles_service
from market_brief.bootstrap import build_generate_briefing_service

from market_brief.interfaces.sentiment_briefing_json import (
    serialize_sentiment_briefing,
)


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

    briefing_parser = subparsers.add_parser(
    "briefing",
    help="Generate a briefing from the latest saved articles.",
    )
    briefing_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of articles to include.",
    )
    briefing_parser.add_argument(
        "--db-path",
        default="data/market_brief.db",
        help="SQLite database path.",
    )

    sentiment_briefing_parser = subparsers.add_parser(
        "sentiment-briefing",
        help="Generate a briefing from stored sentiment analyses.",
    )
    sentiment_briefing_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of articles to include.",
    )
    sentiment_briefing_parser.add_argument(
        "--db-path",
        default="data/market_brief.db",
        help="SQLite database path.",
    )
    sentiment_briefing_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze saved articles with FinBERT.",
    )
    analyze_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of articles to analyze.",
    )
    analyze_parser.add_argument(
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


def run_briefing(args: argparse.Namespace) -> None:
    service = build_generate_briefing_service(
        db_path=args.db_path,
    )
    briefing = service.execute(limit=args.limit)

    if not briefing.items:
        print("No articles found.")
        return

    for index, item in enumerate(briefing.items, start=1):
        print(f"{index}. {item.title}")
        print(
            f"   {item.source} | "
            f"{item.timestamp_label}: {item.timestamp.isoformat()}"
        )
        print(f"   {item.url}")


def run_sentiment_briefing(args: argparse.Namespace) -> None:
    service = build_generate_sentiment_briefing_service(
        db_path=args.db_path,
    )
    briefing = service.execute(limit=args.limit)

    if args.format == "json":
        print(serialize_sentiment_briefing(briefing))
        return

    if not briefing.items:
        print("No articles found.")
        return

    print("Sentiment Briefing")
    print(f"Model: {briefing.analyzer_name}")
    print(f"Revision: {briefing.analyzer_version}")
    print(
        "Note: Sentiment describes headline language, "
        "not price direction or a trading signal."
    )
    print()

    for index, item in enumerate(briefing.items, start=1):
        print(f"{index}. {item.title}")
        print(
            f"   {item.source} | "
            f"{item.timestamp_label}: {item.timestamp.isoformat()}"
        )

        if item.analysis is None:
            print("   Text sentiment: unavailable")
            print(
                "   No stored analysis for the selected model revision."
            )
        else:
            analysis = item.analysis
            print(
                f"   Text sentiment: {analysis.text_sentiment} | "
                f"Confidence: {analysis.confidence:.2%}"
            )
            print(
                "   Probabilities: "
                f"positive {analysis.positive_score:.2%} | "
                f"neutral {analysis.neutral_score:.2%} | "
                f"negative {analysis.negative_score:.2%}"
            )

        print(f"   {item.url}")


def run_analyze(args: argparse.Namespace) -> None:
    article_service = build_get_latest_articles_service(
        db_path=args.db_path,
    )
    articles = article_service.execute(limit=args.limit)

    if not articles:
        print("No articles found.")
        return

    analysis_service = build_analyze_article_service(
        db_path=args.db_path,
    )

    analyzed_count = 0
    skipped_count = 0

    for article in articles:
        result = analysis_service.execute(article)

        if result is None:
            skipped_count += 1
        else:
            analyzed_count += 1

    print(
        f"Analyzed {analyzed_count} articles. "
        f"Skipped {skipped_count} existing analyses."
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "collect":
        run_collect(args)
    elif args.command == "latest":
        run_latest(args)
    elif args.command == "briefing":
        run_briefing(args)
    elif args.command == "sentiment-briefing":
        run_sentiment_briefing(args)
    elif args.command == "analyze":
        run_analyze(args)