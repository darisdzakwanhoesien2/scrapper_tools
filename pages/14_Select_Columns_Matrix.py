# pages/14_Select_Columns_Matrix.py
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import re

HTML_DIR = "scraped_html"
SCRAPE_LOG_FILE = "scrape_log.json"

st.set_page_config(page_title="Matrix Column Selector", layout="wide")
st.title("🧩 Tick-Box Matrix (Content Only) → Wide Table")


# -----------------------------------------------------------
# Load JSON files
# -----------------------------------------------------------
all_files = os.listdir(HTML_DIR)
json_files = [f for f in all_files if f.endswith(".json")]

if not json_files:
    st.info("No JSON files found.")
    st.stop()

selected_json = st.selectbox("Choose JSON file:", json_files)

json_path = os.path.join(HTML_DIR, selected_json)
data = json.load(open(json_path, "r", encoding="utf-8"))

# Number of items in JSON
N = len(data)


# -----------------------------------------------------------
# Load scrape URL from logs
# -----------------------------------------------------------
scrape_url = None
op_id = None

if os.path.exists(SCRAPE_LOG_FILE):
    logs = json.load(open(SCRAPE_LOG_FILE, "r"))
    logs_df = pd.DataFrame(logs)

    # Extract numeric ID from filename
    m = re.search(r"_(\d+)", selected_json)
    op_id = m.group(1) if m else None

    if op_id:
        match = logs_df[logs_df["url"].str.contains(op_id, na=False)]
        if len(match) > 0:
            scrape_url = match.iloc[0]["url"]


# -----------------------------------------------------------
# Initialize checkbox states *per JSON file*
# -----------------------------------------------------------
state_key = f"matrix_checks_{selected_json}"

if state_key not in st.session_state:
    # By default: include all items
    st.session_state[state_key] = {i: True for i in range(1, N + 1)}

checks = st.session_state[state_key]


# -----------------------------------------------------------
# Quick selection controls
# -----------------------------------------------------------
st.write("### Quick Controls")

colA, colB, colC = st.columns(3)

if colA.button("Select All"):
    st.session_state[state_key] = {i: True for i in range(1, N + 1)}

if colB.button("Unselect All"):
    st.session_state[state_key] = {i: False for i in range(1, N + 1)}

if colC.button("Invert Selection"):
    st.session_state[state_key] = {i: not checks[i] for i in range(1, N + 1)}

checks = st.session_state[state_key]  # refreshed


# -----------------------------------------------------------
# Tick-Box Matrix
# -----------------------------------------------------------
st.subheader("📋 Select Items to Keep")

for idx in range(1, N + 1):
    item = data[idx - 1]
    text = item.get("content") or "(empty)"

    st.checkbox(
        f"Include item {idx}: {text}",
        key=f"{state_key}_{idx}",
        value=checks.get(idx, False),
        on_change=lambda i=idx: st.session_state[state_key].update(
            {i: st.session_state[f"{state_key}_{i}"]}
        )
    )


# -----------------------------------------------------------
# Collect selected items
# -----------------------------------------------------------
selected_indices = [
    i for i in range(1, N + 1)
    if st.session_state[state_key].get(i, False)
]

if not selected_indices:
    st.warning("No items selected.")
    st.stop()


# -----------------------------------------------------------
# Build the final WIDE table (content only)
# -----------------------------------------------------------
wide_row = {
    "json_file": selected_json,
    "opportunity_id": op_id,
    "scrape_url": scrape_url,
}

# Fill content_n columns
for col_num, item_index in enumerate(selected_indices, start=1):
    item = data[item_index - 1]
    wide_row[f"content_{col_num}"] = item.get("content")

df_output = pd.DataFrame([wide_row])


# -----------------------------------------------------------
# Show results
# -----------------------------------------------------------
st.subheader("📊 Final Table (Content Only)")
st.dataframe(df_output, use_container_width=True)

# Download CSV
csv = df_output.to_csv(index=False)
st.download_button(
    "⬇ Download Selected Items CSV",
    csv,
    file_name=f"selected_items_{selected_json}.csv",
    mime="text/csv"
)


# # pages/6_Select_Columns_Matrix.py
# import streamlit as st
# import os
# import json
# import pandas as pd
# from datetime import datetime
# import re

# HTML_DIR = "scraped_html"
# SCRAPE_LOG_FILE = "scrape_log.json"

# st.set_page_config(page_title="Matrix Column Selector", layout="wide")
# st.title("🧩 Tick-Box Matrix: Select Which Items to Include in Final Table")


# # -----------------------------------------------------------
# # Load JSON files
# # -----------------------------------------------------------
# all_files = os.listdir(HTML_DIR)
# json_files = [f for f in all_files if f.endswith(".json")]

# if len(json_files) == 0:
#     st.info("No JSON files found.")
#     st.stop()

# selected_json = st.selectbox("Choose JSON file:", json_files)

# json_path = os.path.join(HTML_DIR, selected_json)
# data = json.load(open(json_path, "r", encoding="utf-8"))


# # -----------------------------------------------------------
# # Load scrape logs (to locate scrape_url)
# # -----------------------------------------------------------
# scrape_url = None
# op_id = None

# if os.path.exists(SCRAPE_LOG_FILE):
#     logs = json.load(open(SCRAPE_LOG_FILE, "r"))
#     df_logs = pd.DataFrame(logs)

#     # Extract numeric ID from filename
#     m = re.search(r"_(\d+)", selected_json)
#     op_id = m.group(1) if m else None

#     if op_id:
#         match = df_logs[df_logs["url"].str.contains(op_id, na=False)]
#         if len(match) > 0:
#             scrape_url = match.iloc[0]["url"]


# # -----------------------------------------------------------
# # Build matrix table of items
# # -----------------------------------------------------------
# st.subheader("📋 Select Which Items to Keep (Matrix Style)")

# # Prepare table for display
# matrix_rows = []
# for i, item in enumerate(data, start=1):
#     matrix_rows.append({
#         "index": i,
#         "level": item.get("level"),
#         "content": item.get("content")
#     })

# df_matrix = pd.DataFrame(matrix_rows)

# # -----------------------------------------------------------
# # Global selection buttons
# # -----------------------------------------------------------
# st.write("### Quick Controls")

# if "checkbox_states" not in st.session_state:
#     st.session_state.checkbox_states = {i: True for i in df_matrix["index"]}

# colA, colB, colC = st.columns(3)
# if colA.button("Select All"):
#     for i in df_matrix["index"]:
#         st.session_state.checkbox_states[i] = True

# if colB.button("Unselect All"):
#     for i in df_matrix["index"]:
#         st.session_state.checkbox_states[i] = False

# if colC.button("Invert Selection"):
#     for i in df_matrix["index"]:
#         st.session_state.checkbox_states[i] = not st.session_state.checkbox_states[i]


# # -----------------------------------------------------------
# # Show matrix with checkboxes
# # -----------------------------------------------------------
# st.write("### Tick-Box Matrix")

# for i, row in df_matrix.iterrows():
#     idx = row["index"]

#     st.checkbox(
#         f"Include item {idx}: {row['content']}",
#         key=f"item_select_{idx}",
#         value=st.session_state.checkbox_states[idx],
#         on_change=lambda x=idx: st.session_state.checkbox_states.update({x: st.session_state[f'item_select_{x}']})
#     )


# # -----------------------------------------------------------
# # Build final wide table using ONLY selected items
# # -----------------------------------------------------------
# selected_indexes = [i for i, checked in st.session_state.checkbox_states.items() if checked]

# if len(selected_indexes) == 0:
#     st.warning("No items selected – nothing to export.")
#     st.stop()


# # -----------------------------------------------------------
# # Build output row
# # -----------------------------------------------------------
# wide_row = {
#     "json_file": selected_json,
#     "opportunity_id": op_id,
#     "scrape_url": scrape_url
# }

# for col_num, item_index in enumerate(selected_indexes, start=1):
#     item = data[item_index - 1]

#     wide_row[f"level_{col_num}"] = item.get("level")
#     wide_row[f"content_{col_num}"] = item.get("content")

# df_output = pd.DataFrame([wide_row])

# st.subheader("📊 Final Table (Based on Selected Items)")
# st.dataframe(df_output, use_container_width=True)


# # -----------------------------------------------------------
# # Download CSV
# # -----------------------------------------------------------
# csv = df_output.to_csv(index=False)
# st.download_button(
#     "⬇ Download Selected Items as CSV",
#     csv,
#     file_name=f"selected_items_{selected_json}.csv",
#     mime="text/csv"
# )
