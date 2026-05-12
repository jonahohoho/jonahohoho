import asyncio
import re
import logging
import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, RawListing

logger = logging.getLogger(__name__)

PTT_BASE = "https://www.ptt.cc"
PTT_INDEX = f"{PTT_BASE}/bbs/Tenant/index.html"
PTT_COOKIES = {"over18": "1"}

# [15k] [15K] [15,000] patterns in title
_PRICE_K = re.compile(r'\b(\d{1,3})[kK]\b')
_PRICE_FULL = re.compile(r'\b(\d{1,3},\d{3})\b')
_PRICE_5DIGIT = re.compile(r'\b([1-9]\d{4})\b')

SKIP_TAGS = {"[問題]", "[心得]", "[新聞]", "[討論]", "[公告]", "[閒聊]", "[版務]", "[情報]"}
PING_RE = re.compile(r'(\d+(?:\.\d+)?)\s*坪')
ROOMS_RE = re.compile(r'(\d+)\s*房\s*(\d+)\s*廳')


def _parse_price(text: str) -> int | None:
    m = _PRICE_K.search(text)
    if m:
        return int(m.group(1)) * 1000
    m = _PRICE_FULL.search(text)
    if m:
        return int(m.group(1).replace(",", ""))
    m = _PRICE_5DIGIT.search(text)
    if m:
        val = int(m.group(1))
        if 3000 <= val <= 150000:
            return val
    return None


def _parse_district(title: str) -> str | None:
    # PTT titles: [板橋][整層] ... or [台北/中山] ...
    m = re.match(r'\[([^\]]{1,6})\]', title)
    if m:
        return m.group(1)
    return None


def _parse_ping(title: str) -> float | None:
    m = PING_RE.search(title)
    return float(m.group(1)) if m else None


def _parse_rooms(title: str) -> str | None:
    m = ROOMS_RE.search(title)
    return f"{m.group(1)}房{m.group(2)}廳" if m else None


class PTTScraper(BaseScraper):
    source = "ptt"

    async def scrape(self) -> list[RawListing]:
        listings: list[RawListing] = []
        url = PTT_INDEX

        async with httpx.AsyncClient(
            cookies=PTT_COOKIES, headers=self.headers, timeout=15, follow_redirects=True
        ) as client:
            for _ in range(3):  # up to 3 index pages
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    for item in soup.select("div.r-ent"):
                        title_el = item.select_one("div.title a")
                        if not title_el:
                            continue

                        title = title_el.get_text(strip=True)
                        href = title_el.get("href", "")

                        if not href or any(t in title for t in SKIP_TAGS):
                            continue

                        # only keep posts that look like rentals
                        if not any(
                            kw in title
                            for kw in ["出租", "整層", "分租", "套房", "雅房", "獨立", "房間", "[租]", "租屋"]
                        ):
                            continue

                        post_url = PTT_BASE + href
                        listings.append(
                            RawListing(
                                source=self.source,
                                title=title,
                                url=post_url,
                                price=_parse_price(title),
                                district=_parse_district(title),
                                area_ping=_parse_ping(title),
                                rooms=_parse_rooms(title),
                            )
                        )

                    # navigate to previous page (older posts)
                    prev = None
                    for a in soup.select("div.btn-group-paging a.btn"):
                        if "前頁" in a.get_text():
                            prev = a.get("href")
                            break

                    if prev:
                        url = PTT_BASE + prev
                        await asyncio.sleep(1)
                    else:
                        break

                except Exception as e:
                    logger.error(f"PTT error on {url}: {e}")
                    break

        logger.info(f"PTT: {len(listings)} listings")
        return listings
