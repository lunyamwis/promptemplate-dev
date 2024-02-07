import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--lang=en")
    # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager(
            # latest_release_url='https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json',
            # driver_version='116.0.5845.96').install()), options=options)
    driver = webdriver.Chrome(options=options)
    return driver

def click_element(xpath):
    driver = setup_driver()
    try:
        element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))  
        element.click()
    except NoSuchElementException as err:
        logging.warning(err)
    return driver

def generate_html(url):
    driver = setup_driver()
    driver.get(url)
    return driver
