import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime

HTML_DIR = "scraped_html"

st.set_page_config(page_title="JSON Viewer", layout="wide")
st.title("📄 JSON Output Viewer")
st.write("View, filter, search, and preview all parsed JSON files.")


# ========================================
# LOAD ALL JSON FILES
# ========================================
all_files = os.listdir(HTML_DIR)
json_files = [f for f in all_files if f.endswith(".json")]

if len(json_files) == 0:
    st.info("No JSON files found in scraped_html/")
    st.stop()


# ========================================
# Extract date + base filename
# ========================================
def extract_datetime_from_filename(fname):
    try:
        # Example filename:
        # 2025-12-11T07-59-16_Requests_1322886_parse_html_to_json_v2.json
        timestamp = fname.split("_")[0]  # Before first underscore
        return datetime.strptime(timestamp, "%Y-%m-%dT%H-%M-%S")
    except:
        return None


# Build table metadata
json_metadata = []

for f in json_files:
    dt = extract_datetime_from_filename(f)
    json_metadata.append({
        "filename": f,
        "datetime": dt,
        "date": dt.date() if dt else None,
        "size_kb": round(os.path.getsize(os.path.join(HTML_DIR, f)) / 1024, 1)
    })

df = pd.DataFrame(json_metadata)


# ========================================
# FILTERING CONTROLS
# ========================================
st.subheader("🔍 Filter JSON Files")

col1, col2 = st.columns(2)

with col1:
    selected_date = st.date_input("Filter by date", None)

with col2:
    keyword_filter = st.text_input("Search keyword in filename", "")


filtered_df = df.copy()

if selected_date:
    filtered_df = filtered_df[ filtered_df["date"] == selected_date ]

if keyword_filter.strip():
    filtered_df = filtered_df[ filtered_df["filename"].str.contains(keyword_filter, case=False) ]


# ========================================
# DISPLAY FILTERED LIST
# ========================================
st.subheader("📂 JSON Files")

if filtered_df.empty:
    st.warning("No JSON files match the filter.")
else:
    st.dataframe(filtered_df, use_container_width=True)


# ========================================
# PREVIEW SELECTED JSON
# ========================================
st.subheader("📄 Preview JSON Content")

selected_json = st.selectbox(
    "Choose JSON file to preview:",
    filtered_df["filename"] if not filtered_df.empty else json_files,
    key="json_preview_selector"
)

if selected_json:
    json_path = os.path.join(HTML_DIR, selected_json)
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Show preview
        st.json(data)

        # Download button
        st.download_button(
            label="⬇ Download JSON",
            data=json.dumps(data, indent=4),
            file_name=selected_json,
            mime="application/json"
        )

    except Exception as e:
        st.error(f"Error reading file: {e}")

