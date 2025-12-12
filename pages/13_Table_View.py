# pages/6_Select_Columns.py
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import re

HTML_DIR = "scraped_html"
SCRAPE_LOG_FILE = "scrape_log.json"

st.set_page_config(page_title="Column Selector", layout="wide")
st.title("🧩 Select Columns to Display (Wide JSON Table)")


# -----------------------------------------------------------
# Load JSON files
# -----------------------------------------------------------
all_files = os.listdir(HTML_DIR)
json_files = [f for f in all_files if f.endswith(".json")]

if len(json_files) == 0:
    st.info("No JSON files found in scraped_html/")
    st.stop()

selected_jsons = st.multiselect(
    "Choose JSON file(s):",
    json_files,
    key="col_selector_json_choice"
)

if len(selected_jsons) == 0:
    st.stop()


# -----------------------------------------------------------
# Load scrape logs (for scrape_url)
# -----------------------------------------------------------
scrape_logs = []
if os.path.exists(SCRAPE_LOG_FILE):
    scrape_logs = json.load(open(SCRAPE_LOG_FILE, "r"))

scrape_df = pd.DataFrame(scrape_logs) if scrape_logs else pd.DataFrame()


# -----------------------------------------------------------
# Helper: Extract metadata
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
# Build wide table
# -----------------------------------------------------------
rows = []

for json_file in selected_jsons:
    json_path = os.path.join(HTML_DIR, json_file)

    try:
        data = json.load(open(json_path, "r", encoding="utf-8"))
    except:
        st.error(f"Failed to load: {json_file}")
        continue

    timestamp, opp_id = extract_meta(json_file)

    # find matching scrape url
    scrape_url = None
    if opp_id and not scrape_df.empty:
        match = scrape_df[scrape_df["url"].str.contains(opp_id, na=False)]
        if len(match) > 0:
            scrape_url = match.iloc[0]["url"]

    record = {
        "json_file": json_file,
        "opportunity_id": opp_id,
        "timestamp": timestamp
    }

    for i, item in enumerate(data, start=1):
        record[f"level_{i}"] = item.get("level")
        record[f"content_{i}"] = item.get("content")
        record[f"scrape_url_{i}"] = scrape_url

    rows.append(record)

df = pd.DataFrame(rows)


# -----------------------------------------------------------
# Column Selection UI
# -----------------------------------------------------------
st.subheader("🧩 Choose Which Columns to Display")

all_columns = df.columns.tolist()

# Choose metadata columns (freeze)
metadata_cols = ["json_file", "opportunity_id", "timestamp"]

# Dynamic columns (the rest)
dynamic_cols = [c for c in all_columns if c not in metadata_cols]

selected_dynamic = st.multiselect(
    "Select dynamic columns (level_n, content_n, scrape_url_n):",
    dynamic_cols,
    default=dynamic_cols,  # start with all visible
    key="dynamic_col_selector"
)

# The final selected columns
selected_cols = metadata_cols + selected_dynamic

# -----------------------------------------------------------
# Display filtered table
# -----------------------------------------------------------
st.subheader("📄 Filtered Table")
st.dataframe(df[selected_cols], use_container_width=True)


# -----------------------------------------------------------
# Download CSV
# -----------------------------------------------------------
st.download_button(
    "⬇ Download Selected Columns CSV",
    df[selected_cols].to_csv(index=False),
    file_name="selected_columns.json_table.csv",
    mime="text/csv"
)
