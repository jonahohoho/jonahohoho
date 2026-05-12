"""
rental123.com.tw scraper.
URL structure: https://www.rental123.com.tw/租屋/{city}/{district}?page=N
Listing selector: .house-list .house-item  (verify against actual HTML)

To debug selectors, set env DEBUG_SCRAPER=1 and run:
  python -c "from scrapers.rental123 import Rental123Scraper; import asyncio; asyncio.run(Rental123Scraper().scrape())"
"""
import asyncio
import logging
import re
import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, RawListing
from config import SEARCH_AREAS

logger = logging.getLogger(__name__)

BASE_URL = "https://www.rental123.com.tw"
PRICE_RE = re.compile(r'[\$＄]?\s*([\d,]+)')
PING_RE = re.compile(r'([\d.]+)\s*坪')


def _to_int(text: str) -> int | None:
    cleaned = re.sub(r'[^\d]', '', text)
    return int(cleaned) if cleaned else None


def _find_listings(soup: BeautifulSoup) -> list:
    # Try multiple selector patterns common in Taiwan rental sites
    for sel in [
        ".house-list .house-item",
        ".list-item",
        ".rent-list li",
        "article.item",
        ".item-list .item",
        ".search-result .result-item",
    ]:
        items = soup.select(sel)
        if items:
            logger.debug(f"rental123: matched selector '{sel}' → {len(items)} items")
            return items
    return []


def _extract_text(el, *selectors) -> str:
    for sel in selectors:
        node = el.select_one(sel)
        if node:
            return node.get_text(strip=True)
    return ""


class Rental123Scraper(BaseScraper):
    source = "rental123"

    async def scrape(self) -> list[RawListing]:
        listings: list[RawListing] = []
        async with httpx.AsyncClient(headers=self.headers, timeout=20, follow_redirects=True) as client:
            for area in SEARCH_AREAS[:6]:  # first 6 areas for MVP
                city = area["city"]
                district = area["district"]
                url = f"{BASE_URL}/租屋/{city}/{district}"
                await self._scrape_area(client, url, city, district, listings)
                await asyncio.sleep(1.5)

        logger.info(f"rental123: {len(listings)} listings")
        return listings

    async def _scrape_area(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        city: str,
        district: str,
        listings: list[RawListing],
    ):
        for page in range(1, 4):
            url = base_url if page == 1 else f"{base_url}?page={page}"
            try:
                resp = await client.get(url)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                items = _find_listings(soup)

                if not items:
                    logger.warning(f"rental123: no items found at {url} — selectors may need updating")
                    break

                new = 0
                for item in items:
                    link_el = item.select_one("a[href*='/租屋/']") or item.select_one("a")
                    if not link_el:
                        continue
                    href = link_el.get("href", "")
                    item_url = href if href.startswith("http") else BASE_URL + href
                    if not item_url:
                        continue

                    title = _extract_text(item, ".title", "h2", "h3", ".name", ".house-title")
                    if not title:
                        title = link_el.get_text(strip=True)

                    price_text = _extract_text(item, ".price", ".rent-price", "[class*=price]")
                    price = _to_int(price_text) if price_text else None

                    address = _extract_text(item, ".address", ".location", "[class*=addr]", "[class*=loc]")
                    ping_text = _extract_text(item, ".area", ".ping", "[class*=area]", "[class*=ping]")
                    ping_m = PING_RE.search(ping_text) if ping_text else None

                    img_el = item.select_one("img")
                    img_url = img_el.get("src") if img_el else None
                    if img_url and img_url.startswith("//"):
                        img_url = "https:" + img_url

                    listings.append(
                        RawListing(
                            source=self.source,
                            title=title,
                            url=item_url,
                            price=price,
                            address=address or None,
                            district=district,
                            city=city,
                            area_ping=float(ping_m.group(1)) if ping_m else None,
                            image_url=img_url,
                        )
                    )
                    new += 1

                if new == 0:
                    break
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"rental123 error {url}: {e}")
                break
