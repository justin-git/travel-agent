"""Playwright-based recursive web scraper tool for the ADK agent.

Navigates to a URL using a headless browser, extracts visible text content,
and discovers sub-links for the agent to decide whether to follow.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, TimeoutError as PwTimeout

logger = logging.getLogger(__name__)

# Keywords the agent uses to judge relevance (Chinese + English)
_TRAVEL_KEYWORDS: list[str] = [
    "機票", "航班", "優惠", "特價", "快閃", "折扣",
    "HKD", "來回", "單程", "廉航", "直飛",
    "flight", "deal", "promo", "fare", "airline",
    "discount", "booking", "cheap",
]

# Domains we never follow
_BLOCKED_DOMAINS: set[str] = {
    "accounts.google.com", "login.", "facebook.com",
    "twitter.com", "x.com", "instagram.com",
    "youtube.com", "linkedin.com",
}


def _is_blocked(url: str) -> bool:
    """Return True if the URL belongs to a domain we should skip."""
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return True
    return any(b in host for b in _BLOCKED_DOMAINS)


def _relevance_score(text: str) -> int:
    """Count how many travel keywords appear in *text*."""
    lower = text.lower()
    return sum(1 for kw in _TRAVEL_KEYWORDS if kw.lower() in lower)


async def scrape_page(
    url: str,
    depth: int = 0,
    max_depth: int = 4,
) -> dict:
    """Scrape a web page and return its text content plus discovered sub-links.

    The agent calls this tool with a URL obtained from Google Search results.
    The tool renders the page in a headless Chromium browser (handling JS-heavy
    travel blogs) and returns:
      - url: the page URL
      - title: page <title>
      - content: visible text (truncated to ~12 000 chars to fit context)
      - sub_links: list of {url, anchor_text, relevance} for the agent to
        evaluate and optionally follow at the next depth level
      - depth: current crawl depth
      - max_depth: configured maximum depth

    Args:
        url: The page URL to scrape.
        depth: Current recursion depth (0 = initial result).
        max_depth: Maximum allowed depth for recursive crawling.

    Returns:
        A dict with page content and discovered sub-links.
    """
    result: dict = {
        "url": url,
        "title": "",
        "content": "",
        "sub_links": [],
        "depth": depth,
        "max_depth": max_depth,
        "error": None,
    }

    if _is_blocked(url):
        result["error"] = f"Blocked domain: {url}"
        return result

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                locale="zh-HK",
                timezone_id="Asia/Hong_Kong",
            )
            page = await context.new_page()

            # Navigate with a generous timeout for slow travel sites
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Small random delay to appear human-like
            await asyncio.sleep(random.uniform(1.0, 3.0))

            # Wait for body to settle (JS rendering)
            try:
                await page.wait_for_load_state("networkidle", timeout=10_000)
            except PwTimeout:
                pass  # proceed with what we have

            # ----- Extract title -----
            result["title"] = await page.title()

            # ----- Extract visible text -----
            body_text: str = await page.inner_text("body")
            # Collapse whitespace
            body_text = re.sub(r"\s+", " ", body_text).strip()
            # Truncate to avoid blowing up the LLM context
            result["content"] = body_text[:12_000]

            # ----- Discover sub-links (only if we can go deeper) -----
            if depth < max_depth:
                anchors = await page.query_selector_all("a[href]")
                seen_urls: set[str] = set()
                sub_links: list[dict] = []

                for anchor in anchors[:100]:  # limit to first 100 anchors
                    href = await anchor.get_attribute("href")
                    if not href:
                        continue
                    full_url = urljoin(url, href)
                    # Normalise
                    parsed = urlparse(full_url)
                    if parsed.scheme not in ("http", "https"):
                        continue
                    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if clean in seen_urls or _is_blocked(clean):
                        continue
                    seen_urls.add(clean)

                    anchor_text = (await anchor.inner_text()).strip()[:200]
                    score = _relevance_score(anchor_text)
                    if score > 0:
                        sub_links.append({
                            "url": full_url,
                            "anchor_text": anchor_text,
                            "relevance": score,
                        })

                # Sort by relevance descending; top 20
                sub_links.sort(key=lambda x: x["relevance"], reverse=True)
                result["sub_links"] = sub_links[:20]

            await browser.close()

    except PwTimeout:
        result["error"] = f"Timeout loading {url}"
        logger.warning("Timeout scraping %s", url)
    except Exception as exc:
        result["error"] = f"Error scraping {url}: {exc}"
        logger.exception("Failed to scrape %s", url)

    return result
