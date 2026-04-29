"""Root ADK agent definition for Travel Deal Radar.

This module exposes ``root_agent`` which is the standard ADK entry point.
The agent uses:
  - Google Search (built-in Gemini tool) for discovering deal URLs
  - scrape_page (Playwright) for deep web content extraction
  - send_telegram_message for broadcasting the digest
"""

from google.adk import Agent
from google.adk.tools import google_search

from config import settings
from prompts.system_prompt import SYSTEM_PROMPT
from tools.scrape_tool import scrape_page
from tools.telegram_tool import send_telegram_message

root_agent = Agent(
    model=settings.model_name,
    name="travel_deal_radar",
    description=(
        "An autonomous agent that discovers Hong Kong flight flash deals "
        "by searching the web, recursively scraping travel sites with a "
        "headless browser, and broadcasting a daily digest to Telegram."
    ),
    instruction=SYSTEM_PROMPT,
    tools=[
        google_search,
        scrape_page,
        send_telegram_message,
    ],
)
