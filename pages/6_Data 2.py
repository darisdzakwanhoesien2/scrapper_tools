import streamlit as st
import os
import json
from bs4 import BeautifulSoup


# =========================================================
# THE SAME PARSER FUNCTION YOU PROVIDED
# =========================================================
def parse_html_to_json(html_file, output_file, parser_type="type_1"):

    if not os.path.exists(html_file):
        return None, f"Error: File '{html_file}' does not exist."

    with open(html_file, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # Helper for section extraction
    def extract_section_by_keywords(soup, keywords, max_nodes=50):
        sections = []
        keywords = [k.lower() for k in keywords]

        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = heading.get_text(strip=True).lower()
            if any(k in text for k in keywords):

                items = []
                count = 0

                for sib in heading.next_siblings:
                    if isinstance(sib, str):
                        continue
                    if sib.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        break
                    if sib.name in ["p", "li", "div", "span"]:
                        t = sib.get_text(strip=True)
                        if t:
                            items.append(t)
                        count += 1
                    if count >= max_nodes:
                        break

                if items:
                    sections.append({
                        "heading": heading.get_text(strip=True),
                        "items": items,
                    })

        return sections

    # Start parsing
    data = []

    if parser_type == "type_1":
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if t:
                data.append({"type": "paragraph", "content": t})
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            t = h.get_text(strip=True)
            if t:
                data.append({"type": "heading", "level": h.name, "content": t})

    elif parser_type == "type_2":
        for a in soup.find_all("a"):
            data.append({
                "type": "link",
                "href": a.get("href"),
                "content": a.get_text(strip=True),
            })
        for li in soup.find_all("li"):
            t = li.get_text(strip=True)
            if t:
                data.append({"type": "list_item", "content": t})

    elif parser_type == "type_3":
        keywords = ["job description", "role description",
                    "main activities", "responsibilities", "what will you do"]
        sections = extract_section_by_keywords(soup, keywords)
        for sec in sections:
            for item in sec["items"]:
                data.append({
                    "type": "job_description",
                    "section": sec["heading"],
                    "content": item
                })

    elif parser_type == "type_4":
        keywords = ["skills", "competencies", "backgrounds", "preferred skills"]
        sections = extract_section_by_keywords(soup, keywords)
        for sec in sections:
            for item in sec["items"]:
                data.append({
                    "type": "skill",
                    "section": sec["heading"],
                    "content": item
                })

    elif parser_type == "type_5":
        keywords = ["eligibility", "requirements", "profile",
                    "who can apply", "criteria"]
        sections = extract_section_by_keywords(soup, keywords)
        for sec in sections:
            for item in sec["items"]:
                data.append({
                    "type": "eligibility",
                    "section": sec["heading"],
                    "content": item
                })

    else:
        return None, f"Error: Unknown parser type '{parser_type}'"

    # Save JSON output
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    return data, f"[OK] Parsed using {parser_type}. Saved to '{output_file}'."


# =========================================================
# STREAMLIT UI
# =========================================================

st.set_page_config(page_title="HTML → JSON Parser", layout="centered")
st.title("🔄 HTML → JSON Parser (Selectable Parser Types)")


# Directory containing scraped HTML
HTML_DIR = "scraped_html"

if not os.path.exists(HTML_DIR):
    st.error(f"Directory '{HTML_DIR}' does not exist. Run scraper first.")
    st.stop()

# List HTML files
html_files = [f for f in os.listdir(HTML_DIR) if f.endswith(".html")]

if not html_files:
    st.info("No HTML files found in scraped_html/. Scrape something first.")
    st.stop()

# --- UI: select HTML file ---
selected_html = st.selectbox("Choose HTML file", html_files)

# --- UI: select parser type ---
parser_types = {
    "Paragraphs & Headings": "type_1",
    "Links & List Items": "type_2",
    "Job Description Sections": "type_3",
    "Skills Sections": "type_4",
    "Eligibility Sections": "type_5",
}

selected_parser_label = st.selectbox("Choose Parser Type", list(parser_types.keys()))
selected_parser = parser_types[selected_parser_label]

# Determine output path
html_path = os.path.join(HTML_DIR, selected_html)
output_json_path = html_path.replace(".html", f"_{selected_parser}.json")

# --- Run parser button ---
if st.button("Parse Now"):
    parsed_data, message = parse_html_to_json(html_path, output_json_path, parser_type=selected_parser)

    st.success(message)

    if parsed_data:
        st.subheader("Preview of Parsed JSON:")
        st.json(parsed_data[:50])   # show first 50 entries

        st.write(f"💾 Output saved to: `{output_json_path}`")
