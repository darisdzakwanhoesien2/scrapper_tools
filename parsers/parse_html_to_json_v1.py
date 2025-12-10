import os
import json
from bs4 import BeautifulSoup


def parse_html_to_json(html_file_path, output_json_path):
    """
    Minimal parser: extracts headings + paragraphs.
    """

    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML file not found: {html_file_path}")

    with open(html_file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    extracted = []

    # Headings
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        extracted.append({
            "type": "heading",
            "level": heading.name,
            "content": heading.get_text(strip=True)
        })

    # Paragraphs
    for p in soup.find_all("p"):
        extracted.append({
            "type": "paragraph",
            "content": p.get_text(strip=True)
        })

    # Save
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=4, ensure_ascii=False)

    return extracted


# ----------------------------------------------------------------------------
# REQUIRED FORMAT FOR STREAMLIT PIPELINE: must return (success, result_dict)
# ----------------------------------------------------------------------------
def run_parser(html_file_path, output_json_path):
    try:
        data = parse_html_to_json(html_file_path, output_json_path)

        return True, {
            "status": "success",
            "html_file_path": html_file_path,
            "output_json_path": output_json_path,
            "items_extracted": len(data)
        }

    except Exception as e:
        return False, {
            "status": "error",
            "error": str(e),
            "html_file_path": html_file_path,
            "output_json_path": output_json_path
        }


if __name__ == "__main__":
    test_html = "scraped_html/sample.html"
    test_out = "scraped_html/sample_parsed_v1.json"
    print(run_parser(test_html, test_out))

# import os
# import json
# from bs4 import BeautifulSoup

# # Define the path to the HTML file
# html_file_path = "scraped_html/2025-12-10T18-57-51_Requests_1330505.html"

# # Define the output JSON file path
# output_json_path = "scraped_html/2025-12-10T18-57-51_Requests_1330505.json"

# def parse_html_to_json(html_file, output_file):
#     # Check if the HTML file exists
#     if not os.path.exists(html_file):
#         print(f"Error: File '{html_file}' does not exist.")
#         return

#     # Read the HTML file
#     with open(html_file, "r", encoding="utf-8") as file:
#         html_content = file.read()

#     # Parse the HTML content using BeautifulSoup
#     soup = BeautifulSoup(html_content, "html.parser")

#     # Extract relevant data (example: paragraphs, headings, etc.)
#     data = []
#     for paragraph in soup.find_all("p"):
#         data.append({"type": "paragraph", "content": paragraph.get_text(strip=True)})

#     for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
#         data.append({"type": "heading", "level": heading.name, "content": heading.get_text(strip=True)})

#     # Convert the extracted data to JSON
#     with open(output_file, "w", encoding="utf-8") as json_file:
#         json.dump(data, json_file, indent=4, ensure_ascii=False)

#     print(f"HTML content has been successfully parsed and saved to '{output_file}'.")

# # Run the parser
# parse_html_to_json(html_file_path, output_json_path)