from pathlib import Path

BASE_DIR = Path(__file__).parent

WORK_LOCATIONS = {
    "guangbao": {
        "name": "光寶中和廠",
        "address": "新北市中和區建一路157號",
        "lat": 24.9987,
        "lng": 121.5015,
    },
    "fengsan": {
        "name": "鳳三設計",
        "address": "台北市士林區中山北路六段302號",
        "lat": 25.0960,
        "lng": 121.5255,
    },
}

# Areas to search (covers reasonable commute range between both workplaces)
SEARCH_AREAS = [
    {"city": "新北市", "district": "中和區"},
    {"city": "新北市", "district": "永和區"},
    {"city": "新北市", "district": "新店區"},
    {"city": "新北市", "district": "板橋區"},
    {"city": "台北市", "district": "文山區"},
    {"city": "台北市", "district": "大安區"},
    {"city": "台北市", "district": "中正區"},
    {"city": "台北市", "district": "萬華區"},
    {"city": "台北市", "district": "中山區"},
    {"city": "台北市", "district": "士林區"},
    {"city": "台北市", "district": "北投區"},
]

DB_PATH = str(BASE_DIR / "rentals.db")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"

SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}
