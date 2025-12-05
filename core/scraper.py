# import requests
# from bs4 import BeautifulSoup
# from core.validator import validate_url
# from utils.html_utils import clean_html_text
# from utils.json_utils import normalize_json


# def scrape_url(url: str, paginate=True):
#     valid = validate_url(url)
#     if not valid["ok"]:
#         return {"error": valid["error"]}

#     try:
#         resp = requests.get(url, timeout=10, headers={"User-Agent": "ScraperApp/1.0"})
#     except Exception as e:
#         return {"error": str(e)}

#     content_type = resp.headers.get("Content-Type", "")

#     # JSON response
#     if "application/json" in content_type:
#         try:
#             data = normalize_json(resp.json())
#         except:
#             return {"error": "Invalid JSON response"}

#         # Handle simple pagination with next field
#         if paginate and isinstance(data, dict) and data.get("next"):
#             items = data.get("data") or data.get("items") or []
#             next_url = data.get("next")

#             page_count = 0
#             while next_url and page_count < 20:
#                 try:
#                     r2 = requests.get(next_url, timeout=10)
#                     d2 = r2.json()
#                     batch = d2.get("data") or d2.get("items") or []
#                     items.extend(batch)
#                     next_url = d2.get("next")
#                     page_count += 1
#                 except:
#                     break

#             return {"data": items}

#         return {"data": data}

#     # HTML fallback
#     soup = BeautifulSoup(resp.text, "html.parser")
#     return {"data": {"text": clean_html_text(soup)}}

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from core.validator import validate_url
from utils.html_utils import clean_html_text


def scrape_url(url: str, paginate=True):
    valid = validate_url(url)
    if not valid["ok"]:
        return {"error": valid["error"]}

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "ScraperApp/1.0"})
    except Exception as e:
        return {"error": str(e)}

    content_type = resp.headers.get("Content-Type", "")

    if "application/json" in content_type:
        try:
            return {"data": resp.json()}
        except:
            return {"error": "JSON parse failed"}

    # HTML scraper
    soup = BeautifulSoup(resp.text, "html.parser")
    return {"data": extract_structured_html(url, soup)}


def extract_structured_html(base_url, soup):
    data = {}

    # Page title (from <title>)
    if soup.title:
        data["page_title"] = soup.title.get_text(strip=True)

    # H1
    h1 = soup.find("h1")
    data["h1"] = h1.get_text(strip=True) if h1 else None

    # Sections with H2
    sections = []
    for h2 in soup.find_all("h2"):
        section_name = h2.get_text(strip=True)
        section_content = extract_section_content(h2)
        sections.append({
            "header": section_name,
            "content": section_content
        })

    data["sections"] = sections

    return data

def extract_section_content(h2_tag):
    section = []

    for sib in h2_tag.find_all_next():
        # Stop when next section begins
        if sib.name == "h2":
            break

        # Paragraphs
        if sib.name == "p":
            section.append({
                "type": "paragraph",
                "text": sib.get_text(strip=True)
            })

        # Cards (div with <h3>)
        if sib.name == "div" and sib.find("h3"):
            card_title = sib.find("h3").get_text(strip=True)

            desc_tag = sib.find("p")
            desc = desc_tag.get_text(strip=True) if desc_tag else ""

            a = sib.find("a")     # <-- safer extraction
            link = a.get("href") if a and a.has_attr("href") else None

            section.append({
                "type": "card",
                "title": card_title,
                "description": desc,
                "link": link
            })

    return section

# def extract_section_content(h2_tag):
#     section = []
#     for sib in h2_tag.find_all_next():
#         if sib.name == "h2":
#             break

#         if sib.name == "p":
#             section.append({
#                 "type": "paragraph",
#                 "text": sib.get_text(strip=True)
#             })

#         # Detect “cards”
#         if sib.name == "div" and sib.find("h3"):
#             card_title = sib.find("h3").get_text(strip=True)
#             desc = sib.find("p").get_text(strip=True) if sib.find("p") else ""
#             link = sib.find("a")["href"] if sib.find("a") else None

#             section.append({
#                 "type": "card",
#                 "title": card_title,
#                 "description": desc,
#                 "link": link
#             })

#     return section


# # core/scraper.py
# import requests
# from bs4 import BeautifulSoup
# from typing import Any, Dict
# from config.settings import SETTINGS
# from core.validator import validate_url
# from utils.html_utils import clean_html_text
# from utils.json_utils import normalize_json
# from services.storage_service import StorageService

# storage = StorageService()


# def _fetch(url: str) -> requests.Response:
#     headers = {"User-Agent": SETTINGS["user_agent"]}
#     return requests.get(url, headers=headers, timeout=SETTINGS["timeout"])


# def _handle_response(resp: requests.Response) -> Dict[str, Any]:
#     content_type = resp.headers.get("Content-Type", "")
#     if "application/json" in content_type:
#         try:
#             data = resp.json()
#             return {"type": "json", "data": normalize_json(data)}
#         except Exception as e:
#             return {"error": f"JSON parse error: {e}"}

#     # fallback to HTML
#     soup = BeautifulSoup(resp.text, "html.parser")
#     text = clean_html_text(soup)
#     return {"type": "html", "data": {"text": text}}


# def scrape_url(url: str, paginate: bool = True) -> Dict[str, Any]:
#     v = validate_url(url)
#     if not v["ok"]:
#         return {"error": v["error"]}

#     try:
#         resp = _fetch(url)
#     except Exception as e:
#         return {"error": f"Fetch error: {e}"}

#     result = _handle_response(resp)

#     # Save raw
#     storage.save_raw(url, resp.text)

#     # If pagination expected and JSON with list content, try to follow 'next' keys
#     if paginate and result.get("type") == "json":
#         data = result["data"]
#         # Basic pagination handlers — try common keys
#         items = []
#         if isinstance(data, dict):
#             # check for items
#             for key in ("data", "items", "results", "rows"):
#                 if key in data and isinstance(data[key], list):
#                     items = data[key]
#                     break

#             # naive next link
#             next_url = data.get("next") or data.get("next_page") or data.get("next_url")
#             pages = 0
#             while next_url and pages <  SETTINGS.get("max_pages", 10):
#                 try:
#                     resp2 = _fetch(next_url)
#                     storage.save_raw(next_url, resp2.text)
#                     r2 = _handle_response(resp2)
#                     if r2.get("type") == "json" and isinstance(r2.get("data"), dict):
#                         for key in ("data", "items", "results", "rows"):
#                             if key in r2["data"] and isinstance(r2["data"][key], list):
#                                 items.extend(r2["data"][key])
#                                 break
#                         next_url = r2["data"].get("next") or r2["data"].get("next_page")
#                     else:
#                         break
#                 except Exception:
#                     break
#                 pages += 1

#             if items:
#                 return {"data": items}

#         # default return
#         return {"data": data}

#     return {"data": result.get("data")}