"""
崔媽媽租屋 (tmm.org.tw) scraper.
URL: https://www.tmm.org.tw/list.php?city=新北市&area=中和區
Non-profit, simple HTML, no anti-scraping.
Selector: .house-list li, .list-item, or table rows (verify against actual HTML)
"""
import asyncio
import logging
import re
import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, RawListing
from config import SEARCH_AREAS

logger = logging.getLogger(__name__)

BASE_URL = "https://www.tmm.org.tw"
PING_RE = re.compile(r'([\d.]+)\s*坪')
PRICE_RE = re.compile(r'([\d,]+)')


def _int(text: str) -> int | None:
    cleaned = re.sub(r'[^\d]', '', text or "")
    return int(cleaned) if cleaned else None


def _find_items(soup: BeautifulSoup) -> list:
    for sel in [
        ".house-list li",
        "ul.list li",
        ".list-item",
        "table.list tr",
        ".rent-list .item",
        "div[class*=item]",
    ]:
        items = soup.select(sel)
        if items:
            logger.debug(f"tmm: selector '{sel}' → {len(items)}")
            return items
    return []


class TMMScraper(BaseScraper):
    source = "tmm"

    async def scrape(self) -> list[RawListing]:
        listings: list[RawListing] = []
        async with httpx.AsyncClient(headers=self.headers, timeout=20, follow_redirects=True) as client:
            for area in SEARCH_AREAS[:6]:
                city = area["city"]
                district = area["district"]
                url = f"{BASE_URL}/list.php?city={city}&area={district}"
                await self._scrape_area(client, url, city, district, listings)
                await asyncio.sleep(1.5)

        logger.info(f"tmm: {len(listings)} listings")
        return listings

    async def _scrape_area(
        self,
        client: httpx.AsyncClient,
        url: str,
        city: str,
        district: str,
        listings: list[RawListing],
    ):
        for page in range(1, 4):
            paged = url if page == 1 else f"{url}&page={page}"
            try:
                resp = await client.get(paged)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                items = _find_items(soup)

                if not items:
                    logger.warning(f"tmm: no items at {paged}")
                    break

                added = 0
                for item in items:
                    link = item.select_one("a[href]")
                    if not link:
                        continue
                    href = link.get("href", "")
                    if not href or href == "#":
                        continue
                    item_url = href if href.startswith("http") else BASE_URL + href

                    title = ""
                    for sel in [".title", "h3", "h4", ".house-name", "[class*=title]"]:
                        n = item.select_one(sel)
                        if n:
                            title = n.get_text(strip=True)
                            break
                    if not title:
                        title = link.get_text(strip=True)
                    if not title:
                        continue

                    price_text = ""
                    for sel in [".price", "[class*=price]", ".rent", "td.price"]:
                        n = item.select_one(sel)
                        if n:
                            price_text = n.get_text(strip=True)
                            break

                    addr = ""
                    for sel in [".address", "[class*=addr]", "td.addr"]:
                        n = item.select_one(sel)
                        if n:
                            addr = n.get_text(strip=True)
                            break

                    ping_text = ""
                    for sel in [".area", "[class*=area]", "[class*=ping]", "td.area"]:
                        n = item.select_one(sel)
                        if n:
                            ping_text = n.get_text(strip=True)
                            break

                    ping_m = PING_RE.search(ping_text)
                    img = item.select_one("img")
                    img_url = img.get("src") if img else None
                    if img_url and img_url.startswith("//"):
                        img_url = "https:" + img_url

                    listings.append(
                        RawListing(
                            source=self.source,
                            title=title,
                            url=item_url,
                            price=_int(price_text),
                            address=addr or None,
                            district=district,
                            city=city,
                            area_ping=float(ping_m.group(1)) if ping_m else None,
                            image_url=img_url,
                        )
                    )
                    added += 1

                if added == 0:
                    break
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"tmm error {paged}: {e}")
                break
