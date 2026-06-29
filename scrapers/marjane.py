from __future__ import annotations

from services.models import Catalogue
from scrapers.common import generic_catalogue_links


def scrape(url: str) -> list[Catalogue]:
    return generic_catalogue_links("Marjane", url, "Marjane")
