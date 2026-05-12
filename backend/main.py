import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware

import db
from models import Listing, ListingsResponse, ScrapeResult, SourceStats
from scrapers import ALL_SCRAPERS
from commute import geocode_and_update_all

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(title="租屋聚合器 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/listings", response_model=ListingsResponse)
async def list_listings(
    source: str | None = None,
    min_price: int | None = Query(None, ge=0),
    max_price: int | None = Query(None, ge=0),
    district: str | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    sort_by: str = Query("scraped_at_desc", pattern="^(price_asc|price_desc|commute_guangbao|commute_fengsan|scraped_at_desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
):
    total, listings = await db.get_listings(
        source=source,
        min_price=min_price,
        max_price=max_price,
        district=district,
        min_area=min_area,
        max_area=max_area,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return ListingsResponse(total=total, page=page, page_size=page_size, listings=listings)


@app.post("/api/scrape", response_model=list[ScrapeResult])
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    sources: list[str] | None = Query(None),
):
    targets = sources or list(ALL_SCRAPERS.keys())
    results: list[ScrapeResult] = []

    for name in targets:
        cls = ALL_SCRAPERS.get(name)
        if not cls:
            continue
        scraper = cls()
        inserted = errors = 0
        try:
            raw_listings = await scraper.scrape()
            for raw in raw_listings:
                listing = Listing(
                    source=raw.source,
                    external_id=raw.external_id,
                    title=raw.title,
                    price=raw.price,
                    address=raw.address,
                    district=raw.district,
                    city=raw.city,
                    area_ping=raw.area_ping,
                    rooms=raw.rooms,
                    floor=raw.floor,
                    url=raw.url,
                    image_url=raw.image_url,
                )
                if await db.upsert_listing(listing):
                    inserted += 1
        except Exception as e:
            logger.error(f"Scraper {name} failed: {e}")
            errors += 1

        results.append(ScrapeResult(source=name, inserted=inserted, errors=errors))
        logger.info(f"{name}: inserted={inserted} errors={errors}")

    # geocode in background (respects Nominatim 1 req/s)
    background_tasks.add_task(geocode_and_update_all, db)
    return results


@app.get("/api/stats", response_model=list[SourceStats])
async def get_stats():
    rows = await db.get_stats()
    return [SourceStats(**r) for r in rows]


@app.get("/api/districts")
async def get_districts():
    return await db.get_distinct_districts()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
