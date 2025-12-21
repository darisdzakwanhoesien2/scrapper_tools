from playwright.sync_api import sync_playwright
from pathlib import Path

URL = "https://bigfuture.collegeboard.org/colleges/avery-james-college/campus-life"
OUTPUT_FILE = Path("avery_james_college_rendered_campus-life.html")

def download_rendered_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle")
        html = page.content()

        OUTPUT_FILE.write_text(html, encoding="utf-8")
        browser.close()

        print(f"Saved rendered HTML to: {OUTPUT_FILE.resolve()}")

if __name__ == "__main__":
    download_rendered_html()


# import requests
# from bs4 import BeautifulSoup
# import json

# # URL to scrape (profile page)
# BASE_URL = "https://bigfuture.collegeboard.org/colleges/avery-james-college"

# # Additional pages for detailed sections
# PAGES = {
#     "overview": BASE_URL,
#     "academics": BASE_URL + "/academics",
#     "costs": BASE_URL + "/tuition-and-costs",
#     "campus_life": BASE_URL + "/campus-life"
# }

# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
# }

# def fetch_page(url):
#     """Fetch the content of a URL with headers."""
#     r = requests.get(url, headers=HEADERS, timeout=10)
#     r.raise_for_status()
#     return r.text

# def scrape_overview(soup):
#     """Extract overview info."""
#     info = {}
#     try:
#         # College name and location
#         header = soup.find("h1")
#         if header:
#             info["name"] = header.get_text(strip=True)

#         loc = soup.select_one(".college-header-location")
#         if loc:
#             info["location"] = loc.get_text(strip=True)

#         # Overview details (type, campus life, aid, SAT, graduation rate)
#         rows = soup.select("section[data-test='college-overview'] dl")
#         for dl in rows:
#             items = dl.find_all(["dt", "dd"])
#             for i in range(0, len(items), 2):
#                 key = items[i].get_text(strip=True).rstrip(":")
#                 val = items[i+1].get_text(strip=True)
#                 info[key.lower().replace(" ", "_")] = val
#     except Exception as e:
#         print("Overview parse error:", e)
#     return info

# def scrape_academics(soup):
#     """Extract academic info."""
#     data = {}
#     try:
#         for dl in soup.find_all("dl"):
#             items = dl.find_all(["dt", "dd"])
#             for i in range(0, len(items), 2):
#                 key = items[i].get_text(strip=True).rstrip(":")
#                 val = items[i+1].get_text(strip=True)
#                 data[key.lower().replace(" ", "_")] = val
#     except Exception as e:
#         print("Academics parse error:", e)
#     return data

# def scrape_costs(soup):
#     """Extract tuition & costs info."""
#     data = {}
#     try:
#         for dl in soup.find_all("dl"):
#             items = dl.find_all(["dt", "dd"])
#             for i in range(0, len(items), 2):
#                 key = items[i].get_text(strip=True).rstrip(":")
#                 val = items[i+1].get_text(strip=True)
#                 data[key.lower().replace(" ", "_")] = val
#     except Exception as e:
#         print("Costs parse error:", e)
#     return data

# def scrape_campus_life(soup):
#     """Extract campus life info."""
#     data = {}
#     try:
#         # Example: Race & Ethnicity stats may be in tables
#         sections = soup.find_all("section")
#         for sec in sections:
#             heading = sec.find("h2")
#             if heading:
#                 key = heading.get_text(strip=True).lower().replace(" ", "_")
#                 # Collect text under that section
#                 data[key] = sec.get_text(separator=" | ", strip=True)
#     except Exception as e:
#         print("Campus life parse error:", e)
#     return data

# # MAIN
# all_data = {}

# for section, url in PAGES.items():
#     print(f"Fetching {section} from {url} …")
#     html = fetch_page(url)
#     soup = BeautifulSoup(html, "html.parser")

#     if section == "overview":
#         all_data["overview"] = scrape_overview(soup)
#     elif section == "academics":
#         all_data["academics"] = scrape_academics(soup)
#     elif section == "costs":
#         all_data["costs"] = scrape_costs(soup)
#     elif section == "campus_life":
#         all_data["campus_life"] = scrape_campus_life(soup)

# # Output JSON
# print(json.dumps(all_data, indent=2))
