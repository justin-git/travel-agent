"""CLI entry point – run the Travel Deal Radar agent once.

Usage:
    uv run python main.py              # full run (search → scrape → telegram)
    uv run python main.py --dry-run    # skip Telegram send, print to stdout
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from google.adk.runners import InMemoryRunner
from google.genai import types

from agent import root_agent
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("travel_deal_radar")


async def run_agent(dry_run: bool = False) -> None:
    """Execute the agent with a single triggering message."""

    # The triggering prompt tells the agent to begin its workflow
    trigger = (
        f"請開始執行今日的香港機票快閃優惠搜尋任務。"
        f"搜尋關鍵字：「{settings.search_query}」。"
        f"最大爬取深度：{settings.max_crawl_depth} 層。"
    )
    if dry_run:
        trigger += "\n⚠️ 這是乾跑模式（dry-run）。請不要實際發送 Telegram 訊息，而是把最終訊息內容直接輸出在回覆中。"

    runner = InMemoryRunner(
        agent=root_agent,
        app_name="travel_deal_radar",
    )

    user_id = "system"
    session = await runner.session_service.create_session(
        app_name="travel_deal_radar",
        user_id=user_id,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=trigger)],
    )

    logger.info("🚀 Starting Travel Deal Radar agent...")
    logger.info("   Search query: %s", settings.search_query)
    logger.info("   Max crawl depth: %d", settings.max_crawl_depth)
    logger.info("   Dry run: %s", dry_run)

    final_response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=user_message,
    ):
        # Collect the agent's final text response
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text
                if hasattr(part, "function_call") and part.function_call:
                    logger.info(
                        "  🔧 Tool call: %s", part.function_call.name
                    )

    if final_response:
        logger.info("✅ Agent completed.")
        if dry_run:
            print("\n" + "=" * 60)
            print("📋 DRY RUN OUTPUT:")
            print("=" * 60)
            print(final_response)
    else:
        logger.warning("⚠️ Agent produced no text response.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Travel Deal Radar – Hong Kong flight deal scout"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without sending Telegram messages; print output to stdout.",
    )
    args = parser.parse_args()

    # Validate credentials
    if not settings.google_api_key:
        logger.error("❌ GOOGLE_API_KEY not set. Please configure .env")
        sys.exit(1)

    if not args.dry_run:
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.error(
                "❌ TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set. "
                "Use --dry-run or configure .env"
            )
            sys.exit(1)

    asyncio.run(run_agent(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
