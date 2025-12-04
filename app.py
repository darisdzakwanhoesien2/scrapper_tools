import streamlit as st
from core.scraper import scrape_url
from services.dataset_service import DatasetService
from ui.layout import sidebar_layout, main_layout

st.set_page_config(page_title="Scraper App", layout="wide")

dataset = DatasetService()

sidebar_layout()

st.title("🌐 URL Scraper Tool")

with st.form("scrape_form"):
    url = st.text_input("Enter URL to scrape")
    paginate = st.checkbox("Enable pagination", True)
    merge_data = st.checkbox("Merge into dataset", True)
    submit = st.form_submit_button("Scrape")

if submit:
    with st.spinner("Scraping..."):
        result = scrape_url(url, paginate=paginate)

    if result.get("error"):
        st.error(result["error"])
    else:
        st.success("Scraping successful")
        st.json(result["data"])

        if merge_data:
            merge_info = dataset.merge(result["data"])
            st.info(f"Added: {merge_info['added']} | Duplicates removed: {merge_info['deduped']}")

main_layout(dataset)



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