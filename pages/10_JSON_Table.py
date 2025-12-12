# pages/5_JSON_Table.py
import streamlit as st
import os
import json
import pandas as pd

HTML_DIR = "scraped_html"
st.set_page_config(page_title="JSON → Table", layout="wide")
st.header("📄 JSON → Table Viewer / Exporter")

all_files = os.listdir(HTML_DIR)
json_files = [f for f in all_files if f.endswith(".json")]

if len(json_files) == 0:
    st.info("No JSON files found in scraped_html/")
    st.stop()

selected_json = st.selectbox("Choose JSON file to convert:", json_files, key="json_table_file_selector")
json_path = os.path.join(HTML_DIR, selected_json)

try:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    st.error(f"Failed to load JSON: {e}")
    st.stop()

# Normalize to rows
rows = []
for item in data:
    rows.append({
        "filename": selected_json,
        "type": item.get("type"),
        "level": item.get("level"),
        "content": item.get("content")
    })
df = pd.DataFrame(rows)

st.subheader("JSON as Table")
st.dataframe(df, use_container_width=True)

st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name=selected_json.replace(".json", ".csv"), mime="text/csv")

search = st.text_input("Search content", key="json_table_search")
if search.strip():
    filtered = df[df["content"].str.contains(search, case=False, na=False)]
    st.subheader("Search Results")
    st.dataframe(filtered, use_container_width=True)
