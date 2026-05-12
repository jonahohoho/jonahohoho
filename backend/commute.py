import asyncio
import logging
import httpx
from config import NOMINATIM_URL, OSRM_URL, WORK_LOCATIONS

logger = logging.getLogger(__name__)

NOMINATIM_HEADERS = {
    "User-Agent": "rental-aggregator/1.0 (personal; contact@example.com)",
}


async def geocode(address: str, client: httpx.AsyncClient) -> tuple[float, float] | None:
    """Return (lat, lng) or None. Rate-limit: caller must sleep 1s between calls."""
    try:
        r = await client.get(
            NOMINATIM_URL,
            params={"q": address + ", Taiwan", "format": "json", "limit": 1},
            headers=NOMINATIM_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.warning(f"Geocode failed for '{address}': {e}")
    return None


async def driving_minutes(
    lat1: float, lng1: float, lat2: float, lng2: float, client: httpx.AsyncClient
) -> int | None:
    """OSRM driving duration in minutes. Uses (lng, lat) order."""
    try:
        url = f"{OSRM_URL}/{lng1},{lat1};{lng2},{lat2}"
        r = await client.get(url, params={"overview": "false"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "Ok":
            secs = data["routes"][0]["duration"]
            return max(1, round(secs / 60))
    except Exception as e:
        logger.warning(f"OSRM failed ({lat1},{lng1}→{lat2},{lng2}): {e}")
    return None


async def compute_commutes(
    lat: float, lng: float, client: httpx.AsyncClient
) -> tuple[int | None, int | None]:
    """Return (min_guangbao, min_fengsan)."""
    gb = WORK_LOCATIONS["guangbao"]
    fs = WORK_LOCATIONS["fengsan"]

    min_gb, min_fs = await asyncio.gather(
        driving_minutes(lat, lng, gb["lat"], gb["lng"], client),
        driving_minutes(lat, lng, fs["lat"], fs["lng"], client),
    )
    return min_gb, min_fs


async def geocode_and_update_all(db_module):
    """Background task: geocode un-geocoded listings and compute commute times."""
    from db import get_ungeocode_listings, update_commute

    rows = await get_ungeocode_listings(limit=50)
    if not rows:
        return

    logger.info(f"Geocoding {len(rows)} listings...")
    async with httpx.AsyncClient() as client:
        for row in rows:
            addr = row.get("address") or f"{row.get('city', '')} {row.get('district', '')}"
            coords = await geocode(addr, client)
            await asyncio.sleep(1.1)  # Nominatim: 1 req/s

            if coords:
                lat, lng = coords
                min_gb, min_fs = await compute_commutes(lat, lng, client)
                await update_commute(row["id"], lat, lng, min_gb, min_fs)
                logger.debug(f"Geocoded listing {row['id']}: 光寶={min_gb}m 鳳三={min_fs}m")
