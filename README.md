# Leaflet Monitoring Tool

A free, open-source Streamlit web app for a weekly Monday workflow that monitors Moroccan retailer catalogues, detects new leaflets, OCRs pages, classifies activity into MX / VD / DA, lets you review the results, and generates three editable PowerPoint reports plus one Excel summary.

## What it does

- Checks configured retailer sources:
  - Carrefour: <https://carrefour.ma/catalogues/>
  - Marjane: <https://www.marjane.ma/contenu/nos-catalogues>
  - Aswak Assalam: <https://aswakassalam.com/catalogue/>
  - Electroplanet via DepenseLess: <https://depenseless.com/magasin/electroplanet/>
- Detects catalogue metadata, URLs, validity text when available, source label, and hashes.
- Saves catalogue history in SQLite and optionally Supabase.
- Skips catalogue entries already stored in history.
- Downloads PDFs/images, converts PDFs to page images with PyMuPDF, and OCRs pages with Tesseract.
- Classifies pages into MX, VD, DA, or Other using configurable keywords.
- Detects Samsung and competitor brands using configurable brand lists.
- Provides a review dashboard where you can correct category, brands, inclusion, and comments.
- Generates:
  - `Leaflet WXX MX.pptx`
  - `Leaflet WXX VD TV.pptx`
  - `Leaflet WXX DA.pptx`
  - `Leaflet WXX Summary.xlsx`
- Allows JSON export/import of history for backup on free hosting.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

### OCR dependency

`pytesseract` requires the free Tesseract OCR engine to be installed on your machine. Install French and English language data if possible because Moroccan catalogues often contain French text.

- Windows: install Tesseract from the UB Mannheim build.
- macOS: `brew install tesseract tesseract-lang`
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng`

If OCR is unavailable, the app continues and records a warning-like OCR text instead of crashing.

## Password login

The app uses `APP_PASSWORD`.

- Local development: if `APP_PASSWORD` is not set, the app allows access and shows a warning.
- Hosted deployment: set `APP_PASSWORD` in Streamlit Community Cloud secrets.

Example local `.env`:

```bash
cp .env.example .env
# edit APP_PASSWORD
```

## Streamlit Community Cloud deployment

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud and create a new app from the repository.
3. Set the main file path to `app.py`.
4. In app secrets, add:

```toml
APP_PASSWORD = "your-secure-password"
```

5. Deploy the app.
6. Open it from your work browser, log in, run the scan, review pages, generate reports, and download the PPT/Excel files.

## Optional Supabase history persistence

Free Streamlit hosting may reset local files. SQLite works locally and during a live session, but for more persistent hosted history you can optionally create a free Supabase project.

Create a table named `leaflet_history` with columns matching the catalogue metadata you want to persist, then add these secrets:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-or-service-key"
SUPABASE_TABLE = "leaflet_history"
```

You can also use the History page to export/import `leaflet_history_backup.json` manually.

## Configuration

The app avoids hardcoding business rules:

- `config/retailers.yaml` contains retailer URLs and scraper module names.
- `config/categories.yaml` contains MX / VD / DA keywords and report names.
- `config/brands.yaml` contains Samsung and competitor brand keywords.
- `config/ppt_style.yaml` contains presentation style values.

## Notes and limitations

- Retailer websites change frequently. Each scraper is intentionally simple and fault-tolerant. If one retailer fails, the scan continues for the others and shows a warning.
- Some sites may block cloud-hosted scraping. If that happens, export/import history and manual catalogue uploads can be added next.
- Playwright is included as an optional dependency for future dynamic-page scraping, but the first implementation uses `requests` and BeautifulSoup by default.
- Charts in PPT files are editable PowerPoint charts. Catalogue pages are inserted as images because they originate from PDFs/screenshots.

## Run tests

```bash
python -m pytest
```

## Testing without your personal PC

If you cannot use your personal PC, the easiest browser-only path is to push this repository to GitHub and deploy it directly to a free host.

### Recommended option 1: Streamlit Community Cloud

Use this first because the app is already a Streamlit app.

1. Push the repository to GitHub.
2. Create a new app on Streamlit Community Cloud.
3. Select `app.py` as the entry file.
4. Add this secret:

```toml
APP_PASSWORD = "your-secure-password"
```

5. Deploy and open the app URL from your work browser.



### Recommended option 2: Hugging Face Spaces with Docker

Use this if Streamlit Community Cloud cannot install OCR dependencies or if you want a Docker-based free host.

1. Create a free Hugging Face Space.
2. Choose **Docker** as the SDK.
3. Connect or upload this repository.
4. Set `APP_PASSWORD` as a Space secret.
5. The included `Dockerfile` installs Python dependencies and Tesseract OCR, then runs Streamlit.

### Recommended option 3: Render free web service

Render can deploy this repository using the included `render.yaml` and `Dockerfile`.

1. Push the repo to GitHub.
2. In Render, create a new Blueprint or Web Service from the repo.
3. Use the free plan.
4. Set `APP_PASSWORD` as an environment variable.
5. Deploy.

Render free services may sleep after inactivity, so the first load can be slow.

### About Vercel

Vercel is not the best fit for this app because Streamlit is a long-running web server and this project also needs OCR/system packages such as Tesseract. Vercel is optimized for serverless web apps, not persistent Streamlit sessions with file generation. If you must use Vercel later, the app would need to be redesigned as a FastAPI backend plus separate frontend, and OCR/report generation would need careful handling around serverless limits.
