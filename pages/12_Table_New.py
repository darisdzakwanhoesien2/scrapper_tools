import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import re

HTML_DIR = "scraped_html"
SCRAPE_LOG_FILE = "scrape_log.json"
PARSER_LOG_FILE = "parser_run_log.json"

st.set_page_config(page_title="JSON → Wide Table", layout="wide")
st.header("📄 Multi-JSON → Wide Table Converter (level_n, content_n, scrape_url_n)")

# -----------------------------------------------------------
# Load JSON files
# -----------------------------------------------------------
all_files = os.listdir(HTML_DIR)
json_files = [f for f in all_files if f.endswith(".json")]

if len(json_files) == 0:
    st.info("No JSON files found in scraped_html/")
    st.stop()

selected_jsons = st.multiselect(
    "Choose JSON file(s) to convert:",
    json_files,
    key="json_table_wide_selector"
)

if len(selected_jsons) == 0:
    st.stop()


# -----------------------------------------------------------
# Load scrape logs (to get scrape_url)
# -----------------------------------------------------------
scrape_logs = []
if os.path.exists(SCRAPE_LOG_FILE):
    scrape_logs = json.load(open(SCRAPE_LOG_FILE, "r"))

scrape_df = pd.DataFrame(scrape_logs) if scrape_logs else pd.DataFrame()


# -----------------------------------------------------------
# Helper: Extract timestamp + ID from filename
# -----------------------------------------------------------
def extract_meta(filename):
    try:
        timestamp_str = filename.split("_")[0]
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M-%S")
    except:
        timestamp = None

    m = re.search(r"_(\d+)", filename)
    opportunity_id = m.group(1) if m else None

    return timestamp, opportunity_id


# -----------------------------------------------------------
# Convert each JSON to WIDE format (one row)
# -----------------------------------------------------------
rows = []

for json_file in selected_jsons:
    json_path = os.path.join(HTML_DIR, json_file)

    try:
        data = json.load(open(json_path, "r", encoding="utf-8"))
    except:
        st.error(f"Failed to load JSON: {json_path}")
        continue

    timestamp, opp_id = extract_meta(json_file)

    # find scrape_url from scrape logs
    scrape_url = None
    if not scrape_df.empty and opp_id:
        matched = scrape_df[scrape_df["url"].str.contains(opp_id, na=False)]
        if len(matched) > 0:
            scrape_url = matched.iloc[0]["url"]

    # Convert into wide columns
    wide_record = {
        "json_file": json_file,
        "opportunity_id": opp_id,
        "timestamp": timestamp,
    }

    for idx, item in enumerate(data, start=1):
        level = item.get("level")
        content = item.get("content")

        wide_record[f"level_{idx}"]   = level
        wide_record[f"content_{idx}"] = content
        wide_record[f"scrape_url_{idx}"] = scrape_url  # same URL for every item

    rows.append(wide_record)


df = pd.DataFrame(rows)


# -----------------------------------------------------------
# Show table
# -----------------------------------------------------------
st.subheader("📊 Wide Format Table (1 row per JSON)")
st.dataframe(df, use_container_width=True)


# -----------------------------------------------------------
# Search across all columns
# -----------------------------------------------------------
search = st.text_input("🔎 Search any content", key="wide_search")

if search.strip():
    mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False, na=False).any(), axis=1)
    filtered = df[mask]

    st.subheader("Search Results")
    st.dataframe(filtered, use_container_width=True)


# -----------------------------------------------------------
# Download CSV
# -----------------------------------------------------------
csv = df.to_csv(index=False)
st.download_button(
    "⬇ Download Wide CSV",
    csv,
    file_name="wide_json_table.csv",
    mime="text/csv"
)
