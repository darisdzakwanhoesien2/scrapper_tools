# import streamlit as st
# import importlib.util
# import os
# import json
# from pathlib import Path

# SCRAPED_HTML_DIR = Path("scraped_html")
# OUTPUT_DIR = Path("scraped_html")
# PARSERS_DIR = Path("parsers")

# st.title("🧩 HTML → JSON Parser Runner")


# # ---------------------------------------------------------
# # Helper: Load parser dynamically
# # ---------------------------------------------------------
# def load_parser_module(parser_filename):
#     parser_path = PARSERS_DIR / parser_filename

#     if not parser_path.exists():
#         st.error(f"Parser script not found: {parser_path}")
#         return None

#     spec = importlib.util.spec_from_file_location("parser_module", parser_path)
#     module = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(module)

#     # Validate required function
#     if not hasattr(module, "run_parser"):
#         st.error("❌ Parser script must contain a function named run_parser(html_file_path, output_json_path)")
#         return None

#     return module


# # ---------------------------------------------------------
# # UI
# # ---------------------------------------------------------
# parser_files = [f for f in os.listdir(PARSERS_DIR) if f.endswith(".py")]

# parser_choice = st.selectbox("Choose Parser Script", parser_files)

# html_files = [f for f in os.listdir(SCRAPED_HTML_DIR) if f.endswith(".html")]
# html_choice = st.selectbox("Choose HTML File to Parse", html_files)


# if st.button("Run Parser"):
#     module = load_parser_module(parser_choice)

#     if module:
#         html_path = SCRAPED_HTML_DIR / html_choice
#         output_path = OUTPUT_DIR / f"{html_choice}_parsed.json"

#         st.info(f"Running parser on {html_choice}...")

#         try:
#             success, result = module.run_parser(str(html_path), str(output_path))

#             if success:
#                 st.success("Parsing completed successfully!")
#                 st.json(result)

#                 # Load JSON preview
#                 if output_path.exists():
#                     with open(output_path, "r", encoding="utf-8") as f:
#                         data = json.load(f)
#                     st.subheader("Parsed JSON Preview")
#                     st.json(data)

#             else:
#                 st.error("❌ Parsing failed")
#                 st.json(result)

#         except Exception as e:
#             st.error(f"Unexpected error: {e}")


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
# Streamlit UI
# ===========================================
st.set_page_config(page_title="HTML → JSON Parser Suite", layout="wide")
st.title("🔄 HTML → JSON Parser | Multi-Type Parser Runner")


tab_run, tab_logs = st.tabs(["▶ Run Parser", "📊 Visualize Logs"])


# ==========================================================
# TAB 1: RUN PARSER
# ==========================================================
with tab_run:

    st.header("▶ Run a Parser")

    # ------------------ Load parser scripts ------------------
    parser_files = [f for f in os.listdir(PARSER_DIR) if f.endswith(".py")]

    if not parser_files:
        st.warning("⚠ No parser scripts found in /parsers/")
        st.stop()

    parser_choice = st.selectbox("Choose parser script:", parser_files)

    # ------------------ Load HTML files ----------------------
    html_files = [f for f in os.listdir(HTML_DIR) if f.endswith(".html")]

    if not html_files:
        st.warning("⚠ No HTML files found in /scraped_html/")
        st.stop()

    html_choice = st.selectbox("Choose HTML file:", html_files)

    # ------------------ Run parser button -------------------
    if st.button("Run Parser Now"):

        html_path = os.path.join(HTML_DIR, html_choice)
        output_json_path = html_path.replace(".html", f"_{parser_choice.replace('.py','')}.json")

        # Import parser module dynamically
        module_name = parser_choice.replace(".py", "")
        module = importlib.import_module(f"{PARSER_DIR}.{module_name}")

        # Validate run_parser function exists
        if not hasattr(module, "run_parser"):
            st.error("❌ The parser script must define a function: run_parser(html_file_path, output_json_path)")
            st.stop()

        success, result = module.run_parser(html_path, output_json_path)

        # Number of extracted items (if it's a list)
        items_extracted = len(result) if success and isinstance(result, list) else None

        # Build log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "parser_name": module_name,
            "status": "success" if success else "failed",
            "html_file_path": html_path,
            "output_json_path": output_json_path,
            "items_extracted": items_extracted
        }

        save_parser_run_log(log_entry)

        # Show results
        if success:
            st.success(f"Parser succeeded! JSON saved to: {output_json_path}")
            st.subheader("Preview of Parsed Content")
            st.json(result[:50] if isinstance(result, list) else result)
        else:
            st.error(f"Parser failed: {result}")

        st.subheader("Log Entry Saved:")
        st.json(log_entry)



# ==========================================================
# TAB 2: LOG VISUALIZATION
# ==========================================================
with tab_logs:

    st.header("📊 Parser Run Logs & Analytics")

    if not os.path.exists(PARSER_LOG_FILE):
        st.info("No logs yet. Run a parser first.")
        st.stop()

    logs = json.load(open(PARSER_LOG_FILE, "r"))

    if len(logs) == 0:
        st.info("Log file is empty.")
        st.stop()

    df = pd.DataFrame(logs)

    # Display table
    st.subheader("📄 Raw Log Table")
    st.dataframe(df)

    # =============================
    # Visualization 1: Items Extracted
    # =============================
    if "items_extracted" in df.columns:
        st.subheader("📈 Items Extracted per Run")
        st.bar_chart(df["items_extracted"].fillna(0))

    # =============================
    # Visualization 2: Parser Usage Count
    # =============================
    if "parser_name" in df.columns:
        st.subheader("🔧 Parser Usage Count")
        usage = df["parser_name"].value_counts()
        st.bar_chart(usage)

    # =============================
    # Visualization 3: Timeline Plot
    # =============================
    if "timestamp" in df.columns and "items_extracted" in df.columns:
        st.subheader("📅 Timeline of Items Extracted")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df_sorted = df.sort_values("timestamp")
        st.line_chart(df_sorted.set_index("timestamp")["items_extracted"].fillna(0))

    # Download logs
    st.subheader("⬇ Download Logs")
    st.download_button(
        label="Download parser_run_log.json",
        data=json.dumps(logs, indent=4),
        file_name="parser_run_log.json",
        mime="application/json"
    )


# import streamlit as st
# import os
# import importlib
# import json

# HTML_DIR = "scraped_html"
# PARSER_DIR = "parsers"

# st.set_page_config(page_title="HTML → JSON Parser Runner", layout="centered")
# st.title("🔄 Run HTML Parser Scripts")


# # ------------------------------------------------------------
# # LOAD AVAILABLE PARSERS (detects python files automatically)
# # ------------------------------------------------------------
# parser_files = [f for f in os.listdir(PARSER_DIR) if f.endswith(".py")]

# if not parser_files:
#     st.error("⚠ No parser scripts found in /parsers")
#     st.stop()

# parser_choice = st.selectbox("Choose parser script:", parser_files)


# # ------------------------------------------------------------
# # LOAD HTML FILES TO PARSE
# # ------------------------------------------------------------
# html_files = [f for f in os.listdir(HTML_DIR) if f.endswith(".html")]

# if not html_files:
#     st.error("⚠ No HTML files found in /scraped_html")
#     st.stop()

# html_choice = st.selectbox("Choose HTML file:", html_files)


# # ------------------------------------------------------------
# # RUN BUTTON
# # ------------------------------------------------------------
# if st.button("Run Parser"):

#     html_path = os.path.join(HTML_DIR, html_choice)
#     output_path = html_path.replace(".html", f"_{parser_choice.replace('.py','')}.json")

#     # Dynamically import parser module
#     module_name = parser_choice.replace(".py", "")
#     module = importlib.import_module(f"{PARSER_DIR}.{module_name}")

#     # Run the parser
#     if not hasattr(module, "run_parser"):
#         st.error("❌ Parser script must contain a function named run_parser(html_file_path, output_json_path)")
#         st.stop()

#     success, result = module.run_parser(html_path, output_path)

#     if success:
#         st.success(f"JSON saved to: {output_path}")
#         st.subheader("Preview:")
#         st.json(result if isinstance(result, list) else result)
#     else:
#         st.error(f"Parser failed: {result}")
