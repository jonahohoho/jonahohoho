import aiosqlite
from config import DB_PATH
from models import Listing
from datetime import datetime
from typing import Optional

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS listings (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    source               TEXT NOT NULL,
    external_id          TEXT,
    title                TEXT NOT NULL,
    price                INTEGER,
    address              TEXT,
    district             TEXT,
    city                 TEXT,
    area_ping            REAL,
    rooms                TEXT,
    floor                TEXT,
    url                  TEXT UNIQUE NOT NULL,
    image_url            TEXT,
    lat                  REAL,
    lng                  REAL,
    commute_min_guangbao INTEGER,
    commute_min_fengsan  INTEGER,
    is_available         INTEGER DEFAULT 1,
    scraped_at           TEXT,
    geocoded_at          TEXT
)
"""

CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_source ON listings(source)"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE)
        await db.execute(CREATE_INDEX)
        await db.commit()


async def upsert_listing(listing: Listing) -> bool:
    """Insert or ignore (url is unique). Returns True if inserted."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT OR IGNORE INTO listings
              (source, external_id, title, price, address, district, city,
               area_ping, rooms, floor, url, image_url, scraped_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                listing.source, listing.external_id, listing.title,
                listing.price, listing.address, listing.district, listing.city,
                listing.area_ping, listing.rooms, listing.floor,
                listing.url, listing.image_url,
                datetime.now().isoformat(),
            ),
        )
        await db.commit()
        return cursor.rowcount > 0


async def update_commute(
    listing_id: int,
    lat: float,
    lng: float,
    min_guangbao: Optional[int],
    min_fengsan: Optional[int],
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE listings
            SET lat=?, lng=?, commute_min_guangbao=?, commute_min_fengsan=?, geocoded_at=?
            WHERE id=?
            """,
            (lat, lng, min_guangbao, min_fengsan, datetime.now().isoformat(), listing_id),
        )
        await db.commit()


async def get_listings(
    source: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    district: Optional[str] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    sort_by: str = "scraped_at_desc",
    page: int = 1,
    page_size: int = 24,
) -> tuple[int, list[Listing]]:
    conditions = ["is_available = 1"]
    params: list = []

    if source:
        conditions.append("source = ?")
        params.append(source)
    if min_price is not None:
        conditions.append("price >= ?")
        params.append(min_price)
    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)
    if district:
        conditions.append("district LIKE ?")
        params.append(f"%{district}%")
    if min_area is not None:
        conditions.append("area_ping >= ?")
        params.append(min_area)
    if max_area is not None:
        conditions.append("area_ping <= ?")
        params.append(max_area)

    where = "WHERE " + " AND ".join(conditions)

    order_map = {
        "price_asc": "price ASC NULLS LAST",
        "price_desc": "price DESC NULLS LAST",
        "commute_guangbao": "commute_min_guangbao ASC NULLS LAST",
        "commute_fengsan": "commute_min_fengsan ASC NULLS LAST",
        "scraped_at_desc": "scraped_at DESC",
    }
    order = order_map.get(sort_by, "scraped_at DESC")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        count_row = await db.execute_fetchall(
            f"SELECT COUNT(*) as cnt FROM listings {where}", params
        )
        total = count_row[0]["cnt"]

        offset = (page - 1) * page_size
        rows = await db.execute_fetchall(
            f"SELECT * FROM listings {where} ORDER BY {order} LIMIT ? OFFSET ?",
            [*params, page_size, offset],
        )

    listings = [Listing(**dict(row)) for row in rows]
    return total, listings


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            """
            SELECT source, COUNT(*) as count, MAX(scraped_at) as last_scraped
            FROM listings WHERE is_available=1
            GROUP BY source ORDER BY count DESC
            """
        )
    return [dict(r) for r in rows]


async def get_ungeocode_listings(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, address, district, city FROM listings WHERE lat IS NULL AND address IS NOT NULL LIMIT ?",
            [limit],
        )
    return [dict(r) for r in rows]


async def get_distinct_districts() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT DISTINCT district FROM listings WHERE district IS NOT NULL ORDER BY district"
        )
    return [r[0] for r in rows]
