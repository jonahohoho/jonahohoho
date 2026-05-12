from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Listing(BaseModel):
    id: Optional[int] = None
    source: str
    external_id: Optional[str] = None
    title: str
    price: Optional[int] = None         # TWD/month
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    area_ping: Optional[float] = None   # 坪
    rooms: Optional[str] = None         # e.g. "2房1廳1衛"
    floor: Optional[str] = None
    url: str
    image_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    commute_min_guangbao: Optional[int] = None
    commute_min_fengsan: Optional[int] = None
    is_available: bool = True
    scraped_at: Optional[datetime] = None
    geocoded_at: Optional[datetime] = None


class ListingsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    listings: list[Listing]


class SourceStats(BaseModel):
    source: str
    count: int
    last_scraped: Optional[datetime]


class ScrapeResult(BaseModel):
    source: str
    inserted: int
    errors: int
