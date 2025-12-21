import os
import json
from bs4 import BeautifulSoup

# Define the path to the HTML file
HTML_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "../scraped_html/data.html"
)

# Define the output JSON file path
OUTPUT_JSON_PATH = os.path.join(
    os.path.dirname(__file__), "../data/processed/netherlands_data.json"
)

def parse_html_to_json(html_file_path, output_json_path):
    """
    Parses the given HTML file and converts the extracted data into JSON format.

    Args:
        html_file_path (str): Path to the HTML file.
        output_json_path (str): Path to save the output JSON file.
    """
    try:
        # Read the HTML file
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Debug: Print the parsed HTML structure
        print("Parsed HTML content:")
        print(soup.prettify()[:500])  # Print the first 500 characters for inspection

        # Extract relevant data (example: table rows, divs, etc.)
        # Modify the selectors based on the structure of your HTML file
        data = []
        for item in soup.find_all("div", class_="data-item"):  # Example selector
            title = item.find("h2").get_text(strip=True) if item.find("h2") else None
            description = item.find("p").get_text(strip=True) if item.find("p") else None
            link = item.find("a")["href"] if item.find("a") else None

            # Debug: Print extracted data for each item
            print(f"Extracted item: title={title}, description={description}, link={link}")

            # Append the extracted data to the list
            data.append({
                "title": title,
                "description": description,
                "link": link
            })

        # Save the extracted data to a JSON file
        with open(output_json_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)

        print(f"Data successfully parsed and saved to {output_json_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Run the parser
    parse_html_to_json(HTML_FILE_PATH, OUTPUT_JSON_PATH)