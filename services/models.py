from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Catalogue:
    retailer: str
    title: str
    url: str
    source_url: str
    source_label: str
    validity: str = ""
    file_hash: str = ""
    local_path: str = ""
    cover_image: str = ""
    status: str = "new"


@dataclass
class PageDetection:
    retailer: str
    catalogue_title: str
    catalogue_url: str
    page_number: int
    image_path: str
    text: str = ""
    category: str = "Other"
    brands: list[str] = field(default_factory=list)
    include: bool = True
    comment: str = ""
    source_label: str = ""


@dataclass
class ProductPromotion:
    retailer: str
    catalogue_title: str
    name: str
    brand: str = ""
    price: str = ""
    old_price: str = ""
    discount: str = ""
    promo_type: str = ""
    category: str = "Other"
