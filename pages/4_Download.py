import streamlit as st
import requests
import re
import json
import os
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

# ===============================================================
# CONFIG
# ===============================================================
LOG_FILE = "scrape_log.json"
HTML_DIR = "scraped_html"
DB_FILE = "scrape_log.db"

os.makedirs(HTML_DIR, exist_ok=True)


# ===============================================================
# UTILITIES
# ===============================================================
def extract_id(url):
    m = re.search(r"/opportunity/.+?/(\d+)", url)
    return m.group(1) if m else "unknown"


def compute_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------
# Save HTML file
# ---------------------------------------------------------------
def save_html_file(html_content, method, url):
    op_id = extract_id(url)
    timestamp = datetime.utcnow().isoformat().replace(":", "-").split(".")[0]

    filename = f"{timestamp}_{method}_{op_id}.html"
    filepath = os.path.join(HTML_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filepath


# ---------------------------------------------------------------
# Load existing logs
# ---------------------------------------------------------------
def load_logs():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


# ---------------------------------------------------------------
# Save log entry
# ---------------------------------------------------------------
def save_log(url, method, html_content):
    html_hash = compute_hash(html_content)

    logs = load_logs()

    # Duplicate detection
    for entry in logs:
        if entry.get("html_hash") == html_hash:
            return entry  # avoid duplicates

    html_path = save_html_file(html_content, method, url)

    log_entry = {
        "url": url,
        "method": method,
        "timestamp": datetime.utcnow().isoformat(),
        "html_path": html_path,
        "html_hash": html_hash
    }

    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

    save_to_sqlite(log_entry)

    return log_entry


# ---------------------------------------------------------------
# Save log to SQLite DB
# ---------------------------------------------------------------
def save_to_sqlite(entry):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            url TEXT,
            method TEXT,
            timestamp TEXT,
            html_path TEXT,
            html_hash TEXT UNIQUE
        )
    """)

    try:
        c.execute("""
            INSERT INTO logs (url, method, timestamp, html_path, html_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (entry["url"], entry["method"], entry["timestamp"], entry["html_path"], entry["html_hash"]))
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()


# ===============================================================
# SCRAPING LAYERS
# ===============================================================

# ------------------ Layer 1: Requests ------------------
def try_requests(url):
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        return {
            "method": "Requests",
            "status": "success",
            "html": r.text
        }
    except:
        return None


# ------------------ Layer 2: Requests-HTML ------------------
def try_requests_html(url):
    try:
        from requests_html import HTMLSession
        session = HTMLSession()
        r = session.get(url)
        r.html.render(timeout=20)

        return {
            "method": "Requests-HTML",
            "status": "success",
            "html": r.html.html
        }
    except:
        return None


# ------------------ Layer 3: Splash ------------------
def try_splash(url):
    try:
        splash_url = "http://localhost:8050/render.html"
        r = requests.get(splash_url, params={"url": url, "wait": 1})
        if r.status_code == 200:
            return {
                "method": "Splash",
                "status": "success",
                "html": r.text
            }
    except:
        return None


# ------------------ Layer 4: Playwright ------------------
def try_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            html = page.content()
            title = page.title()
            browser.close()
            return {
                "method": "Playwright",
                "status": "success",
                "html": html,
                "title": title
            }
    except:
        return None


# ------------------ Layer 5: Selenium ------------------
def try_selenium(url):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        opts = Options()
        opts.add_argument("--headless")
        driver = webdriver.Chrome(options=opts)

        driver.get(url)
        html = driver.page_source
        title = driver.title
        driver.quit()

        return {
            "method": "Selenium",
            "status": "success",
            "html": html,
            "title": title
        }
    except:
        return None


# ------------------ Layer 6: Cloud Browser API ------------------
def try_cloud_api(url, api_key):
    if not api_key:
        return None

    try:
        api = f"http://api.scraperapi.com?api_key={api_key}&render=true&url={url}"
        r = requests.get(api, timeout=20)
        if r.status_code == 200:
            return {
                "method": "Cloud API",
                "status": "success",
                "html": r.text
            }
    except:
        return None


# ------------------ Layer 7: AIESEC API ------------------
def try_aiesec_api(url):
    op_id = extract_id(url)
    if not op_id:
        return None

    api = f"https://gis-api.aiesec.org/v2/opportunities/{op_id}"

    try:
        r = requests.get(api, timeout=10)
        if r.status_code == 200:
            return {
                "method": "AIESEC API",
                "status": "success",
                "json": r.json()
            }
    except:
        return None


# ------------------ Layer 8: AI Extraction ------------------
def try_ai_extraction(html):
    try:
        import openai
        prompt = f"Extract structured info from this HTML:\n\n{html[:20000]}"

        res = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "method": "AI Extraction",
            "status": "success",
            "structured": res["choices"][0]["message"]["content"]
        }
    except:
        return None


# ===============================================================
# STREAMLIT INTERFACE
# ===============================================================
st.set_page_config(page_title="AIESEC Universal Scraper (FULL)", layout="wide")
st.title("🌍 Universal AIESEC Scraper — FULL VERSION")
st.write("Includes: HTML saving · logging · viewer · duplicate hashing · CSV export · SQLite")

url = st.text_input("Enter URL:")
cloud_key = st.text_input("Cloud API Key (optional):", type="password")

if st.button("Run Scraper"):
    if not url:
        st.error("Please enter a URL.")
        st.stop()

    layers = [
        try_requests,
        try_requests_html,
        try_splash,
        try_playwright,
        try_selenium,
        lambda u: try_cloud_api(u, cloud_key),
        try_aiesec_api,
        lambda u: try_ai_extraction("No HTML captured")
    ]

    for layer in layers:
        res = layer(url)

        if res:
            method = res["method"]
            st.success(f"Succeeded using {method}")

            html_output = res.get("html") or json.dumps(res.get("json", ""), indent=2)

            log_entry = save_log(url, method, html_output)

            st.subheader("Log Entry")
            st.json(log_entry)

            st.subheader("Output")
            st.json(res)

            st.stop()

        else:
            st.warning(f"{layer.__name__} failed. Trying next...")

    st.error("All layers failed.")


# ===============================================================
# LOG VIEWER SECTION
# ===============================================================
st.header("📜 Log Viewer")

logs = load_logs()
df = pd.DataFrame(logs)

if len(df) > 0:
    st.dataframe(df)

    if st.button("Export logs to CSV"):
        df.to_csv("scrape_logs.csv", index=False)
        st.success("Logs exported to scrape_logs.csv")

else:
    st.info("No logs yet.")


# ===============================================================
# HTML VIEWER
# ===============================================================
st.header("📂 Browse Saved HTML Files")

html_files = os.listdir(HTML_DIR)

if html_files:
    selected = st.selectbox("Choose HTML file:", html_files)

    if selected:
        with open(os.path.join(HTML_DIR, selected), "r", encoding="utf-8") as f:
            content = f.read()
        st.code(content[:5000], language="html")
else:
    st.info("No HTML files saved yet.")


# import streamlit as st
# import requests
# import re

# # Optional imports inside functions so Streamlit loads even if modules missing


# # ------------------------------------------
# # Helper: Extract ID from AIESEC URL
# # ------------------------------------------
# def extract_id(url):
#     m = re.search(r"/opportunity/.+?/(\d+)", url)
#     return m.group(1) if m else None


# # ------------------------------------------
# # Layer 1: Fast HTML via Requests
# # ------------------------------------------
# def try_requests(url):
#     try:
#         r = requests.get(url, timeout=8)
#         if r.status_code != 200:
#             return None
#         return {
#             "method": "Requests",
#             "status": "success",
#             "html": r.text,
#             "note": "Raw HTML returned (may not contain JS-rendered content)"
#         }
#     except:
#         return None


# # ------------------------------------------
# # Layer 2: Requests-HTML (Light JS)
# # ------------------------------------------
# def try_requests_html(url):
#     try:
#         from requests_html import HTMLSession
#         session = HTMLSession()
#         r = session.get(url)
#         r.html.render(timeout=20)

#         return {
#             "method": "Requests-HTML",
#             "status": "success",
#             "html": r.html.html
#         }
#     except:
#         return None


# # ------------------------------------------
# # Layer 3: Splash (Docker)
# # ------------------------------------------
# def try_splash(url):
#     try:
#         splash_url = "http://localhost:8050/render.html"
#         r = requests.get(splash_url, params={"url": url, "wait": 1})
#         if r.status_code == 200:
#             return {
#                 "method": "Splash",
#                 "status": "success",
#                 "html": r.text
#             }
#     except:
#         return None


# # ------------------------------------------
# # Layer 4: Playwright
# # ------------------------------------------
# def try_playwright(url):
#     try:
#         from playwright.sync_api import sync_playwright
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             page = browser.new_page()
#             page.goto(url, wait_until="networkidle")
#             html = page.content()
#             title = page.title()
#             browser.close()
#             return {
#                 "method": "Playwright",
#                 "status": "success",
#                 "html": html,
#                 "title": title,
#             }
#     except:
#         return None


# # ------------------------------------------
# # Layer 5: Selenium
# # ------------------------------------------
# def try_selenium(url):
#     try:
#         from selenium import webdriver
#         from selenium.webdriver.chrome.options import Options

#         options = Options()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(options=options)

#         driver.get(url)
#         html = driver.page_source
#         title = driver.title
#         driver.quit()

#         return {
#             "method": "Selenium",
#             "status": "success",
#             "html": html,
#             "title": title
#         }
#     except:
#         return None


# # ------------------------------------------
# # Layer 6: Cloud API (ScraperAPI example)
# # ------------------------------------------
# def try_cloud_api(url, api_key):
#     if not api_key:
#         return None

#     try:
#         api = f"http://api.scraperapi.com?api_key={api_key}&render=true&url={url}"
#         r = requests.get(api, timeout=20)

#         if r.status_code == 200:
#             return {
#                 "method": "Cloud API (ScraperAPI)",
#                 "status": "success",
#                 "html": r.text
#             }
#     except:
#         return None


# # ------------------------------------------
# # Layer 7: AIESEC official API
# # ------------------------------------------
# def try_aiesec_api(url):

#     op_id = extract_id(url)
#     if not op_id:
#         return None

#     api = f"https://gis-api.aiesec.org/v2/opportunities/{op_id}"

#     try:
#         r = requests.get(api, timeout=10)
#         if r.status_code == 200:
#             return {
#                 "method": "AIESEC API",
#                 "status": "success",
#                 "json": r.json()
#             }
#     except:
#         return None


# # ------------------------------------------
# # Layer 8: AI Extraction (OpenAI or other LLM)
# # ------------------------------------------
# def try_ai_extraction(html):
#     try:
#         import openai

#         prompt = f"""
#         Extract structured job opportunity info (title, description, skills, backgrounds, salary)
#         from this HTML:

#         {html}
#         """

#         result = openai.ChatCompletion.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}]
#         )

#         return {
#             "method": "AI Extraction",
#             "status": "success",
#             "structured": result["choices"][0]["message"]["content"]
#         }
#     except:
#         return None


# # ------------------------------------------
# # STREAMLIT PAGE
# # ------------------------------------------
# st.set_page_config(page_title="Universal AIESEC Scraper", layout="wide")

# st.title("🌍 Universal AIESEC Opportunity Scraper (All Methods in One Page)")
# st.write("This tool tries 8 scraping layers from fastest → most robust until one succeeds.")

# url = st.text_input("Enter AIESEC Opportunity URL:")
# cloud_key = st.text_input("ScraperAPI Key (optional fallback):", type="password")

# run = st.button("Run Scraper")

# if run:
#     if not url:
#         st.error("Please enter a URL.")
#         st.stop()

#     st.info("🔍 Starting multi-layer scraping...")

#     layers = [
#         ("Requests", try_requests),
#         ("Requests-HTML", try_requests_html),
#         ("Splash", try_splash),
#         ("Playwright", try_playwright),
#         ("Selenium", try_selenium),
#         ("Cloud API", lambda u: try_cloud_api(u, cloud_key)),
#         ("AIESEC API", try_aiesec_api),
#         ("AI Extraction", lambda u: try_ai_extraction("Fallback HTML"))
#     ]

#     for name, func in layers:
#         with st.expander(f"Attempt: {name}", expanded=False):
#             st.write(f"Running {name}...")

#             result = func(url)

#             if result:
#                 st.success(f"{name} succeeded!")
#                 st.json(result)
#                 st.stop()

#             else:
#                 st.warning(f"{name} failed. Moving to next layer...")

#     st.error("❌ All layers failed. Please check the URL or your environment.")


# import streamlit as st
# import requests
# import re
# import json

# # Optional: Only load Playwright if used
# from playwright.sync_api import sync_playwright


# st.set_page_config(page_title="AIESEC Opportunity Scraper", layout="wide")

# st.title("🌍 AIESEC Opportunity Scraper")
# st.write("Scrape Global Talent / Global Teacher opportunity pages with multiple fallback methods.")


# # -----------------------------
# # Helper: Extract numeric ID
# # -----------------------------
# def extract_id(url):
#     match = re.search(r"/opportunity/.+?/(\d+)", url)
#     return match.group(1) if match else None


# # -----------------------------
# # Mode A: Direct API scraping
# # -----------------------------
# def scrape_api(op_id):
#     api_url = f"https://gis-api.aiesec.org/v2/opportunities/{op_id}"

#     try:
#         r = requests.get(api_url, timeout=10)
#         if r.status_code != 200:
#             return None
#         return r.json()
#     except:
#         return None


# # -----------------------------
# # Mode B: Playwright scraping
# # -----------------------------
# def scrape_playwright(url):

#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             page = browser.new_page()
#             page.goto(url, wait_until="networkidle", timeout=30000)

#             html = page.content()

#             # Extract text fallback
#             title = page.query_selector("h1")
#             title_text = title.inner_text() if title else ""

#             browser.close()

#             return {"html": html, "title": title_text}
#     except Exception as e:
#         return {"error": str(e)}


# # -----------------------------
# # Mode C: ScraperAPI
# # -----------------------------
# def scrape_scraperapi(url, key):
#     try:
#         api = f"http://api.scraperapi.com?api_key={key}&render=true&url={url}"
#         r = requests.get(api, timeout=20)
#         if r.status_code != 200:
#             return None
#         return r.text
#     except:
#         return None


# # -----------------------------
# # Streamlit UI
# # -----------------------------
# url = st.text_input("Enter AIESEC Opportunity URL:", "")

# use_scraperapi = st.checkbox("Enable ScraperAPI fallback?")
# scraper_key = st.text_input("ScraperAPI key (if checked)", type="password") if use_scraperapi else None

# if st.button("Scrape Opportunity"):
#     if not url:
#         st.error("Please enter a URL.")
#         st.stop()

#     op_id = extract_id(url)
#     if not op_id:
#         st.error("Could not extract the opportunity ID from the URL.")
#         st.stop()

#     st.info(f"Opportunity ID detected: {op_id}")

#     # -----------------------------
#     # 1. Try FASTEST: official AIESEC API
#     # -----------------------------
#     st.subheader("1️⃣ Trying Direct AIESEC API...")
#     data = scrape_api(op_id)

#     if data:
#         st.success("Success! Data retrieved from the official API.")
#         st.json(data)

#         # Pretty summary
#         opp = data.get("opportunity", {})
#         st.subheader("Extracted Information Summary")
#         st.write(f"### 🏷️ Title: {opp.get('title', 'N/A')}")
#         st.write(f"### 🌍 Location: {opp.get('location', {}).get('city', 'N/A')}, "
#                  f"{opp.get('location', {}).get('country', 'N/A')}")
#         st.write("### 📘 Description")
#         st.write(opp.get("description", "N/A"))

#         st.write("### 🧑‍💼 Skills")
#         st.write(", ".join([s.get("name") for s in opp.get("skills", [])]))

#         st.write("### 🎓 Backgrounds")
#         st.write(", ".join([b.get("name") for b in opp.get("backgrounds", [])]))

#         st.write("### 💰 Salary")
#         st.write(opp.get("salary", {}).get("salary", "N/A"))

#         st.stop()

#     else:
#         st.warning("API method failed. Trying JavaScript rendering...")

#     # -----------------------------
#     # 2. Playwright fallback
#     # -----------------------------
#     st.subheader("2️⃣ Trying Playwright Rendering...")

#     result = scrape_playwright(url)
    
#     if "html" in result:
#         st.success("Playwright successfully rendered the page.")
#         st.write("### Extracted Title (fallback):")
#         st.write(result["title"] or "No title found")

#         st.write("### Full HTML (debug):")
#         st.code(result["html"][:4000])

#         st.stop()

#     else:
#         st.error(f"Playwright failed: {result.get('error')}")
    
#     # -----------------------------
#     # 3. ScraperAPI fallback
#     # -----------------------------
#     if use_scraperapi and scraper_key:
#         st.subheader("3️⃣ Trying ScraperAPI...")

#         html = scrape_scraperapi(url, scraper_key)
#         if html:
#             st.success("ScraperAPI retrieved the page!")
#             st.code(html[:4000])
#             st.stop()
#         else:
#             st.error("ScraperAPI also failed.")

#     st.error("All scraping methods failed. Try enabling ScraperAPI or check the URL.")
