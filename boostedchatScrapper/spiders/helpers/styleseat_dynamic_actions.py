import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from .utils import setup_driver

def generate_styleseat_links(url):
    driver = setup_driver()
    driver.get(url)
    driver.implicitly_wait(5)
    time.sleep(10)  # Wait for the page to load dynamically
    url_list = []

    list_of_seats = None
    try:
        list_of_seats = driver.find_element(By.XPATH, "//div[contains(@class,'search-results-list-component')]")
    except TimeoutException:
        print("No popup...")

    i = 0
    while True:

        try:
            loadMoreButton = list_of_seats.find_element(
                By.XPATH, "//li[contains(@class,'load-more-wrapper')]/button"
            )
            time.sleep(4)
            logging.warning(f"state -- {i+1}")
            loadMoreButton.click()
            time.sleep(4)

        except Exception as e:
            print(e)
            break

    try:
        names = list_of_seats.find_elements(By.TAG_NAME, "h3")
    except NoSuchElementException:
        print("escape")
    for name in names:
        logging.warning(f"state --- {name}")
        name.click()
        time.sleep(5)

    for window in range(1, len(driver.window_handles)):
        try:
            driver.switch_to.window(driver.window_handles[window])
        except IndexError as err:
            print(f"{err}")

        url_list.append(driver.current_url)
        logging.warning(f"state --- {driver.current_url}")
        if window == 1:

            break
        
    driver.switch_to.window(driver.window_handles[0])
    driver.quit()

    return url_list