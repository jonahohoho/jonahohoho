from dataclasses import dataclass, field
from typing import Optional
from config import SCRAPE_HEADERS


@dataclass
class RawListing:
    source: str
    title: str
    url: str
    external_id: Optional[str] = None
    price: Optional[int] = None
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    area_ping: Optional[float] = None
    rooms: Optional[str] = None
    floor: Optional[str] = None
    image_url: Optional[str] = None


class BaseScraper:
    source: str = "unknown"
    headers: dict = field(default_factory=lambda: dict(SCRAPE_HEADERS))

    def __init__(self):
        self.headers = dict(SCRAPE_HEADERS)

    async def scrape(self) -> list[RawListing]:
        raise NotImplementedError
