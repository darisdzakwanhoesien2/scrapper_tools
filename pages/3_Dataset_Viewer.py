import streamlit as st
from services.dataset_service import DatasetService
from ui.components import render_table, download_buttons

st.title("📊 Dataset Viewer")

dataset = DatasetService()
records = dataset.get()

page = st.number_input("Page", min_value=1, value=1)
page_size = st.selectbox("Page size", [10, 20, 50, 100], 1)

render_table(records, page, page_size)
download_buttons(records)
