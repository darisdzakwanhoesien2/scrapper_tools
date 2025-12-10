import os
import json
from bs4 import BeautifulSoup


def parse_html_to_json(html_file_path, output_json_path):
    """
    Full extraction parser:
    - Title
    - Head + Body HTML
    - Plain text
    - Links
    - Images
    """

    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML file not found: {html_file_path}")

    with open(html_file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    parsed = {
        "title": soup.title.string if soup.title else None,
        "head_html": str(soup.head) if soup.head else None,
        "body_html": str(soup.body) if soup.body else None,
        "all_text": soup.get_text(" ", strip=True),
        "links": [a["href"] for a in soup.find_all("a", href=True)],
        "images": [img["src"] for img in soup.find_all("img", src=True)]
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=4, ensure_ascii=False)

    return parsed


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
    test_html = "scraped_html/sample.html"
    test_out = "scraped_html/sample_parsed_v2.json"
    print(run_parser(test_html, test_out))


# import os
# import json
# from bs4 import BeautifulSoup

# def parse_html_to_json(html_file_path, output_json_path):
#     """
#     Parses an HTML file and converts its content into JSON format.

#     Args:
#         html_file_path (str): Path to the HTML file to be parsed.
#         output_json_path (str): Path to save the resulting JSON file.
#     """
#     # Check if the HTML file exists
#     if not os.path.exists(html_file_path):
#         print(f"Error: File {html_file_path} does not exist.")
#         return

#     # Read the HTML file
#     with open(html_file_path, 'r', encoding='utf-8') as html_file:
#         html_content = html_file.read()

#     # Parse the HTML content using BeautifulSoup
#     soup = BeautifulSoup(html_content, 'html.parser')

#     # Extract data from the HTML (example: extracting all text and tags)
#     parsed_data = {
#         "title": soup.title.string if soup.title else None,
#         "head": str(soup.head) if soup.head else None,
#         "body": str(soup.body) if soup.body else None,
#         "all_text": soup.get_text(strip=True),
#         "links": [a['href'] for a in soup.find_all('a', href=True)],
#         "images": [img['src'] for img in soup.find_all('img', src=True)]
#     }

#     # Save the parsed data to a JSON file
#     with open(output_json_path, 'w', encoding='utf-8') as json_file:
#         json.dump(parsed_data, json_file, indent=4, ensure_ascii=False)

#     print(f"JSON file has been saved to {output_json_path}")

# if __name__ == "__main__":
#     # Define the input HTML file path and output JSON file path
#     html_file_path = "scraped_html/2025-12-10T19-52-39_Requests_unknown.html"
#     output_json_path = "scraped_html/2025-12-10T19-52-39_Requests_unknown.json"

#     # Parse the HTML and save it as JSON
#     parse_html_to_json(html_file_path, output_json_path)