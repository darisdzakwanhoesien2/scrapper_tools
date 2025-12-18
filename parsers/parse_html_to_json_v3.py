import os
import json
from bs4 import BeautifulSoup


def parse_html_to_json_v3(html_file_path, output_json_path):
    """
    Enhanced HTML to JSON parser:
    - Title
    - Metadata (meta tags, Open Graph tags)
    - Head + Body HTML
    - Plain text
    - Links
    - Images
    - Structured content (headings, paragraphs)
    """

    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML file not found: {html_file_path}")

    with open(html_file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Extract metadata
    metadata = {}
    for meta in soup.find_all("meta"):
        if meta.get("name"):
            metadata[meta["name"]] = meta.get("content", "")
        if meta.get("property"):
            metadata[meta["property"]] = meta.get("content", "")

    # Extract structured content
    structured_content = []
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        structured_content.append({
            "type": "heading",
            "level": heading.name,
            "content": heading.get_text(strip=True)
        })

    for paragraph in soup.find_all("p"):
        structured_content.append({
            "type": "paragraph",
            "content": paragraph.get_text(strip=True)
        })

    # Compile parsed data
    parsed = {
        "title": soup.title.string if soup.title else None,
        "metadata": metadata,
        "head_html": str(soup.head) if soup.head else None,
        "body_html": str(soup.body) if soup.body else None,
        "all_text": soup.get_text(" ", strip=True),
        "links": [a["href"] for a in soup.find_all("a", href=True)],
        "images": [img["src"] for img in soup.find_all("img", src=True)],
        "structured_content": structured_content
    }

    # Save to JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=4, ensure_ascii=False)

    return parsed


# ----------------------------------------------------------------------------
# REQUIRED FORMAT FOR STREAMLIT PIPELINE: must return (success, result_dict)
# ----------------------------------------------------------------------------
def run_parser(html_file_path, output_json_path):
    try:
        data = parse_html_to_json_v3(html_file_path, output_json_path)

        return True, {
            "status": "success",
            "html_file_path": html_file_path,
            "output_json_path": output_json_path,
            "items_extracted": len(data) if isinstance(data, dict) else None
        }

    except Exception as e:
        return False, {
            "status": "error",
            "error": str(e),
            "html_file_path": html_file_path,
            "output_json_path": output_json_path
        }


if __name__ == "__main__":
    test_html = "scraped_html/2025-12-13T21-27-40_Requests_unknown.html"
    test_out = "scraped_html/2025-12-13T21-27-40_Requests_unknown_parsed_v3.json"
    print(run_parser(test_html, test_out))