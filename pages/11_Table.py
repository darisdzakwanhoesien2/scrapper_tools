# pages/5_JSON_Table.py
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import re

HTML_DIR = "scraped_html"
SCRAPE_LOG_FILE = "scrape_log.json"
PARSER_LOG_FILE = "parser_run_log.json"

st.set_page_config(page_title="JSON → Table", layout="wide")
st.header("📄 Multi-JSON → Multi-Column Table Viewer / Exporter")

# ===============================================================
# Load JSON files
# ===============================================================
all_files = os.listdir(HTML_DIR)
json_files = [f for f in all_files if f.endswith(".json")]

if len(json_files) == 0:
    st.info("No JSON files found in scraped_html/")
    st.stop()

selected_jsons = st.multiselect(
    "Choose JSON file(s) to convert:",
    json_files,
    key="json_table_multi_selector"
)

if len(selected_jsons) == 0:
    st.info("Select at least one JSON file.")
    st.stop()


# ===============================================================
# Load logs for metadata enrichment
# ===============================================================
scrape_logs = []
parser_logs = []

if os.path.exists(SCRAPE_LOG_FILE):
    scrape_logs = json.load(open(SCRAPE_LOG_FILE, "r"))

if os.path.exists(PARSER_LOG_FILE):
    parser_logs = json.load(open(PARSER_LOG_FILE, "r"))

scrape_df = pd.DataFrame(scrape_logs) if len(scrape_logs) else pd.DataFrame()
parser_df = pd.DataFrame(parser_logs) if len(parser_logs) else pd.DataFrame()


# ===============================================================
# Helper: Extract timestamp + ID from filename
# Example: 2025-12-11T07-59-18_Requests_1293818.html
# Or      2025-12-11T07-59-18_Requests_1293818_parse_v1.json
# ===============================================================
def extract_meta(filename):
    try:
        timestamp_str = filename.split("_")[0]  # 2025-12-11T07-59-18
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M-%S")
    except:
        timestamp = None

    m = re.search(r"_(\d+)", filename)
    opportunity_id = m.group(1) if m else None

    return timestamp, opportunity_id



# ===============================================================
# Build unified table from all selected JSON files
# ===============================================================
rows = []

for json_file in selected_jsons:
    json_path = os.path.join(HTML_DIR, json_file)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Failed to load JSON {json_path}: {e}")
        continue

    timestamp, opportunity_id = extract_meta(json_file)

    # Find matching scrape log
    matching_scrape = None
    if not scrape_df.empty:
        matches = scrape_df[scrape_df["html_path"].str.contains(opportunity_id, na=False)]
        if len(matches) > 0:
            matching_scrape = matches.iloc[0].to_dict()

    # Find matching parser log
    matching_parser = None
    if not parser_df.empty:
        matches = parser_df[parser_df["html_file_path"].str.contains(opportunity_id, na=False)]
        if len(matches) > 0:
            matching_parser = matches.iloc[0].to_dict()

    for item in data:
        rows.append({
            "json_file": json_file,
            "opportunity_id": opportunity_id,
            "timestamp": timestamp,
            "type": item.get("type"),
            "level": item.get("level"),
            "content": item.get("content"),

            # Add metadata from logs
            "scrape_method": matching_scrape.get("method") if matching_scrape else None,
            "scrape_url": matching_scrape.get("url") if matching_scrape else None,

            "parser_name": matching_parser.get("parser_name") if matching_parser else None,
            "parser_status": matching_parser.get("status") if matching_parser else None,
        })

df = pd.DataFrame(rows)



# ===============================================================
# Display table
# ===============================================================
st.subheader("📊 Combined Multi-JSON Table")
st.dataframe(df, use_container_width=True)


# ===============================================================
# Search
# ===============================================================
search = st.text_input("🔎 Search in content", key="json_multi_search")

if search.strip():
    df_filtered = df[df["content"].str.contains(search, case=False, na=False)]
    st.subheader("Search Results")
    st.dataframe(df_filtered, use_container_width=True)


# ===============================================================
# Export CSV
# ===============================================================
csv_data = df.to_csv(index=False)
st.download_button(
    "⬇ Download Combined CSV",
    csv_data,
    file_name="combined_json_table.csv",
    mime="text/csv"
)
