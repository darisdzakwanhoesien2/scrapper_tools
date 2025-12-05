# import streamlit as st
# import json
# from pathlib import Path
# import streamlit.components.v1 as components

# st.title("📂 JSON Data Viewer")

# raw_dir = Path("data/raw")
# files = sorted(raw_dir.glob("*.json"))

# if not files:
#     st.info("No JSON files yet.")
# else:
#     filenames = [f.name for f in files]
#     selected = st.selectbox("Select a file", filenames)

#     path = raw_dir / selected
#     content = json.loads(path.read_text())

#     source_url = content.get("_source_url", None)

#     # -------------------------------
#     # TWO-COLUMN LAYOUT
#     # -------------------------------
#     col1, col2 = st.columns([1, 1])

#     # LEFT → Website Preview
#     with col1:
#         st.subheader("🌍 Original Website")
#         if source_url:
#             components.iframe(source_url, height=800)
#         else:
#             st.warning("No source URL stored in JSON")

#     # RIGHT → JSON Viewer
#     with col2:
#         st.subheader("📄 Extracted JSON Data")
#         st.json(content)

import streamlit as st
import json
from pathlib import Path
import streamlit.components.v1 as components

st.title("📂 JSON Data Viewer")

raw_dir = Path("data/raw")
files = sorted(raw_dir.glob("*.json"))

if not files:
    st.info("No JSON files yet.")
else:
    # Load all JSON metadata first
    file_map = {}  # filename → (_source_url, content)

    for f in files:
        try:
            obj = json.loads(f.read_text())
            url = obj.get("_source_url", "Unknown URL")
            file_map[f.name] = (url, obj)
        except:
            file_map[f.name] = ("Corrupted JSON", {})

    # ------------------------------------------------
    # Build URL dropdown
    # ------------------------------------------------
    unique_urls = sorted({file_map[f][0] for f in file_map})
    selected_url = st.selectbox("Filter by URL", unique_urls)

    # Filter filenames associated with this URL
    matching_files = [fname for fname, (url, _) in file_map.items() if url == selected_url]

    selected_file = st.selectbox("Select JSON file", matching_files)

    # Load content
    source_url, content = file_map[selected_file]

    # ------------------------------------------------
    # Display URL clearly at top
    # ------------------------------------------------
    st.markdown(f"### 🔗 Original URL")
    st.markdown(f"**[{source_url}]({source_url})**")

    st.markdown("---")

    # -------------------------------
    # TWO-COLUMN VIEW: website + JSON
    # -------------------------------
    col1, col2 = st.columns([1, 1])

    # LEFT → Website Preview
    with col1:
        st.subheader("🌍 Website Preview")
        if source_url and source_url.startswith("http"):
            try:
                components.iframe(source_url, height=800)
            except:
                st.error("Website cannot be previewed (blocked by X-Frame-Options).")
        else:
            st.warning("No valid source URL stored.")

    # RIGHT → JSON Viewer
    with col2:
        st.subheader("📄 Extracted JSON Data")
        st.json(content)


# import streamlit as st
# import json
# from pathlib import Path

# st.title("📂 JSON Data Viewer")

# raw_dir = Path("data/raw")

# files = sorted(raw_dir.glob("*.json"))

# if not files:
#     st.info("No JSON files yet.")
# else:
#     filenames = [f.name for f in files]
#     selected = st.selectbox("Select a file", filenames)

#     path = raw_dir / selected
#     content = json.loads(path.read_text())

#     # Show original URL (you added _source_url in dataset)
#     source_url = content.get("_source_url", "Unknown")

#     st.write(f"🔗 **Original URL:** {source_url}")
#     st.json(content)
