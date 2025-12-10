from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


def load_dynamic_page(url, wait=3, screenshot_path=None):
    """Load a dynamic webpage with Selenium and return BeautifulSoup + optional screenshot."""

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")   # NEW Chrome headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    # FIXED: Modern ChromeDriver construction
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)
    time.sleep(wait)  # allow JS to render

    # Optional screenshot
    if screenshot_path:
        driver.save_screenshot(screenshot_path)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    return soup


# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup
# import time


# def load_dynamic_page(url, wait=3):
#     """Load a dynamic webpage with Selenium and return parsed BeautifulSoup."""
    
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")

#     driver = webdriver.Chrome(
#         ChromeDriverManager().install(),
#         options=chrome_options
#     )

#     driver.get(url)
#     time.sleep(wait)  # wait for JS to render

#     html = driver.page_source
#     driver.quit()

#     soup = BeautifulSoup(html, "html.parser")
#     return soup
