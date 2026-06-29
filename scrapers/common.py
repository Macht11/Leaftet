from __future__ import annotations

import hashlib
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from services.models import Catalogue

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LeafletMonitor/1.0)"}


def soup_from_url(url: str) -> BeautifulSoup:
    response = requests.get(url, timeout=30, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def catalogue_from_link(retailer: str, source_url: str, link, source_label: str = "") -> Catalogue | None:
    href = link.get("href")
    if not href:
        return None
    absolute_url = urljoin(source_url, href)
    title = " ".join(link.get_text(" ", strip=True).split()) or link.get("title") or absolute_url.rsplit("/", 1)[-1]
    digest = hashlib.sha256(absolute_url.encode("utf-8")).hexdigest()
    return Catalogue(retailer=retailer, title=title, url=absolute_url, source_url=source_url, source_label=source_label or retailer, file_hash=digest)


def generic_catalogue_links(retailer: str, source_url: str, source_label: str = "") -> list[Catalogue]:
    soup = soup_from_url(source_url)
    catalogues: list[Catalogue] = []
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        text = link.get_text(" ", strip=True).lower()
        if any(marker in href or marker in text for marker in ("catalog", "catalogue", "leaflet", "promo", ".pdf")):
            item = catalogue_from_link(retailer, source_url, link, source_label)
            if item and item.url not in {catalogue.url for catalogue in catalogues}:
                catalogues.append(item)
    return catalogues[:10]
