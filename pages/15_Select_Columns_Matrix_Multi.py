# pages/14_Select_Columns_Matrix_Multi.py
import streamlit as st
import os
import json
import re
import pandas as pd
from datetime import datetime

HTML_DIR = "scraped_html"
SCRAPE_LOG_FILE = "scrape_log.json"

st.set_page_config(page_title="Multi-JSON Matrix Selector", layout="wide")
st.title("🧩 Multi-JSON Tick-Box Matrix → Wide Table (Content Only)")


# -----------------------------------------------------------
# Load JSON files
# -----------------------------------------------------------
all_files = os.listdir(HTML_DIR)
json_files = [f for f in all_files if f.endswith(".json")]

if not json_files:
    st.info("No JSON files available.")
    st.stop()


selected_jsons = st.multiselect(
    "Choose JSON files:",
    json_files,
    key="matrix_multi_json_select"
)

if len(selected_jsons) == 0:
    st.stop()


# -----------------------------------------------------------
# Load scrape logs for URLs
# -----------------------------------------------------------
scrape_url_map = {}

if os.path.exists(SCRAPE_LOG_FILE):
    logs = json.load(open(SCRAPE_LOG_FILE, "r"))
    logs_df = pd.DataFrame(logs)

    for js in selected_jsons:
        m = re.search(r"_(\d+)", js)
        opp_id = m.group(1) if m else None

        if opp_id and not logs_df.empty:
            match = logs_df[logs_df["url"].str.contains(opp_id, na=False)]
            if len(match) > 0:
                scrape_url_map[js] = match.iloc[0]["url"]
            else:
                scrape_url_map[js] = None
        else:
            scrape_url_map[js] = None


# -----------------------------------------------------------
# Helper: extract metadata
# -----------------------------------------------------------
def extract_meta(filename):
    try:
        ts = filename.split("_")[0]
        ts = datetime.strptime(ts, "%Y-%m-%dT%H-%M-%S")
    except:
        ts = None

    m = re.search(r"_(\d+)", filename)
    opp_id = m.group(1) if m else None

    return ts, opp_id


# -----------------------------------------------------------
# MASTER: Final wide table rows
# -----------------------------------------------------------
final_rows = []


# -----------------------------------------------------------
# Process each JSON FILE with its own tick-box matrix
# -----------------------------------------------------------
for json_file in selected_jsons:

    st.markdown("---")
    st.subheader(f"📄 Matrix for: `{json_file}`")

    json_path = os.path.join(HTML_DIR, json_file)
    data = json.load(open(json_path, "r", encoding="utf-8"))
    N = len(data)

    ts, opp_id = extract_meta(json_file)
    scrape_url = scrape_url_map.get(json_file)

    # Store checkbox states separately per JSON file
    state_key = f"checks_{json_file}"

    if state_key not in st.session_state:
        st.session_state[state_key] = {i: True for i in range(1, N + 1)}

    checks = st.session_state[state_key]

    # ---------- QUICK SELECTION ----------
    colA, colB, colC = st.columns(3)

    if colA.button(f"Select All ({json_file})"):
        st.session_state[state_key] = {i: True for i in range(1, N + 1)}

    if colB.button(f"Unselect All ({json_file})"):
        st.session_state[state_key] = {i: False for i in range(1, N + 1)}

    if colC.button(f"Invert Selection ({json_file})"):
        st.session_state[state_key] = {i: not checks[i] for i in range(1, N + 1)}

    checks = st.session_state[state_key]

    # ---------- MATRIX TABLE ----------
    for idx in range(1, N + 1):
        item = data[idx - 1]
        text = item.get("content") or "(empty)"

        st.checkbox(
            f"[{idx}] {text}",
            key=f"{state_key}_{idx}",
            value=checks[idx],
            on_change=lambda x=idx: st.session_state[state_key].update(
                {x: st.session_state[f"{state_key}_{x}"]}
            )
        )

    # ---------- BUILD WIDE ROW ----------
    selected_indices = [i for i in range(1, N + 1) if checks[i]]

    wide_row = {
        "json_file": json_file,
        "opportunity_id": opp_id,
        "scrape_url": scrape_url,
        "timestamp": ts
    }

    col_n = 1
    for idx in selected_indices:
        item = data[idx - 1]
        wide_row[f"content_{col_n}"] = item.get("content")
        col_n += 1

    final_rows.append(wide_row)


# # -----------------------------------------------------------
# # Combine into final DataFrame
# # -----------------------------------------------------------
# st.markdown("---")
# st.subheader("📊 Final Combined Table")

# df_final = pd.DataFrame(final_rows)
# st.dataframe(df_final, use_container_width=True)

# -----------------------------------------------------------
# Combine into final DataFrame
# -----------------------------------------------------------
st.markdown("---")
st.subheader("📊 Final Combined Table (Transposed Format)")

df_final = pd.DataFrame(final_rows)

# Transpose: rows → columns
df_transposed = df_final.set_index("json_file").T

st.dataframe(df_transposed, use_container_width=True)

# -----------------------------------------------------------
# Download CSV (transposed)
# -----------------------------------------------------------
csv = df_transposed.to_csv()

st.download_button(
    "⬇ Download Transposed CSV",
    csv,
    file_name="selected_items_multi_json_transposed.csv",
    mime="text/csv"
)


# -----------------------------------------------------------
# Download CSV
# -----------------------------------------------------------
csv = df_final.to_csv(index=False)
st.download_button(
    "⬇ Download Combined CSV",
    csv,
    file_name="selected_items_multi_json.csv",
    mime="text/csv"
)
