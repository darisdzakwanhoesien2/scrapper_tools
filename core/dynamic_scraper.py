from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


def load_dynamic_page(url, wait=3):
    """Load a dynamic webpage with Selenium and return parsed BeautifulSoup."""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        ChromeDriverManager().install(),
        options=chrome_options
    )

    driver.get(url)
    time.sleep(wait)  # wait for JS to render

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    return soup
