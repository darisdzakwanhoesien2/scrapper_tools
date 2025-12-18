import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================
HTML_DIR = "scraped_html"

st.set_page_config(
    page_title="Multi-JSON Content & Metadata Matrix",
    layout="wide"
)

st.title("🧩 Multi-JSON Content Selector → Content + Metadata Tables")

# =========================================================
# HELPERS
# =========================================================
def extract_filename_metadata(filename):
    """
    Expected filename format:
    2025-12-14T06-17-23_Requests_unknown.json
    """
    ts = ""
    opp = ""

    try:
        base = os.path.splitext(filename)[0]
        ts_part, opp_part = base.split("_", 1)
        ts = ts_part.replace("-", ":", 2)
        opp = opp_part
    except:
        pass

    return ts, opp


def extract_metadata_row(json_file, data):
    meta = data.get("metadata", {}) if isinstance(data, dict) else {}
    structured = data.get("structured_content", [])

    paragraphs = [b for b in structured if b.get("type") == "paragraph"]
    headings = [b for b in structured if b.get("type") == "heading"]

    ts, opp_id = extract_filename_metadata(json_file)

    return {
        "json_file": json_file,
        "timestamp": ts,
        "opportunity_id": opp_id,

        # ---- Page identity ----
        "title": data.get("title", "").strip(),
        "description": meta.get("description", "").strip(),
        "og_title": meta.get("og:title", ""),
        "og_description": meta.get("og:description", ""),
        "og_url": meta.get("og:url", ""),
        "site_name": meta.get("og:site_name", ""),
        "generator": meta.get("Generator", ""),

        # ---- Structural stats ----
        "num_links": len(data.get("links", [])),
        "num_images": len(data.get("images", [])),
        "num_structured_blocks": len(structured),
        "num_headings": len(headings),
        "num_paragraphs": len(paragraphs),

        # ---- Content size ----
        "text_length": len(data.get("all_text", "")),
    }


# =========================================================
# LOAD JSON FILES
# =========================================================
if not os.path.exists(HTML_DIR):
    st.error(f"Directory not found: {HTML_DIR}")
    st.stop()

json_files = sorted([
    f for f in os.listdir(HTML_DIR)
    if f.endswith(".json")
])

if not json_files:
    st.info("No JSON files found.")
    st.stop()

selected_jsons = st.multiselect(
    "📂 Select JSON files",
    json_files
)

if not selected_jsons:
    st.stop()


# =========================================================
# METADATA TABLE (TRANSPOSED)
# =========================================================
st.markdown("---")
st.header("🧾 Metadata Overview (Transposed)")

metadata_rows = []

for json_file in selected_jsons:
    try:
        data = json.load(open(os.path.join(HTML_DIR, json_file), "r", encoding="utf-8"))
        metadata_rows.append(extract_metadata_row(json_file, data))
    except Exception as e:
        st.error(f"Metadata error for {json_file}: {e}")

if not metadata_rows:
    st.info("No metadata available.")
    st.stop()

# ---------------------------------------------------------
# Build metadata DataFrame
# ---------------------------------------------------------
df_meta = pd.DataFrame(metadata_rows)

# Column order (important for readability before transpose)
preferred_order = [
    "json_file", "timestamp", "opportunity_id",
    "title", "site_name", "og_url",
    "description", "og_title", "og_description",
    "num_links", "num_images",
    "num_structured_blocks", "num_headings", "num_paragraphs",
    "text_length", "generator"
]

df_meta = df_meta[[c for c in preferred_order if c in df_meta.columns]]

# ---------------------------------------------------------
# TRANSPOSE
# ---------------------------------------------------------
df_meta_t = df_meta.set_index("json_file").T

# ---------------------------------------------------------
# CSV DOWNLOAD
# ---------------------------------------------------------
csv_meta = df_meta_t.to_csv().encode("utf-8")

st.download_button(
    "⬇️ Download Metadata CSV (Transposed)",
    csv_meta,
    file_name=f"metadata_transposed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)

# ---------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------
st.dataframe(df_meta_t, use_container_width=True)

# =========================================================
# CONTENT SELECTION
# =========================================================
final_rows = []

for json_file in selected_jsons:
    st.markdown("---")
    st.subheader(f"📄 {json_file}")

    path = os.path.join(HTML_DIR, json_file)

    try:
        data = json.load(open(path, "r", encoding="utf-8"))
    except Exception as e:
        st.error(f"Failed to load JSON: {e}")
        continue

    # -----------------------------------------------------
    # Extract content blocks
    # -----------------------------------------------------
    blocks = []

    if isinstance(data, dict):
        if isinstance(data.get("structured_content"), list):
            for b in data["structured_content"]:
                txt = b.get("content")
                if txt and txt.strip():
                    blocks.append(txt.strip())
        elif data.get("all_text", "").strip():
            blocks.append(data["all_text"].strip())

    if not blocks:
        st.warning("No content blocks found.")
        continue

    N = len(blocks)
    ts, opp_id = extract_filename_metadata(json_file)

    # -----------------------------------------------------
    # Session state
    # -----------------------------------------------------
    state_key = f"checks_{json_file}"

    if state_key not in st.session_state:
        st.session_state[state_key] = {i: True for i in range(N)}

    checks = st.session_state[state_key]

    # -----------------------------------------------------
    # Action buttons
    # -----------------------------------------------------
    c1, c2, c3 = st.columns(3)

    if c1.button("✅ Select All", key=f"all_{json_file}"):
        st.session_state[state_key] = {i: True for i in range(N)}

    if c2.button("❌ Unselect All", key=f"none_{json_file}"):
        st.session_state[state_key] = {i: False for i in range(N)}

    if c3.button("🔁 Invert", key=f"invert_{json_file}"):
        st.session_state[state_key] = {
            i: not checks[i] for i in range(N)
        }

    checks = st.session_state[state_key]

    # -----------------------------------------------------
    # Checkboxes
    # -----------------------------------------------------
    for i, text in enumerate(blocks):
        preview = text[:150].replace("\n", " ")
        if len(text) > 150:
            preview += "..."

        st.checkbox(
            f"[{i+1}] {preview}",
            key=f"{state_key}_{i}",
            value=checks[i],
            on_change=lambda idx=i: st.session_state[state_key].update(
                {idx: st.session_state[f"{state_key}_{idx}"]}
            )
        )

    # -----------------------------------------------------
    # Build content row
    # -----------------------------------------------------
    row = {
        "json_file": json_file,
        "opportunity_id": opp_id,
        "timestamp": ts
    }

    col_idx = 1
    for i in range(N):
        if checks[i]:
            row[f"content_{col_idx}"] = blocks[i]
            col_idx += 1

    final_rows.append(row)

# =========================================================
# CONTENT MATRIX TABLE
# =========================================================
st.markdown("---")
st.header("📊 Selected Content Matrix (Transposed)")

if final_rows:
    df_content = pd.DataFrame(final_rows)

    meta_cols = [c for c in ["json_file", "opportunity_id", "timestamp"] if c in df_content.columns]
    content_cols = sorted([c for c in df_content.columns if c.startswith("content_")])

    df_content = df_content[meta_cols + content_cols]
    df_content_t = df_content.set_index("json_file").T

    csv_content = df_content_t.to_csv().encode("utf-8")

    st.download_button(
        "⬇️ Download Content CSV",
        csv_content,
        file_name=f"content_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    st.dataframe(df_content_t, use_container_width=True)
else:
    st.info("No content selected.")

# # =========================================================
# # METADATA TABLE
# # =========================================================
# st.markdown("---")
# st.header("🧾 Metadata Overview")

# metadata_rows = []

# for json_file in selected_jsons:
#     try:
#         data = json.load(open(os.path.join(HTML_DIR, json_file), "r", encoding="utf-8"))
#         metadata_rows.append(extract_metadata_row(json_file, data))
#     except Exception as e:
#         st.error(f"Metadata error for {json_file}: {e}")

# if metadata_rows:
#     df_meta = pd.DataFrame(metadata_rows)

#     preferred_order = [
#         "json_file", "timestamp", "opportunity_id",
#         "title", "site_name", "og_url",
#         "description",
#         "num_links", "num_images",
#         "num_structured_blocks", "num_headings", "num_paragraphs",
#         "text_length", "generator"
#     ]

#     df_meta = df_meta[[c for c in preferred_order if c in df_meta.columns]]

#     csv_meta = df_meta.to_csv(index=False).encode("utf-8")

#     st.download_button(
#         "⬇️ Download Metadata CSV",
#         csv_meta,
#         file_name=f"metadata_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
#         mime="text/csv"
#     )

#     st.dataframe(df_meta, use_container_width=True)
# else:
#     st.info("No metadata available.")


# import streamlit as st
# import os
# import json
# import pandas as pd
# from datetime import datetime

# # =========================================================
# # CONFIG
# # =========================================================
# HTML_DIR = "scraped_html"

# st.set_page_config(
#     page_title="Multi-JSON Content Matrix",
#     layout="wide"
# )

# st.title("🧩 Multi-JSON Content Selector → Wide Table")

# # =========================================================
# # HELPERS
# # =========================================================
# def extract_metadata(filename):
#     """
#     Expected filename format:
#     2025-12-14T06-17-23_Requests_unknown.json
#     """
#     ts = None
#     opp = None

#     try:
#         base = os.path.splitext(filename)[0]
#         ts_part, opp_part = base.split("_", 1)
#         ts = ts_part.replace("-", ":", 2)
#         opp = opp_part
#     except:
#         pass

#     return ts, opp


# # =========================================================
# # LOAD JSON FILES
# # =========================================================
# if not os.path.exists(HTML_DIR):
#     st.error(f"Directory not found: {HTML_DIR}")
#     st.stop()

# json_files = sorted([
#     f for f in os.listdir(HTML_DIR)
#     if f.endswith(".json")
# ])

# if not json_files:
#     st.info("No JSON files found.")
#     st.stop()

# selected_jsons = st.multiselect(
#     "📂 Select JSON files",
#     json_files
# )

# if not selected_jsons:
#     st.stop()

# # =========================================================
# # MAIN PROCESSING
# # =========================================================
# final_rows = []

# for json_file in selected_jsons:

#     st.markdown("---")
#     st.subheader(f"📄 {json_file}")

#     path = os.path.join(HTML_DIR, json_file)

#     try:
#         data = json.load(open(path, "r", encoding="utf-8"))
#     except Exception as e:
#         st.error(f"Failed to load JSON: {e}")
#         continue

#     # -----------------------------------------------------
#     # EXTRACT CONTENT BLOCKS
#     # -----------------------------------------------------
#     blocks = []

#     if isinstance(data, dict):
#         if "structured_content" in data and isinstance(data["structured_content"], list):
#             for b in data["structured_content"]:
#                 txt = b.get("content")
#                 if txt and txt.strip():
#                     blocks.append(txt.strip())
#         elif "all_text" in data and data["all_text"].strip():
#             blocks.append(data["all_text"].strip())

#     if not blocks:
#         st.warning("No content blocks found.")
#         continue

#     N = len(blocks)

#     ts, opp_id = extract_metadata(json_file)

#     # -----------------------------------------------------
#     # SESSION STATE INIT
#     # -----------------------------------------------------
#     state_key = f"checks_{json_file}"

#     if state_key not in st.session_state:
#         st.session_state[state_key] = {i: True for i in range(N)}

#     checks = st.session_state[state_key]

#     # -----------------------------------------------------
#     # ACTION BUTTONS
#     # -----------------------------------------------------
#     c1, c2, c3 = st.columns(3)

#     if c1.button("✅ Select All", key=f"all_{json_file}"):
#         st.session_state[state_key] = {i: True for i in range(N)}

#     if c2.button("❌ Unselect All", key=f"none_{json_file}"):
#         st.session_state[state_key] = {i: False for i in range(N)}

#     if c3.button("🔁 Invert", key=f"invert_{json_file}"):
#         st.session_state[state_key] = {
#             i: not checks[i] for i in range(N)
#         }

#     checks = st.session_state[state_key]

#     # -----------------------------------------------------
#     # CHECKBOXES
#     # -----------------------------------------------------
#     for i, text in enumerate(blocks):
#         preview = text[:150].replace("\n", " ")
#         if len(text) > 150:
#             preview += "..."

#         st.checkbox(
#             f"[{i+1}] {preview}",
#             key=f"{state_key}_{i}",
#             value=checks[i],
#             on_change=lambda idx=i: st.session_state[state_key].update(
#                 {idx: st.session_state[f"{state_key}_{idx}"]}
#             )
#         )

#     # -----------------------------------------------------
#     # BUILD ROW
#     # -----------------------------------------------------
#     row = {
#         "json_file": json_file,
#         "opportunity_id": opp_id,
#         "timestamp": ts
#     }

#     col_idx = 1
#     for i in range(N):
#         if checks[i]:
#             row[f"content_{col_idx}"] = blocks[i]
#             col_idx += 1

#     final_rows.append(row)

# # =========================================================
# # BUILD FINAL TABLE
# # =========================================================
# st.markdown("---")
# st.subheader("📊 Final Combined Table (Transposed)")

# if not final_rows:
#     st.warning("No content selected.")
#     st.stop()

# df = pd.DataFrame(final_rows)

# meta_cols = [c for c in ["json_file", "opportunity_id", "timestamp"] if c in df.columns]
# content_cols = sorted([c for c in df.columns if c.startswith("content_")])

# df = df[meta_cols + content_cols]
# df_transposed = df.set_index("json_file").T

# # =========================================================
# # CSV DOWNLOAD (ABOVE TABLE)
# # =========================================================
# csv = df_transposed.to_csv().encode("utf-8")

# st.download_button(
#     "⬇️ Download CSV",
#     csv,
#     file_name=f"content_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
#     mime="text/csv"
# )

# st.dataframe(df_transposed, use_container_width=True)


# import streamlit as st
# import os
# import json
# import re
# import pandas as pd
# from datetime import datetime

# # =========================================================
# # CONFIG
# # =========================================================
# HTML_DIR = "scraped_html"
# SCRAPE_LOG_FILE = "scrape_log.json"

# st.set_page_config(page_title="Multi JSON Dataset Builder", layout="wide")
# st.title("📊 Dataset Builder — Multi JSON Selector")

# # =========================================================
# # LOAD JSON FILES (ONLY PARSED ONES)
# # =========================================================
# all_files = os.listdir(HTML_DIR)

# json_files = sorted([
#     f for f in all_files
#     if f.endswith(".json") and "parse_html_to_json" in f
# ])

# if not json_files:
#     st.info("No parsed JSON files found in scraped_html/")
#     st.stop()

# # =========================================================
# # TOP OUTPUT PLACEHOLDERS (CSV FIRST)
# # =========================================================
# st.markdown("### 📤 Combined Dataset Output")

# placeholder_table = st.empty()
# placeholder_dl1 = st.empty()
# placeholder_dl2 = st.empty()

# final_rows = []

# # =========================================================
# # LOAD SCRAPE LOG → MAP JSON → URL
# # =========================================================
# scrape_url_map = {}

# if os.path.exists(SCRAPE_LOG_FILE):
#     logs = json.load(open(SCRAPE_LOG_FILE, "r"))
#     logs_df = pd.DataFrame(logs)

#     for jf in json_files:
#         m = re.search(r"_(\d+)", jf)
#         opp_id = m.group(1) if m else None

#         if opp_id and not logs_df.empty:
#             match = logs_df[logs_df["url"].str.contains(opp_id, na=False)]
#             scrape_url_map[jf] = match.iloc[0]["url"] if len(match) else None
#         else:
#             scrape_url_map[jf] = None

# # =========================================================
# # HELPERS
# # =========================================================
# def extract_metadata(filename):
#     try:
#         ts = filename.split("_")[0]
#         ts = datetime.strptime(ts, "%Y-%m-%dT%H-%M-%S")
#     except:
#         ts = None

#     m = re.search(r"_(\d+)", filename)
#     opp_id = m.group(1) if m else None

#     return ts, opp_id

# # =========================================================
# # JSON MULTI-SELECTION DROPDOWN
# # =========================================================
# selected_jsons = st.multiselect(
#     "📂 Select parsed JSON files:",
#     json_files,
#     key="multi_json_selector"
# )

# if not selected_jsons:
#     st.stop()

# # =========================================================
# # PROCESS EACH JSON FILE
# # =========================================================
# for json_file in selected_jsons:

#     st.markdown("---")
#     st.subheader(f"📄 {json_file}")

#     json_path = os.path.join(HTML_DIR, json_file)

#     try:
#         data = json.load(open(json_path, "r", encoding="utf-8"))
#     except Exception as e:
#         st.error(f"Failed to load {json_file}: {e}")
#         continue

#     if not isinstance(data, list):
#         st.warning("JSON is not a list — skipping")
#         continue

#     N = len(data)

#     ts, opp_id = extract_metadata(json_file)
#     scrape_url = scrape_url_map.get(json_file)

#     state_key = f"checks_{json_file}"

#     if state_key not in st.session_state:
#         st.session_state[state_key] = {i: True for i in range(1, N + 1)}

#     checks = st.session_state[state_key]

#     # -------------------------------
#     # QUICK ACTIONS
#     # -------------------------------
#     col1, col2, col3 = st.columns(3)

#     if col1.button("Select All", key=f"all_{json_file}"):
#         st.session_state[state_key] = {i: True for i in range(1, N + 1)}

#     if col2.button("Unselect All", key=f"none_{json_file}"):
#         st.session_state[state_key] = {i: False for i in range(1, N + 1)}

#     if col3.button("Invert", key=f"invert_{json_file}"):
#         st.session_state[state_key] = {
#             i: not checks[i] for i in range(1, N + 1)
#         }

#     checks = st.session_state[state_key]

#     # -------------------------------
#     # CONTENT CHECKBOX MATRIX
#     # -------------------------------
#     for idx in range(1, N + 1):
#         item = data[idx - 1]
#         text = item.get("content") or "(empty)"

#         st.checkbox(
#             f"[{idx}] {text}",
#             key=f"{state_key}_{idx}",
#             value=checks[idx],
#             on_change=lambda x=idx: st.session_state[state_key].update(
#                 {x: st.session_state[f"{state_key}_{x}"]}
#             )
#         )

#     # -------------------------------
#     # BUILD ROW
#     # -------------------------------
#     selected_idx = [i for i in range(1, N + 1) if checks[i]]

#     row = {
#         "json_file": json_file,
#         "opportunity_id": opp_id,
#         "scrape_url": scrape_url,
#         "timestamp": ts
#     }

#     col_n = 1
#     for i in selected_idx:
#         row[f"content_{col_n}"] = data[i - 1].get("content")
#         col_n += 1

#     final_rows.append(row)

# # =========================================================
# # BUILD FINAL DATAFRAMES
# # =========================================================
# df_wide = pd.DataFrame(final_rows)

# meta_cols = ["json_file", "opportunity_id", "scrape_url", "timestamp"]
# content_cols = sorted([c for c in df_wide.columns if c.startswith("content_")])
# df_wide = df_wide[meta_cols + content_cols]

# df_transposed = df_wide.set_index("json_file").T

# # =========================================================
# # DISPLAY + DOWNLOAD (TOP AREA)
# # =========================================================
# placeholder_table.dataframe(df_transposed, use_container_width=True)

# placeholder_dl1.download_button(
#     "⬇ Download Transposed CSV",
#     df_transposed.to_csv(),
#     file_name="dataset_transposed.csv",
#     mime="text/csv"
# )

# placeholder_dl2.download_button(
#     "⬇ Download Wide CSV",
#     df_wide.to_csv(index=False),
#     file_name="dataset_wide.csv",
#     mime="text/csv"
# )


# import streamlit as st
# import pandas as pd

# # Load JSON
# data = your_json_object

# st.title("📄 Scraped Page Inspector")

# # -------------------------
# # 1. Overview
# # -------------------------
# st.header("Page Overview")

# overview = {
#     "title": data.get("title", "").strip(),
#     "url": data["metadata"].get("og:url"),
#     "source": data["metadata"].get("twitter:site"),
# }

# st.table(pd.DataFrame(overview.items(), columns=["Field", "Value"]))

# # -------------------------
# # 2. Metadata
# # -------------------------
# st.header("Metadata")
# meta_df = pd.DataFrame(
#     data["metadata"].items(),
#     columns=["Key", "Value"]
# )
# st.dataframe(meta_df, use_container_width=True)

# # -------------------------
# # 3. Structured Content
# # -------------------------
# st.header("Structured Content")

# sc_rows = []
# for i, block in enumerate(data.get("structured_content", []), start=1):
#     sc_rows.append({
#         "order": i,
#         "type": block.get("type"),
#         "level": block.get("level"),
#         "content": block.get("content")
#     })

# st.dataframe(pd.DataFrame(sc_rows), use_container_width=True)

# # -------------------------
# # 4. Links
# # -------------------------
# st.header("Links")
# links_df = pd.DataFrame({
#     "index": range(1, len(data["links"]) + 1),
#     "link": data["links"]
# })
# st.dataframe(links_df, use_container_width=True)

# # -------------------------
# # 5. Images
# # -------------------------
# st.header("Images")
# img_df = pd.DataFrame({
#     "index": range(1, len(data["images"]) + 1),
#     "image": data["images"]
# })
# st.dataframe(img_df)
