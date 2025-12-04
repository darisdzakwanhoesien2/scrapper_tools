import streamlit as st
from ui.components import render_table, download_buttons

def sidebar_layout():
    st.sidebar.header("Controls")

def main_layout(dataset_service):
    st.header("📊 Dataset Viewer")

    records = dataset_service.get()

    page = st.number_input("Page", min_value=1, value=1)
    page_size = st.selectbox("Page size", [10, 20, 50, 100], index=1)

    render_table(records, page, page_size)
    download_buttons(records)
