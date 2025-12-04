# utils/html_utils.py
from bs4 import BeautifulSoup


def clean_html_text(soup):
    for s in soup(["script", "style"]):
        s.extract()
    return soup.get_text(separator="\n", strip=True)
