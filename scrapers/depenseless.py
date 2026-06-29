from __future__ import annotations

from urllib.parse import urljoin

from services.models import Catalogue, ProductPromotion
from scrapers.common import soup_from_url


def scrape(url: str) -> list[Catalogue]:
    soup = soup_from_url(url)
    catalogues: list[Catalogue] = []
    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = link["href"]
        if "electroplanet" in (text + href).lower() or "catalogue" in (text + href).lower():
            absolute = urljoin(url, href)
            title = text or "Electroplanet catalogue"
            catalogues.append(Catalogue(retailer="Electroplanet", title=title, url=absolute, source_url=url, source_label="DepenseLess", file_hash=absolute))
    return catalogues[:5]


def scrape_products(catalogue_url: str, retailer: str = "Electroplanet", title: str = "") -> list[ProductPromotion]:
    soup = soup_from_url(catalogue_url)
    products: list[ProductPromotion] = []
    for card in soup.select(".product, .promotion, article, tr"):
        text = " ".join(card.get_text(" ", strip=True).split())
        if not text:
            continue
        products.append(ProductPromotion(retailer=retailer, catalogue_title=title, name=text[:180]))
    return products[:200]
