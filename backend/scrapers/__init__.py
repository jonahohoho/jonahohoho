from .rental123 import Rental123Scraper
from .houseprice import HousepriceScraper
from .tmm import TMMScraper
from .ptt import PTTScraper

ALL_SCRAPERS = {
    "rental123": Rental123Scraper,
    "houseprice": HousepriceScraper,
    "tmm": TMMScraper,
    "ptt": PTTScraper,
}
