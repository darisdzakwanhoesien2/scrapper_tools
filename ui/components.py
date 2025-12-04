import streamlit as st
import pandas as pd

def render_table(records, page=1, page_size=20):
    if not records:
        st.write("No data available.")
        return

    df = pd.DataFrame(records)
    start = (page - 1) * page_size
    end = start + page_size
    st.dataframe(df.iloc[start:end])

def download_buttons(records):
    import json
    st.download_button("Download JSON", json.dumps(records, indent=2), "dataset.json")

    import io
    df = pd.DataFrame(records)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button("Download CSV", csv_buf.getvalue(), "dataset.csv")
