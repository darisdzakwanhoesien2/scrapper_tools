# import streamlit as st
# from core.scraper import scrape_url
# from services.dataset_service import DatasetService
# from ui.layout import sidebar_layout, main_layout

# st.set_page_config(page_title="Scraper App", layout="wide")

# dataset = DatasetService()

# sidebar_layout()

# st.title("🌐 URL Scraper Tool")

# with st.form("scrape_form"):
#     url = st.text_input("Enter URL to scrape")
#     paginate = st.checkbox("Enable pagination", True)
#     merge_data = st.checkbox("Merge into dataset", True)
#     submit = st.form_submit_button("Scrape")

# if submit:
#     with st.spinner("Scraping..."):
#         result = scrape_url(url, paginate=paginate)

#     if result.get("error"):
#         st.error(result["error"])
#     else:
#         st.success("Scraping successful")
#         st.json(result["data"])

#         if merge_data:
#             merge_info = dataset.merge(result["data"])
#             st.info(f"Added: {merge_info['added']} | Duplicates removed: {merge_info['deduped']}")

# main_layout(dataset)

import streamlit as st
from core.scraper import scrape_url
from services.dataset_service import DatasetService
from services.storage_service import StorageService
from utils.logger import logger
from ui.layout import sidebar_layout, main_layout

# ---------------------------------------------------------
# Streamlit Page Config
# ---------------------------------------------------------
st.set_page_config(page_title="Scraper App", layout="wide")

# Core services
dataset = DatasetService()
storage = StorageService()

# Sidebar UI
sidebar_layout()

# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------
st.title("🌐 URL Scraper Tool")

st.markdown("""
Enter one or multiple URLs to scrape.  
Use multiple lines for bulk scraping.
""")

# ---------------------------------------------------------
# Scrape Form
# ---------------------------------------------------------
with st.form("scrape_form"):
    urls_text = st.text_area(
        "Enter URL(s) to scrape, one per line:",
        placeholder="https://example.com/page1\nhttps://example.com/page2"
    )
    paginate = st.checkbox("Enable pagination", True)
    merge_data = st.checkbox("Merge into dataset", True)
    save_file = st.checkbox("Save result to JSON file", True)
    submit = st.form_submit_button("Scrape")

# Convert textarea to list of URLs
urls = [u.strip() for u in urls_text.split("\n") if u.strip()]

# ---------------------------------------------------------
# SCRAPING LOGIC
# ---------------------------------------------------------
if submit:
    if not urls:
        st.error("Please enter at least one URL.")
    else:
        st.info(f"Starting scraping for {len(urls)} URL(s)...")

        for url in urls:

            # ---------------------------------------------------------
            # Check if URL was already scraped
            # ---------------------------------------------------------
            if dataset.has_url(url):
                st.warning(f"⏭️ Skipped (already scraped): {url}")
                logger.info(f"SKIPPED | {url}")
                continue

            # ---------------------------------------------------------
            # Perform scraping
            # ---------------------------------------------------------
            with st.spinner(f"Scraping {url} ..."):
                result = scrape_url(url, paginate=paginate)

            # ---------------------------------------------------------
            # Error handling
            # ---------------------------------------------------------
            if result.get("error"):
                st.error(f"❌ Error scraping {url}: {result['error']}")
                logger.error(f"ERROR | {url} | {result['error']}")
                continue

            # ---------------------------------------------------------
            # Mark success
            # ---------------------------------------------------------
            st.success(f"✅ Scrape successful: {url}")

            # Attach source URL **before saving**
            result["data"]["_source_url"] = url

            # Show JSON preview
            st.json(result["data"])

            # ---------------------------------------------------------
            # Save to file
            # ---------------------------------------------------------
            if save_file:
                filepath = storage.save_json(url, result["data"])
                st.info(f"📁 Saved to: `{filepath}`")
                logger.info(f"SUCCESS | {url} → {filepath}")

            # ---------------------------------------------------------
            # Merge into dataset
            # ---------------------------------------------------------
            if merge_data:
                merge_info = dataset.merge(result["data"])
                st.info(
                    f"📊 Dataset updated for {url}: "
                    f"{merge_info['added']} added, "
                    f"{merge_info['deduped']} duplicates removed."
                )

# ---------------------------------------------------------
# Dataset Viewer (existing UI)
# ---------------------------------------------------------
st.markdown("---")
main_layout(dataset)


# import streamlit as st
# from core.scraper import scrape_url
# from services.dataset_service import DatasetService
# from services.storage_service import StorageService
# from utils.logger import logger
# from ui.layout import sidebar_layout, main_layout

# # ---------------------------------------------------------
# # Streamlit Page Config
# # ---------------------------------------------------------
# st.set_page_config(page_title="Scraper App", layout="wide")

# # Core services
# dataset = DatasetService()
# storage = StorageService()

# # Sidebar
# sidebar_layout()

# # ---------------------------------------------------------
# # UI Header
# # ---------------------------------------------------------
# st.title("🌐 URL Scraper Tool")

# # ---------------------------------------------------------
# # Scrape Form
# # ---------------------------------------------------------
# with st.form("scrape_form"):
#     urls_text = st.text_area(
#         "Enter URL(s) to scrape. One URL per line.",
#         placeholder="https://example.com/page1\nhttps://example.com/page2"
#     )
#     paginate = st.checkbox("Enable pagination", True)
#     merge_data = st.checkbox("Merge into dataset", True)
#     save_file = st.checkbox("Save result to JSON file", True)
#     submit = st.form_submit_button("Scrape")

# # Convert textarea into clean list of URLs
# urls = [u.strip() for u in urls_text.split("\n") if u.strip()]

# # ---------------------------------------------------------
# # SCRAPING LOGIC
# # ---------------------------------------------------------
# if submit:
#     if not urls:
#         st.error("Please enter at least one URL.")
#     else:
#         st.info(f"Scraping {len(urls)} URL(s)...")

#         for url in urls:

#             # --- Start scraping
#             with st.spinner(f"Scraping {url} ..."):
#                 result = scrape_url(url, paginate=paginate)

#             # --- Error Handling
#             if result.get("error"):
#                 st.error(f"❌ Error scraping {url}: {result['error']}")
#                 logger.error(f"ERROR {url} → {result['error']}")
#                 continue

#             # --- Success
#             st.success(f"✅ Scrape successful: {url}")
#             st.json(result["data"])

#             # ---------------------------------------------------------
#             # SAVE FILE IF ENABLED
#             # ---------------------------------------------------------
#             if save_file:
#                 filepath = storage.save_json(url, result["data"])
#                 st.info(f"📁 Saved to: `{filepath}`")
#                 logger.info(f"SUCCESS {url} → {filepath}")

#             # ---------------------------------------------------------
#             # MERGE INTO DATASET IF ENABLED
#             # ---------------------------------------------------------
#             if merge_data:
#                 merge_info = dataset.merge(result["data"])
#                 st.info(
#                     f"📊 Dataset updated for {url}: "
#                     f"{merge_info['added']} added, "
#                     f"{merge_info['deduped']} duplicates removed."
#                 )

# # ---------------------------------------------------------
# # SHOW DATASET VIEWER
# # ---------------------------------------------------------
# st.markdown("---")
# main_layout(dataset)



# # app.py
# import streamlit as st
# from ui.layout import sidebar_layout, main_layout
# from core.scraper import scrape_url
# from services.storage_service import StorageService
# from services.dataset_service import DatasetService
# from core.scheduler import Scheduler
# from config.settings import SETTINGS

# st.set_page_config(page_title="Streamlit Scraper", layout="wide")

# storage = StorageService()
# dataset_service = DatasetService(storage)

# sidebar_layout()

# st.title("🌐 Streamlit Scraper App")

# with st.form("scrape_form"):
#     url = st.text_input("Enter URL to scrape")
#     paginate = st.checkbox("Enable pagination handling", value=True)
#     save_to_dataset = st.checkbox("Save/merge into dataset", value=True)
#     submitted = st.form_submit_button("Scrape")

# if submitted:
#     with st.spinner("Scraping..."):
#         result = scrape_url(url, paginate=paginate)

#     if result.get("error"):
#         st.error(result["error"])
#     else:
#         st.success("Scrape successful")
#         st.json(result["data"])  # show raw response

#         if save_to_dataset:
#             merged = dataset_service.merge_new(result["data"], source=url)
#             st.info(f"Merged: {merged['added']} new items — {merged['deduped']} duplicates removed")

# # Controls + export
# st.markdown("---")
# main_layout(dataset_service)

# # Scheduler example (starts when user presses a button)
# if st.sidebar.button("Start scheduled scraping"):
#     cron = Scheduler(dataset_service)
#     cron.start()
#     st.sidebar.success("Scheduler started (in-process). Press stop to end.")

# if st.sidebar.button("Stop scheduled scraping"):
#     Scheduler.stop()
#     st.sidebar.warning("Scheduler stopped")