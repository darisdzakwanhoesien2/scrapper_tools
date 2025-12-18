import streamlit as st
import os
import re
import json
import hashlib
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ======================================================
# CONFIG
# ======================================================
HTML_DIR = "scraped_html"
LOG_FILE = "scrape_log.json"

os.makedirs(HTML_DIR, exist_ok=True)

# ======================================================
# UTILITIES
# ======================================================
def extract_id(url):
    m = re.search(r"/opportunity/.+?/(\d+)", url)
    return m.group(1) if m else "unknown"


def compute_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def append_log(entry):
    logs = load_logs()
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def create_new_batch_id():
    logs = load_logs()
    batch_nums = []

    for l in logs:
        bid = l.get("batch_id", "")
        m = re.search(r"batch_(\d+)", bid)
        if m:
            batch_nums.append(int(m.group(1)))

    next_id = max(batch_nums) + 1 if batch_nums else 1
    return f"batch_{next_id:03d}"


def save_html_file(html_content, method, url, batch_id):
    op_id = extract_id(url)
    timestamp = datetime.utcnow().isoformat().replace(":", "-").split(".")[0]
    short_hash = compute_hash(html_content)[:8]

    filename = f"{timestamp}_{batch_id}_{method}_{op_id}_{short_hash}.html"
    path = os.path.join(HTML_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return path


# ======================================================
# REQUESTS SESSION WITH RETRIES
# ======================================================
def requests_retry_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def try_requests(url):
    try:
        s = requests_retry_session()
        r = s.get(url, timeout=12)
        if r.status_code == 200:
            return {"method": "Requests", "html": r.text}
    except Exception:
        pass
    return None


# ======================================================
# SINGLE URL SCRAPE
# ======================================================
def run_single_scrape(url, batch_id):
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        return {
            "batch_id": batch_id,
            "url": url,
            "status": "failed",
            "reason": "invalid_url",
        }

    res = try_requests(url)
    if not res:
        entry = {
            "batch_id": batch_id,
            "timestamp": datetime.utcnow().isoformat(),
            "url": url,
            "status": "failed",
            "reason": "request_failed",
        }
        append_log(entry)
        return entry

    html_path = save_html_file(res["html"], res["method"], url, batch_id)

    entry = {
        "batch_id": batch_id,
        "timestamp": datetime.utcnow().isoformat(),
        "url": url,
        "method": res["method"],
        "status": "success",
        "html_path": html_path,
    }

    append_log(entry)
    return entry


# ======================================================
# STREAMLIT UI
# ======================================================
st.set_page_config(page_title="Bulk Scraper", layout="wide")
st.title("🌍 Bulk URL Scraper (Batch-Aware)")

st.markdown(
    """
    **How this works**
    - One click = one batch
    - Each URL is scraped concurrently
    - All outputs are traceable via `batch_id`
    """
)

urls_text = st.text_area(
    "Enter one URL per line",
    height=250,
    placeholder="https://aiesec.org/opportunity/1330505\nhttps://aiesec.org/opportunity/1330447",
)

urls = [u.strip() for u in urls_text.splitlines() if u.strip()]

max_workers = st.slider("Concurrency", 1, 12, 6)

if st.button("🚀 Start Bulk Scraping"):
    if not urls:
        st.warning("No URLs provided")
        st.stop()

    batch_id = create_new_batch_id()
    st.info(f"📦 Starting batch `{batch_id}` with {len(urls)} URLs")

    progress = st.progress(0)
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {
            exe.submit(run_single_scrape, url, batch_id): url
            for url in urls
        }

        for i, fut in enumerate(as_completed(futures)):
            result = fut.result()
            results.append(result)
            progress.progress((i + 1) / len(urls))

    df = pd.DataFrame(results)

    st.success(f"✅ Batch `{batch_id}` completed")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Batch Results CSV",
        csv,
        file_name=f"{batch_id}_results.csv",
        mime="text/csv",
    )


# import streamlit as st
# import os
# import re
# import json
# import time
# import math
# import hashlib
# import urllib.parse
# from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import requests
# import pandas as pd
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry

# # -------------------------
# # Configuration
# # -------------------------
# HTML_DIR = "scraped_html"
# LOG_FILE = "scrape_log.json"
# os.makedirs(HTML_DIR, exist_ok=True)

# # -------------------------
# # Utilities
# # -------------------------
# def extract_id(url):
#     m = re.search(r"/opportunity/.+?/(\d+)", url)
#     return m.group(1) if m else "unknown"

# def compute_hash(content):
#     return hashlib.sha256(content.encode("utf-8")).hexdigest()

# def save_html_file(html_content, method, url):
#     op_id = extract_id(url)
#     timestamp = datetime.utcnow().isoformat().replace(":", "-").split(".")[0]
#     short_hash = compute_hash(html_content)[:8]

#     filename = f"{timestamp}_{method}_{op_id}_{short_hash}.html"
#     path = os.path.join(HTML_DIR, filename)

#     with open(path, "w", encoding="utf-8") as f:
#         f.write(html_content)

#     return path

# def load_logs():
#     if os.path.exists(LOG_FILE):
#         with open(LOG_FILE, "r") as f:
#             return json.load(f)
#     return []

# def append_log(entry):
#     logs = load_logs()
#     logs.append(entry)
#     with open(LOG_FILE, "w") as f:
#         json.dump(logs, f, indent=2)

# # -------------------------
# # Requests session
# # -------------------------
# def requests_retry_session():
#     session = requests.Session()
#     retry = Retry(
#         total=3,
#         backoff_factor=0.5,
#         status_forcelist=(500, 502, 503, 504),
#         allowed_methods=frozenset(["GET"])
#     )
#     adapter = HTTPAdapter(max_retries=retry)
#     session.mount("http://", adapter)
#     session.mount("https://", adapter)
#     return session

# # -------------------------
# # Scrape method
# # -------------------------
# def try_requests(url):
#     try:
#         s = requests_retry_session()
#         r = s.get(url, timeout=12)
#         if r.status_code == 200:
#             return {"method": "Requests", "html": r.text}
#     except:
#         return None

# # -------------------------
# # Orchestrator
# # -------------------------
# def run_single_scrape(url):
#     parsed = urllib.parse.urlparse(url)
#     if not parsed.scheme:
#         return {"url": url, "status": "failed", "reason": "invalid_url"}

#     res = try_requests(url)
#     if not res:
#         return {"url": url, "status": "failed"}

#     html_path = save_html_file(res["html"], res["method"], url)

#     log_entry = {
#         "timestamp": datetime.utcnow().isoformat(),
#         "url": url,
#         "method": res["method"],
#         "status": "success",
#         "html_path": html_path
#     }
#     append_log(log_entry)
#     return log_entry

# # -------------------------
# # Streamlit UI
# # -------------------------
# st.set_page_config(page_title="AIESEC Scraper", layout="wide")
# st.title("🌍 AIESEC URL Scraper")

# urls_text = st.text_area("Enter one URL per line")
# urls = [u.strip() for u in urls_text.splitlines() if u.strip()]

# if st.button("Start Scraping"):
#     if not urls:
#         st.warning("No URLs provided")
#         st.stop()

#     progress = st.progress(0)
#     results = []

#     with ThreadPoolExecutor(max_workers=6) as exe:
#         futures = {exe.submit(run_single_scrape, u): u for u in urls}
#         for i, fut in enumerate(as_completed(futures)):
#             results.append(fut.result())
#             progress.progress((i + 1) / len(urls))

#     st.success("Scraping complete")
#     st.dataframe(pd.DataFrame(results))


# import streamlit as st
# import os
# import importlib
# import json
# import pandas as pd
# from datetime import datetime

# # ===========================================
# # Paths (shared with scraper & parser suite)
# # ===========================================
# HTML_DIR = "scraped_html"
# PARSER_DIR = "parsers"
# PARSER_LOG_FILE = "parser_run_log.json"

# os.makedirs(HTML_DIR, exist_ok=True)
# os.makedirs(PARSER_DIR, exist_ok=True)

# # ===========================================
# # Utilities
# # ===========================================
# def load_parser_logs():
#     if os.path.exists(PARSER_LOG_FILE):
#         try:
#             with open(PARSER_LOG_FILE, "r") as f:
#                 return json.load(f)
#         except Exception:
#             return []
#     return []

# def save_parser_log(entry):
#     logs = load_parser_logs()
#     logs.append(entry)
#     with open(PARSER_LOG_FILE, "w") as f:
#         json.dump(logs, f, indent=2)

# def extract_datetime(fname):
#     try:
#         ts = fname.split("_")[0]
#         return datetime.strptime(ts, "%Y-%m-%dT%H-%M-%S")
#     except Exception:
#         return None

# # ===========================================
# # Streamlit UI
# # ===========================================
# st.set_page_config(page_title="Bulk Parse Scraped HTML", layout="wide")
# st.title("🔁 Scrape → Parse Pipeline (Bulk Parser Page)")

# st.markdown("""
# This page **connects directly to the scraper output**.

# Workflow:
# 1. Run scraper (URLs → HTML)
# 2. Come here
# 3. Select a parser
# 4. Bulk-parse all or selected HTML files
# """)

# # ===========================================
# # Load files
# # ===========================================
# html_files = sorted([f for f in os.listdir(HTML_DIR) if f.endswith(".html")])
# json_files = [f for f in os.listdir(HTML_DIR) if f.endswith(".json")]
# parser_files = [f for f in os.listdir(PARSER_DIR) if f.endswith(".py")]

# if not html_files:
#     st.warning("No HTML files found. Run the scraper first.")
#     st.stop()

# if not parser_files:
#     st.error("No parsers found in /parsers/")
#     st.stop()

# # ===========================================
# # Parsed vs unparsed detection
# # ===========================================
# parsed_html = []
# unparsed_html = []

# for html in html_files:
#     base = html.replace(".html", "")
#     if any(j.startswith(base) for j in json_files):
#         parsed_html.append(html)
#     else:
#         unparsed_html.append(html)

# # ===========================================
# # Filters
# # ===========================================
# st.subheader("📅 Optional Date Filter")
# selected_date = st.date_input("Only show HTML from date (optional)", None)

# if selected_date:
#     unparsed_html = [
#         f for f in unparsed_html
#         if extract_datetime(f) and extract_datetime(f).date() == selected_date
#     ]

# # ===========================================
# # Display
# # ===========================================
# col1, col2 = st.columns(2)

# with col1:
#     st.subheader("❌ Unparsed HTML")
#     st.dataframe(pd.DataFrame({"html": unparsed_html}), use_container_width=True)

# with col2:
#     st.subheader("✅ Already Parsed")
#     st.dataframe(pd.DataFrame({"html": parsed_html}), use_container_width=True)

# # ===========================================
# # Bulk parser controls
# # ===========================================
# st.markdown("---")
# st.subheader("⚙ Bulk Parse Controls")

# parser_choice = st.selectbox(
#     "Choose parser to apply:",
#     parser_files
# )

# selection_mode = st.radio(
#     "Which files to parse?",
#     ["All unparsed HTML", "Manually select"],
#     horizontal=True
# )

# if selection_mode == "Manually select":
#     selected_html = st.multiselect(
#         "Select HTML files:",
#         unparsed_html
#     )
# else:
#     selected_html = unparsed_html

# # ===========================================
# # Run bulk parsing
# # ===========================================
# if st.button("▶ Run Bulk Parsing"):

#     if not selected_html:
#         st.warning("No HTML files selected.")
#         st.stop()

#     module_name = parser_choice.replace(".py", "")
#     module = importlib.import_module(f"{PARSER_DIR}.{module_name}")

#     if not hasattr(module, "run_parser"):
#         st.error("Parser must implement run_parser(html_path, output_json_path)")
#         st.stop()

#     st.info(f"Running parser on {len(selected_html)} files…")
#     progress = st.progress(0)

#     results = []

#     for i, html_file in enumerate(selected_html):
#         html_path = os.path.join(HTML_DIR, html_file)
#         output_json_path = html_path.replace(".html", f"_{module_name}.json")

#         try:
#             success, result = module.run_parser(html_path, output_json_path)
#             items = len(result) if success and isinstance(result, list) else None
#             status = "success" if success else "failed"
#         except Exception as e:
#             success = False
#             result = str(e)
#             items = None
#             status = "failed"

#         log_entry = {
#             "timestamp": datetime.utcnow().isoformat(),
#             "parser_name": module_name,
#             "status": status,
#             "html_file_path": html_path,
#             "output_json_path": output_json_path,
#             "items_extracted": items
#         }

#         save_parser_log(log_entry)
#         results.append(log_entry)

#         progress.progress((i + 1) / len(selected_html))

#     st.success("🎉 Bulk parsing finished")

#     df = pd.DataFrame(results)
#     st.subheader("📄 Parsing Summary")
#     st.dataframe(df, use_container_width=True)

#     st.download_button(
#         "⬇ Download CSV Summary",
#         df.to_csv(index=False),
#         file_name="bulk_parse_from_scraper.csv"
#     )
