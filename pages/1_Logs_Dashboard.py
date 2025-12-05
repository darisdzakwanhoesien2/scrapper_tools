import streamlit as st
from pathlib import Path

st.title("📘 Scraper Logs Dashboard")

log_path = Path("data/logs/scraper.log")

if not log_path.exists():
    st.info("No logs yet.")
else:
    logs = log_path.read_text().split("\n")
    logs = [l for l in logs if l.strip()]

    st.write(f"Total log entries: {len(logs)}")

    # Filters
    status = st.selectbox("Filter by status", ["ALL", "SUCCESS", "ERROR", "SKIPPED"])

    filtered = []
    for line in logs:
        if status != "ALL" and f"| {status} |" not in line:
            continue
        filtered.append(line)

    st.write(f"Showing {len(filtered)} entries")

    st.code("\n".join(filtered), language="text")
