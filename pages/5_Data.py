import streamlit as st
import requests
import re
import json
import os
import hashlib
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

# ===============================================================
# CONFIG
# ===============================================================
LOG_FILE = "scrape_log.json"
HTML_DIR = "scraped_html"
PARSER_LOG_FILE = "parser_log.json"

os.makedirs(HTML_DIR, exist_ok=True)

# ===============================================================
# UTILS: GENERAL
# ===============================================================

def extract_id(url):
    m = re.search(r"/opportunity/.+?/(\d+)", url)
    return m.group(1) if m else "unknown"


def compute_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ----------------- HTML FILE SAVE -----------------

def save_html_file(html_content, method, url):
    op_id = extract_id(url)
    timestamp = datetime.utcnow().isoformat().replace(":", "-").split(".")[0]
    filename = f"{timestamp}_{method}_{op_id}.html"
    filepath = os.path.join(HTML_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filepath


# ----------------- SCRAPE LOGS -----------------

def load_logs():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_log(url, method, html_content):
    html_hash = compute_hash(html_content)
    logs = load_logs()

    # Duplicate detection
    for entry in logs:
        if entry.get("html_hash") == html_hash:
            return entry  # already logged

    html_path = save_html_file(html_content, method, url)

    log_entry = {
        "url": url,
        "method": method,
        "timestamp": datetime.utcnow().isoformat(),
        "html_path": html_path,
        "html_hash": html_hash
    }

    logs.append(log_entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

    return log_entry


# ----------------- PARSER LOGS -----------------

def save_parser_log(html_file, parser_type, json_output_path):
    log_entry = {
        "html_file": html_file,
        "parser_type": parser_type,
        "json_output_path": json_output_path,
        "timestamp": datetime.utcnow().isoformat()
    }

    if os.path.exists(PARSER_LOG_FILE):
        try:
            logs = json.load(open(PARSER_LOG_FILE, "r", encoding="utf-8"))
        except Exception:
            logs = []
    else:
        logs = []

    logs.append(log_entry)

    with open(PARSER_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

    return log_entry


def load_parser_logs():
    if os.path.exists(PARSER_LOG_FILE):
        try:
            return json.load(open(PARSER_LOG_FILE, "r", encoding="utf-8"))
        except Exception:
            return []
    return []


# ===============================================================
# SCRAPING LAYERS
# ===============================================================

def try_requests(url):
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        return {"method": "Requests", "status": "success", "html": r.text}
    except Exception:
        return None


def try_requests_html(url):
    try:
        from requests_html import HTMLSession
        session = HTMLSession()
        r = session.get(url)
        r.html.render(timeout=20)
        return {"method": "Requests-HTML", "status": "success", "html": r.html.html}
    except Exception:
        return None


def try_splash(url):
    try:
        splash_url = "http://localhost:8050/render.html"
        r = requests.get(splash_url, params={"url": url, "wait": 1})
        if r.status_code == 200:
            return {"method": "Splash", "status": "success", "html": r.text}
    except Exception:
        return None


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
            return {"method": "Playwright", "status": "success", "html": html, "title": title}
    except Exception:
        return None


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
        return {"method": "Selenium", "status": "success", "html": html, "title": title}
    except Exception:
        return None


def try_cloud_api(url, api_key):
    if not api_key:
        return None
    try:
        api = f"http://api.scraperapi.com?api_key={api_key}&render=true&url={url}"
        r = requests.get(api, timeout=20)
        if r.status_code == 200:
            return {"method": "Cloud API", "status": "success", "html": r.text}
    except Exception:
        return None


def try_aiesec_api(url):
    op_id = extract_id(url)
    if not op_id:
        return None
    api = f"https://gis-api.aiesec.org/v2/opportunities/{op_id}"
    try:
        r = requests.get(api, timeout=10)
        if r.status_code == 200:
            return {"method": "AIESEC API", "status": "success", "json": r.json()}
    except Exception:
        return None


def try_ai_extraction(html):
    # Placeholder for future AI parsing; currently disabled to avoid extra deps
    return None


# ===============================================================
# PARSER TYPES
# ===============================================================

def extract_section_by_keywords(soup, keywords, max_nodes=50):
    """
    Find headings with given keywords, then collect following siblings
    until the next heading or node limit.
    """
    sections = []
    lowered_keywords = [k.lower() for k in keywords]

    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = heading.get_text(strip=True).lower()
        if any(k in text for k in lowered_keywords):
            items = []
            count = 0
            for sib in heading.next_siblings:
                if isinstance(sib, str):
                    continue
                if sib.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    break
                if sib.name in ["p", "li", "div", "span"]:
                    content = sib.get_text(strip=True)
                    if content:
                        items.append(content)
                        count += 1
                if count >= max_nodes:
                    break
            if items:
                sections.append({
                    "heading": heading.get_text(strip=True),
                    "items": items
                })
    return sections


# Type 1 – Paragraphs & Headings
def parser_type_1(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    data = []

    for p in soup.find_all("p"):
        txt = p.get_text(strip=True)
        if txt:
            data.append({"type": "paragraph", "content": txt})

    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        txt = h.get_text(strip=True)
        if txt:
            data.append({"type": "heading", "level": h.name, "content": txt})

    return data


# Type 2 – Links & List Items
def parser_type_2(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    data = []

    for a in soup.find_all("a"):
        txt = a.get_text(strip=True)
        href = a.get("href")
        if txt or href:
            data.append({"type": "link", "href": href, "content": txt})

    for li in soup.find_all("li"):
        txt = li.get_text(strip=True)
        if txt:
            data.append({"type": "list_item", "content": txt})

    return data


# Type 3 – Job Description Sections
def parser_type_3_job_description(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    keywords = ["job description", "role description", "main activities",
                "responsibilities", "what will you do"]
    sections = extract_section_by_keywords(soup, keywords)
    data = []
    for sec in sections:
        for item in sec["items"]:
            data.append({
                "type": "job_description",
                "section_heading": sec["heading"],
                "content": item
            })
    return data


# Type 4 – Skills Sections
def parser_type_4_skills(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    keywords = ["skills", "competencies", "backgrounds", "preferred skills"]
    sections = extract_section_by_keywords(soup, keywords)
    data = []
    for sec in sections:
        for item in sec["items"]:
            data.append({
                "type": "skill",
                "section_heading": sec["heading"],
                "content": item
            })
    return data


# Type 5 – Eligibility Sections
def parser_type_5_eligibility(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    keywords = ["eligibility", "requirements", "profile", "who can apply", "criteria"]
    sections = extract_section_by_keywords(soup, keywords)
    data = []
    for sec in sections:
        for item in sec["items"]:
            data.append({
                "type": "eligibility",
                "section_heading": sec["heading"],
                "content": item
            })
    return data


PARSER_TYPES = {
    "Type 1 – Paragraphs & Headings": ("type_1", parser_type_1),
    "Type 2 – Links & List Items": ("type_2", parser_type_2),
    "Type 3 – Job Description Sections": ("type_3_job_description", parser_type_3_job_description),
    "Type 4 – Skills Sections": ("type_4_skills", parser_type_4_skills),
    "Type 5 – Eligibility Sections": ("type_5_eligibility", parser_type_5_eligibility),
}


# ===============================================================
# STREAMLIT UI
# ===============================================================
st.set_page_config(page_title="AIESEC Scraper & Parser Suite", layout="wide")
st.title("🌍 AIESEC Scraper & HTML Parser Suite (JSON-only Logs)")

tab_scrape, tab_parse, tab_logs = st.tabs(["🔎 Scrape", "🔄 Parse HTML → JSON", "📊 Logs & Visualizations"])

# ===============================================================
# TAB 1: SCRAPE
# ===============================================================
with tab_scrape:
    st.header("🔎 Scrape AIESEC Opportunity")

    url = st.text_input("Enter AIESEC Opportunity URL:")
    cloud_key = st.text_input("Cloud API Key (optional for Cloud API layer):", type="password")

    if st.button("Run Scraper"):
        if not url:
            st.error("Please enter a URL.")
        else:
            layers = [
                try_requests,
                try_requests_html,
                try_splash,
                try_playwright,
                try_selenium,
                lambda u: try_cloud_api(u, cloud_key),
                try_aiesec_api,
                lambda u: try_ai_extraction("No HTML captured"),
            ]

            for layer in layers:
                res = layer(url)
                if res:
                    method = res["method"]
                    st.success(f"Succeeded using {method}")

                    html_output = res.get("html") or json.dumps(res.get("json", ""), indent=2)
                    log_entry = save_log(url, method, html_output)

                    st.subheader("Scrape Log Entry")
                    st.json(log_entry)

                    st.subheader("Raw Result")
                    st.json(res)
                    break
                else:
                    st.warning(f"{layer.__name__} failed. Trying next...")
            else:
                st.error("All scraping layers failed.")

    st.subheader("📂 Browse Saved HTML Files")
    html_files = os.listdir(HTML_DIR)
    if html_files:
        selected = st.selectbox("Choose HTML file to preview", html_files, key="preview_html")
        if selected:
            with open(os.path.join(HTML_DIR, selected), "r", encoding="utf-8") as f:
                content = f.read()
            st.code(content[:5000], language="html")
    else:
        st.info("No HTML files saved yet.")


# ===============================================================
# TAB 2: PARSE HTML → JSON
# ===============================================================
with tab_parse:
    st.header("🔄 HTML → JSON Parser")

    html_files = os.listdir(HTML_DIR)
    if not html_files:
        st.info("No HTML files available. Scrape something first.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            selected_html = st.selectbox("Select HTML file", html_files, key="parse_html_single")
        with col2:
            parser_label = st.selectbox("Select Parser Type", list(PARSER_TYPES.keys()), key="parser_choice_single")

        run_single = st.button("Run Parser on Selected HTML")
        run_bulk = st.button("Bulk Parse ALL HTML files with Selected Parser")

        if run_single:
            html_path = os.path.join(HTML_DIR, selected_html)
            with open(html_path, "r", encoding="utf-8") as f:
                html_text = f.read()

            parser_type_key, parser_fn = PARSER_TYPES[parser_label]
            parsed_data = parser_fn(html_text)

            json_output_path = html_path.replace(".html", f"_{parser_type_key}.json")
            with open(json_output_path, "w", encoding="utf-8") as out:
                json.dump(parsed_data, out, indent=4, ensure_ascii=False)

            log_entry = save_parser_log(selected_html, parser_type_key, json_output_path)

            st.success(f"Parsed successfully with {parser_label}. JSON saved at: {json_output_path}")
            st.subheader("Preview JSON")
            st.json(parsed_data[:50])  # preview first 50 items
            st.subheader("Parser Log Entry")
            st.json(log_entry)

        if run_bulk:
            parser_type_key, parser_fn = PARSER_TYPES[parser_label]
            bulk_logs = []
            for file_name in html_files:
                html_path = os.path.join(HTML_DIR, file_name)
                with open(html_path, "r", encoding="utf-8") as f:
                    html_text = f.read()
                parsed_data = parser_fn(html_text)
                json_output_path = html_path.replace(".html", f"_{parser_type_key}.json")
                with open(json_output_path, "w", encoding="utf-8") as out:
                    json.dump(parsed_data, out, indent=4, ensure_ascii=False)
                log_entry = save_parser_log(file_name, parser_type_key, json_output_path)
                bulk_logs.append(log_entry)

            st.success(f"Bulk parsed {len(html_files)} HTML files with {parser_label}.")
            st.subheader("Bulk Parser Logs")
            st.json(bulk_logs)

    # Visualization for parser outputs (per JSON file)
    st.subheader("📊 Visualize Parsed JSON (by content type)")
    parser_logs = load_parser_logs()
    if parser_logs:
        df_parser = pd.DataFrame(parser_logs)
        st.dataframe(df_parser)

        json_files = df_parser["json_output_path"].dropna().unique().tolist()
        selected_json = st.selectbox("Select JSON output for visualization", json_files, key="json_vis_select")

        if selected_json and os.path.exists(selected_json):
            with open(selected_json, "r", encoding="utf-8") as f:
                parsed_items = json.load(f)

            if isinstance(parsed_items, dict):
                parsed_items = [parsed_items]

            df_items = pd.DataFrame(parsed_items)
            st.write("Parsed items preview:")
            st.dataframe(df_items.head(50))

            if "type" in df_items.columns:
                st.write("Count of items by 'type':")
                counts = df_items["type"].value_counts()
                st.bar_chart(counts)
            else:
                st.info("No 'type' field in this JSON to aggregate.")
    else:
        st.info("No parser logs yet. Run a parser first.")


# ===============================================================
# TAB 3: LOGS & VISUALIZATIONS
# ===============================================================
with tab_logs:
    st.header("📜 Scrape Logs")

    logs = load_logs()
    if logs:
        df_logs = pd.DataFrame(logs)
        st.dataframe(df_logs)

        if st.button("Export scrape logs to CSV"):
            df_logs.to_csv("scrape_logs.csv", index=False)
            st.success("Scrape logs exported to scrape_logs.csv")

        st.subheader("Scrape Success Count by Method")
        if "method" in df_logs.columns:
            method_counts = df_logs["method"].value_counts()
            st.bar_chart(method_counts)
    else:
        st.info("No scrape logs yet.")

    st.header("📜 Parser Logs")
    parser_logs = load_parser_logs()
    if parser_logs:
        df_parser = pd.DataFrame(parser_logs)
        st.dataframe(df_parser)

        st.subheader("Parser Usage by Type")
        if "parser_type" in df_parser.columns:
            parser_counts = df_parser["parser_type"].value_counts()
            st.bar_chart(parser_counts)
    else:
        st.info("No parser logs yet.")
