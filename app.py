from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from reports.excel_generator import generate_excel
from reports.ppt_generator import generate_ppt
from scrapers import run_scraper
from services.brand_detector import detect_brands
from services.classifier import classify_text
from services.config_loader import load_yaml
from services.downloader import download_file
from services.history_store import HistoryStore
from services.models import PageDetection
from services.ocr_service import ocr_image
from services.pdf_converter import pdf_to_images
from services.storage import DOWNLOAD_DIR, OUTPUT_DIR, PAGE_IMAGE_DIR, ensure_directories

load_dotenv()
ensure_directories()
st.set_page_config(page_title="Leaflet Monitoring Tool", page_icon="🗂️", layout="wide")


def hosted_environment() -> bool:
    return bool(os.getenv("STREAMLIT_SERVER_HEADLESS") or os.getenv("APP_HOSTED"))


def require_login() -> None:
    password = os.getenv("APP_PASSWORD", "")
    if not password:
        st.warning("APP_PASSWORD is not set. Local development is allowed, but set it in Streamlit secrets before hosting.")
        st.session_state.authenticated = True
        return
    if st.session_state.get("authenticated"):
        return
    st.title("Login")
    entered = st.text_input("Password", type="password")
    if st.button("Login") and entered == password:
        st.session_state.authenticated = True
        st.rerun()
    elif entered:
        st.error("Incorrect password")
    st.stop()


def week_number() -> int:
    return date.today().isocalendar().week


def session_defaults() -> None:
    st.session_state.setdefault("catalogues", [])
    st.session_state.setdefault("pages", [])
    st.session_state.setdefault("products", [])
    st.session_state.setdefault("generated_files", [])
    st.session_state.setdefault("scan_warnings", [])


def page_rows() -> list[dict[str, Any]]:
    return st.session_state.get("pages", [])


def process_catalogue(catalogue, categories: dict, brands: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        local_path, file_hash = download_file(catalogue.url, DOWNLOAD_DIR, f"{catalogue.retailer}_{catalogue.title}")
        catalogue.local_path = str(local_path)
        catalogue.file_hash = file_hash
        image_paths = pdf_to_images(local_path, PAGE_IMAGE_DIR) if local_path.suffix.lower() == ".pdf" else [local_path]
        for index, image_path in enumerate(image_paths, start=1):
            text = ocr_image(image_path)
            category = classify_text(text, categories)
            rows.append(
                PageDetection(
                    retailer=catalogue.retailer,
                    catalogue_title=catalogue.title,
                    catalogue_url=catalogue.url,
                    page_number=index,
                    image_path=str(image_path),
                    text=text,
                    category=category,
                    brands=detect_brands(text, brands),
                    include=category != "Other",
                    source_label=catalogue.source_label,
                ).__dict__
            )
    except Exception as exc:
        st.session_state.scan_warnings.append(f"{catalogue.retailer}: could not process {catalogue.title}: {exc}")
    return rows


def check_new_catalogues() -> None:
    retailer_config = load_yaml("config/retailers.yaml").get("retailers", [])
    categories = load_yaml("config/categories.yaml").get("categories", {})
    brands = load_yaml("config/brands.yaml").get("brands", [])
    store = HistoryStore()
    new_count = 0
    old_count = 0
    st.session_state.scan_warnings = []

    for retailer in retailer_config:
        try:
            found = run_scraper(retailer["scraper"], retailer["url"])
        except Exception as exc:
            st.session_state.scan_warnings.append(f"{retailer['name']}: scraper failed: {exc}")
            continue
        for catalogue in found:
            metadata = catalogue.__dict__.copy()
            if store.seen_catalogue(catalogue.retailer, catalogue.url, catalogue.file_hash):
                old_count += 1
                metadata["status"] = "old"
                st.session_state.catalogues.append(metadata)
                continue
            metadata["status"] = "new"
            st.session_state.catalogues.append(metadata)
            rows = process_catalogue(catalogue, categories, brands)
            st.session_state.pages.extend(rows)
            store.add_catalogue(catalogue.__dict__)
            new_count += 1
    store.record_scan(new_count, old_count)
    st.success(f"Scan complete: {new_count} new catalogue(s), {old_count} old catalogue(s) skipped.")


def dashboard() -> None:
    store = HistoryStore()
    last_scan = store.last_scan()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Week", f"W{week_number():02d}")
    col2.metric("Last scan", last_scan["scan_date"][:10] if last_scan else "Never")
    col3.metric("New catalogues found", last_scan["new_count"] if last_scan else 0)
    col4.metric("Old catalogues skipped", last_scan["old_count"] if last_scan else 0)
    if st.session_state.generated_files:
        st.subheader("Quick downloads")
        for file_path in st.session_state.generated_files:
            path = Path(file_path)
            if path.exists():
                st.download_button(path.name, path.read_bytes(), file_name=path.name)


def check_page() -> None:
    st.header("Check New Catalogues")
    st.write("Runs each configured retailer scraper. If one source fails, the scan continues and shows a warning.")
    if st.button("Check New Catalogues", type="primary"):
        check_new_catalogues()
    for warning in st.session_state.scan_warnings:
        st.warning(warning)
    if st.session_state.catalogues:
        st.dataframe(pd.DataFrame(st.session_state.catalogues), use_container_width=True)


def review_page() -> None:
    st.header("Review Pages")
    categories = ["MX", "VD", "DA", "Other"]
    brands = load_yaml("config/brands.yaml").get("brands", [])
    rows = page_rows()
    if not rows:
        st.info("No detected pages yet. Run Check New Catalogues first.")
        return
    for idx, row in enumerate(rows):
        with st.expander(f"{row['retailer']} | {row['catalogue_title']} | Page {row['page_number']}", expanded=idx == 0):
            cols = st.columns([1, 2])
            image_path = Path(row["image_path"])
            if image_path.exists():
                cols[0].image(str(image_path), caption=f"Page {row['page_number']}")
            row["category"] = cols[1].selectbox("Detected category", categories, index=categories.index(row.get("category", "Other")), key=f"cat_{idx}")
            row["brands"] = cols[1].multiselect("Detected brands", brands, default=[brand for brand in row.get("brands", []) if brand in brands], key=f"brands_{idx}")
            row["include"] = cols[1].checkbox("Include in report", value=row.get("include", True), key=f"include_{idx}")
            row["comment"] = cols[1].text_area("Comment", value=row.get("comment", ""), key=f"comment_{idx}")
    if st.button("Save review"):
        st.session_state.pages = rows
        st.success("Review saved in this session.")


def generate_reports_page() -> None:
    st.header("Generate Reports")
    categories_config = load_yaml("config/categories.yaml").get("categories", {})
    pages = [row for row in page_rows() if row.get("include", True)]
    if not pages:
        st.info("No included pages to report. Review pages first.")
        return
    if st.button("Generate Reports", type="primary"):
        generated: list[str] = []
        week = week_number()
        for category, config in categories_config.items():
            rows = [row for row in pages if row.get("category") == category]
            output = OUTPUT_DIR / config["report_name"].format(week=week)
            generate_ppt(config.get("label", category), rows, output, week)
            generated.append(str(output))
        excel_path = OUTPUT_DIR / f"Leaflet W{week:02d} Summary.xlsx"
        generate_excel(st.session_state.catalogues, pages, st.session_state.products, excel_path)
        generated.append(str(excel_path))
        st.session_state.generated_files = generated
        st.success("Reports generated.")
    for file_path in st.session_state.generated_files:
        path = Path(file_path)
        if path.exists():
            st.download_button(path.name, path.read_bytes(), file_name=path.name)


def history_page() -> None:
    st.header("History")
    store = HistoryStore()
    payload = store.export_json()
    st.download_button("Export history JSON", payload, file_name="leaflet_history_backup.json", mime="application/json")
    uploaded = st.file_uploader("Import history JSON", type="json")
    if uploaded and st.button("Import history"):
        store.import_json(uploaded.read().decode("utf-8"))
        st.success("History imported.")


def settings_page() -> None:
    st.header("Settings")
    st.write("Retailers, categories, brands, and PPT style are configured through YAML files in the config folder.")
    st.code(Path("config/retailers.yaml").read_text(encoding="utf-8"), language="yaml")


def main() -> None:
    require_login()
    session_defaults()
    st.sidebar.title("Leaflet Tool")
    page = st.sidebar.radio("Pages", ["Dashboard", "Check New Catalogues", "Review Pages", "Generate Reports", "History", "Settings"])
    st.title("Weekly Leaflet / Catalogue Monitoring")
    if page == "Dashboard":
        dashboard()
    elif page == "Check New Catalogues":
        check_page()
    elif page == "Review Pages":
        review_page()
    elif page == "Generate Reports":
        generate_reports_page()
    elif page == "History":
        history_page()
    else:
        settings_page()


if __name__ == "__main__":
    main()
