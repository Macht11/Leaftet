from __future__ import annotations

from importlib import import_module


def run_scraper(scraper_name: str, url: str):
    module = import_module(f"scrapers.{scraper_name}")
    return module.scrape(url)
