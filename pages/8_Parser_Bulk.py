import streamlit as st
import os
import importlib
import json
import pandas as pd
from datetime import datetime


# ===========================================
# Paths
# ===========================================
HTML_DIR = "scraped_html"
PARSER_DIR = "parsers"
PARSER_LOG_FILE = "parser_run_log.json"


# ===========================================
# Ensure directories exist
# ===========================================
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(PARSER_DIR, exist_ok=True)


# ===========================================
# Save parser logs
# ===========================================
def save_parser_run_log(entry):
    if os.path.exists(PARSER_LOG_FILE):
        try:
            logs = json.load(open(PARSER_LOG_FILE, "r"))
        except:
            logs = []
    else:
        logs = []

    logs.append(entry)

    with open(PARSER_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

    return True


# ===========================================
# STREAMLIT UI
# ===========================================
st.set_page_config(page_title="HTML → JSON Parser Suite", layout="wide")
st.title("🔄 HTML → JSON Parser | Single & Bulk Processing")

tab_run, tab_bulk, tab_logs, tab_manage, tab_unparsed = st.tabs([
    "▶ Run Single Parser",
    "📦 Bulk Parse Multiple HTML Files",
    "📊 Visualize Logs",
    "Manage Duplication",
    "Unparsed"
])



# ==========================================================
# TAB 1: RUN SINGLE FILE
# ==========================================================
with tab_run:

    st.header("▶ Run a Parser on One HTML File")

    # Load parser scripts
    parser_files = [f for f in os.listdir(PARSER_DIR) if f.endswith(".py")]

    if not parser_files:
        st.warning("⚠ No parser scripts found in /parsers/")
        st.stop()

    parser_choice = st.selectbox(
        "Choose parser script:",
        parser_files,
        key="single_parser_choice"
    )

    # Load HTML files
    html_files = [f for f in os.listdir(HTML_DIR) if f.endswith(".html")]

    if not html_files:
        st.warning("⚠ No HTML files found in /scraped_html/")
        st.stop()

    html_choice = st.selectbox(
        "Choose HTML file to parse:",
        html_files,
        key="single_html_choice"
    )

    if st.button("Run Parser Now", key="run_single_parser"):

        html_path = os.path.join(HTML_DIR, html_choice)
        output_json_path = html_path.replace(
            ".html", f"_{parser_choice.replace('.py','')}.json"
        )

        # Import parser dynamically
        module_name = parser_choice.replace(".py", "")
        module = importlib.import_module(f"{PARSER_DIR}.{module_name}")

        if not hasattr(module, "run_parser"):
            st.error("❌ Parser must define: run_parser(html_file_path, output_json_path)")
            st.stop()

        success, result = module.run_parser(html_path, output_json_path)
        items_extracted = len(result) if success and isinstance(result, list) else None

        # Log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "parser_name": module_name,
            "status": "success" if success else "failed",
            "html_file_path": html_path,
            "output_json_path": output_json_path,
            "items_extracted": items_extracted
        }
        save_parser_run_log(log_entry)

        if success:
            st.success(f"✔ Parser succeeded! JSON saved to:\n {output_json_path}")
            st.subheader("Preview of Parsed Content")
            st.json(result[:50] if isinstance(result, list) else result)
        else:
            st.error(f"Parser failed: {result}")

        st.subheader("Log Entry Saved")
        st.json(log_entry)



# ==========================================================
# TAB 2: BULK PARSER
# ==========================================================
with tab_bulk:

    st.header("📦 Bulk Parse HTML Files Using One Parser")

    # Parser selection
    parser_choice_bulk = st.selectbox(
        "Choose parser script:",
        parser_files,
        key="bulk_parser_choice"
    )

    # HTML MULTI-SELECTION
    html_choices = st.multiselect(
        "Select HTML files to parse:",
        html_files,
        key="bulk_html_choices"
    )

    if st.button("Run Bulk Parser", key="run_bulk_parser"):

        if len(html_choices) == 0:
            st.error("Please select at least one HTML file.")
            st.stop()

        st.info(f"Running parser on {len(html_choices)} files...")

        module_name = parser_choice_bulk.replace(".py", "")
        module = importlib.import_module(f"{PARSER_DIR}.{module_name}")

        if not hasattr(module, "run_parser"):
            st.error("❌ Parser missing: run_parser()")
            st.stop()

        progress = st.progress(0)
        results = []

        for i, html_file in enumerate(html_choices):

            html_path = os.path.join(HTML_DIR, html_file)
            output_json_path = html_path.replace(".html", f"_{module_name}.json")

            success, result = module.run_parser(html_path, output_json_path)
            items_extracted = len(result) if success and isinstance(result, list) else None

            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "parser_name": module_name,
                "status": "success" if success else "failed",
                "html_file_path": html_path,
                "output_json_path": output_json_path,
                "items_extracted": items_extracted
            }
            save_parser_run_log(log_entry)

            results.append(log_entry)
            progress.progress((i + 1) / len(html_choices))

        st.success("🎉 Bulk parsing complete!")

        df_summary = pd.DataFrame(results)
        st.dataframe(df_summary)

        st.download_button(
            "⬇ Download Summary CSV",
            df_summary.to_csv(index=False),
            file_name="bulk_parser_summary.csv"
        )



# ==========================================================
# TAB 3: VISUALIZATION
# ==========================================================
with tab_logs:

    st.header("📊 Parser Run Logs & Analytics")

    if not os.path.exists(PARSER_LOG_FILE):
        st.info("No logs yet.")
        st.stop()

    logs = json.load(open(PARSER_LOG_FILE, "r"))

    if len(logs) == 0:
        st.info("Log file is empty.")
        st.stop()

    df = pd.DataFrame(logs)

    st.subheader("📄 Log Table")
    st.dataframe(df)

    if "items_extracted" in df.columns:
        st.subheader("📈 Items Extracted")
        st.bar_chart(df["items_extracted"].fillna(0))

    if "parser_name" in df.columns:
        st.subheader("🔧 Parser Usage")
        st.bar_chart(df["parser_name"].value_counts())

    if "timestamp" in df.columns:
        st.subheader("📅 Timeline")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df_sorted = df.sort_values("timestamp")
        st.line_chart(
            df_sorted.set_index("timestamp")["items_extracted"].fillna(0)
        )

    st.download_button(
        "⬇ Download parser_run_log.json",
        json.dumps(logs, indent=4),
        file_name="parser_run_log.json",
        mime="application/json"
    )

# ==========================================================
# TAB 4: PARSED VS UNPARSED HTML MANAGEMENT
# ==========================================================
with tab_manage:

    st.header("📂 Manage Parsed & Unparsed HTML Files")

    all_files = os.listdir(HTML_DIR)
    html_files = [f for f in all_files if f.endswith(".html")]
    json_files = [f for f in all_files if f.endswith(".json")]

    # Extract which html files have matching json
    parsed_html = []
    unparsed_html = []

    for html in html_files:
        base = html.replace(".html", "")
        matched = [j for j in json_files if j.startswith(base)]
        if matched:
            parsed_html.append(html)
        else:
            unparsed_html.append(html)

    # Date filter UI
    st.subheader("📅 Filter by Date")
    selected_date = st.date_input("Select date", None)

    def extract_datetime(fname):
        try:
            # Format example: 2025-12-11T07-59-16_Requests_1322886.html
            timestamp = fname.split("_")[0]
            return datetime.strptime(timestamp, "%Y-%m-%dT%H-%M-%S")
        except Exception:
            return None

    # Apply date filter (optional)
    if selected_date:
        parsed_html = [
            f for f in parsed_html
            if extract_datetime(f) and extract_datetime(f).date() == selected_date
        ]
        unparsed_html = [
            f for f in unparsed_html
            if extract_datetime(f) and extract_datetime(f).date() == selected_date
        ]

    # PARSED FILES
    st.subheader("✅ Parsed HTML Files (have JSON)")
    if len(parsed_html) == 0:
        st.info("No parsed HTML files found based on filter.")
    else:
        df_parsed = pd.DataFrame({"parsed_html": parsed_html})
        st.dataframe(df_parsed)

    # UNPARSED FILES
    st.subheader("❌ Unparsed HTML Files (no JSON yet)")
    if len(unparsed_html) == 0:
        st.info("No unparsed HTML files found based on filter.")
    else:
        df_unparsed = pd.DataFrame({"unparsed_html": unparsed_html})
        st.dataframe(df_unparsed)

    # Optional preview
    st.subheader("🔍 Preview a File")

    preview_target = st.selectbox(
        "Choose a file to preview content:",
        parsed_html + unparsed_html,
        key="preview_html_list"
    )

    if preview_target:
        with open(os.path.join(HTML_DIR, preview_target), "r", encoding="utf-8") as f:
            st.code(f.read()[:5000], language="html")


# ==========================================================
# TAB 4: PARSED VS UNPARSED HTML MANAGEMENT
# ==========================================================
with tab_unparsed:

    st.header("📂 Manage Parsed & Unparsed HTML Files")

    # Load parser scripts (needed for bulk parsing)
    parser_files = [f for f in os.listdir(PARSER_DIR) if f.endswith(".py")]

    # Load files
    all_files = os.listdir(HTML_DIR)
    html_files = [f for f in all_files if f.endswith(".html")]
    json_files = [f for f in all_files if f.endswith(".json")]

    # Determine which HTML files have a JSON match
    parsed_html = []
    unparsed_html = []

    for html in html_files:
        base = html.replace(".html", "")
        matched_jsons = [j for j in json_files if j.startswith(base)]
        if matched_jsons:
            parsed_html.append(html)
        else:
            unparsed_html.append(html)

    # Helper: Extract datetime from filename
    def extract_datetime(fname):
        try:
            timestamp = fname.split("_")[0]  # Example: 2025-12-11T07-59-16
            return datetime.strptime(timestamp, "%Y-%m-%dT%H-%M-%S")
        except:
            return None

    # ==========================
    # DATE FILTER
    # ==========================
    st.subheader("📅 Filter by Date")
    selected_date = st.date_input("Select date (optional)", None)

    if selected_date:
        parsed_html = [
            f for f in parsed_html
            if extract_datetime(f) and extract_datetime(f).date() == selected_date
        ]
        unparsed_html = [
            f for f in unparsed_html
            if extract_datetime(f) and extract_datetime(f).date() == selected_date
        ]

    # ==========================
    # DISPLAY PARSED FILES
    # ==========================
    st.subheader("✅ Parsed HTML Files (have JSON)")
    if len(parsed_html) == 0:
        st.info("No parsed HTML files found for this filter.")
    else:
        df_parsed = pd.DataFrame({"parsed_html": parsed_html})
        st.dataframe(df_parsed, use_container_width=True)

    # ==========================
    # DISPLAY UNPARSED FILES
    # ==========================
    st.subheader("❌ Unparsed HTML Files (no JSON yet)")
    if len(unparsed_html) == 0:
        st.success("🎉 All HTML files have already been parsed!")
    else:
        df_unparsed = pd.DataFrame({"unparsed_html": unparsed_html})
        st.dataframe(df_unparsed, use_container_width=True)

    # ==========================
    # PREVIEW FILE CONTENT
    # ==========================
    st.subheader("🔍 Preview a File")

    preview_target = st.selectbox(
        "Choose a file to preview content:",
        parsed_html + unparsed_html,
        key="preview_html_list"
    )

    if preview_target:
        with open(os.path.join(HTML_DIR, preview_target), "r", encoding="utf-8") as f:
            st.code(f.read()[:5000], language="html")

    # ==========================
    # BULK PARSE UNPARSED FILES
    # ==========================
    st.subheader("⚙ Bulk Parse All Unparsed HTML Files")

    parser_choice_bulk_unparsed = st.selectbox(
        "Choose parser to apply to ALL unparsed HTML files:",
        parser_files,
        key="bulk_parser_for_unparsed"
    )

    if st.button("▶ Run Bulk Parser for Unparsed HTML", key="run_bulk_parser_unparsed"):

        if len(unparsed_html) == 0:
            st.info("There are no unparsed HTML files to process.")
            st.stop()

        st.warning(f"Running parser on {len(unparsed_html)} unparsed HTML files...")

        # Load parser module dynamically
        module_name = parser_choice_bulk_unparsed.replace(".py", "")
        module = importlib.import_module(f"{PARSER_DIR}.{module_name}")

        if not hasattr(module, "run_parser"):
            st.error("❌ Parser missing required function: run_parser()")
            st.stop()

        progress = st.progress(0)
        bulk_results = []

        for i, html_file in enumerate(unparsed_html):

            html_path = os.path.join(HTML_DIR, html_file)
            output_json_path = html_path.replace(".html", f"_{module_name}.json")

            # Execute parser
            success, result = module.run_parser(html_path, output_json_path)
            items_extracted = len(result) if success and isinstance(result, list) else None

            # Log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "parser_name": module_name,
                "status": "success" if success else "failed",
                "html_file_path": html_path,
                "output_json_path": output_json_path,
                "items_extracted": items_extracted
            }

            save_parser_run_log(log_entry)
            bulk_results.append(log_entry)

            progress.progress((i + 1) / len(unparsed_html))

        st.success("🎉 Finished bulk parsing all unparsed HTML files!")

        # Display summary
        df_summary = pd.DataFrame(bulk_results)
        st.subheader("📄 Bulk Parsing Summary")
        st.dataframe(df_summary, use_container_width=True)

        st.download_button(
            "⬇ Download Summary CSV",
            df_summary.to_csv(index=False),
            file_name="bulk_unparsed_summary.csv"
        )
