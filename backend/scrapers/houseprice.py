"""
rent.houseprice.tw scraper.
Search URL: https://rent.houseprice.tw/list/?keyword={district}&Rentalprice_e=50000
Listing selector: .house-list-item or .item-container (verify against actual HTML)
"""
import asyncio
import logging
import re
import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, RawListing
from config import SEARCH_AREAS

logger = logging.getLogger(__name__)

BASE_URL = "https://rent.houseprice.tw"
PING_RE = re.compile(r'([\d.]+)\s*坪')
PRICE_RE = re.compile(r'([\d,]+)')


def _int(text: str) -> int | None:
    cleaned = re.sub(r'[^\d]', '', text or "")
    return int(cleaned) if cleaned else None


def _find_items(soup: BeautifulSoup) -> list:
    for sel in [
        ".house-list-item",
        ".item-container",
        ".rent-item",
        "ul.list li",
        ".search-list .item",
        "div[class*=house-item]",
    ]:
        items = soup.select(sel)
        if items:
            logger.debug(f"houseprice: selector '{sel}' → {len(items)}")
            return items
    return []


class HousepriceScraper(BaseScraper):
    source = "houseprice"

    async def scrape(self) -> list[RawListing]:
        listings: list[RawListing] = []
        async with httpx.AsyncClient(headers=self.headers, timeout=20, follow_redirects=True) as client:
            for area in SEARCH_AREAS[:6]:
                district = area["district"]
                city = area["city"]
                url = f"{BASE_URL}/list/?keyword={district}&Rentalprice_e=60000"
                await self._scrape_page(client, url, city, district, listings)
                await asyncio.sleep(1.5)

        logger.info(f"houseprice: {len(listings)} listings")
        return listings

    async def _scrape_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        city: str,
        district: str,
        listings: list[RawListing],
    ):
        for page in range(1, 4):
            paged_url = url if page == 1 else f"{url}&page={page}"
            try:
                resp = await client.get(paged_url)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                items = _find_items(soup)

                if not items:
                    logger.warning(f"houseprice: no items at {paged_url}")
                    break

                added = 0
                for item in items:
                    link = item.select_one("a[href]")
                    if not link:
                        continue
                    href = link.get("href", "")
                    item_url = href if href.startswith("http") else BASE_URL + href

                    title = ""
                    for sel in [".title", "h2", "h3", ".name", "[class*=title]"]:
                        n = item.select_one(sel)
                        if n:
                            title = n.get_text(strip=True)
                            break
                    if not title:
                        title = link.get_text(strip=True)
                    if not title:
                        continue

                    price_text = ""
                    for sel in [".price", "[class*=price]", "[class*=rent]"]:
                        n = item.select_one(sel)
                        if n:
                            price_text = n.get_text(strip=True)
                            break

                    addr = ""
                    for sel in [".address", "[class*=addr]", "[class*=location]"]:
                        n = item.select_one(sel)
                        if n:
                            addr = n.get_text(strip=True)
                            break

                    ping_text = ""
                    for sel in [".area", "[class*=area]", "[class*=ping]", "[class*=size]"]:
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
                logger.error(f"houseprice error {paged_url}: {e}")
                break
