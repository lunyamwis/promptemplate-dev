import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .utils import setup_driver




def generate_gmap_links(url,area):
    driver = setup_driver()
    driver.get(url)
    links = []
    time.sleep(7)  # Wait for the page to load dynamically
    search_box = driver.find_element(By.CSS_SELECTOR, '#searchboxinput')
    
    search_box.send_keys(area)  # Perform a search
    search = driver.find_element(By.XPATH, '//*[@id="searchbox-searchbutton"]')
    search.click()
    time.sleep(7)  # Wait for the search results to load
    
    divSideBar = None
    try:
        divSideBar = driver.find_element(
            By.CSS_SELECTOR, f"div[aria-label='Matokeo ya {area}']"
        )
    except NoSuchElementException as err:
        print(err)
        try:
            divSideBar = driver.find_element(
                By.CSS_SELECTOR, f"div[aria-label='Results of {area}']"
            )
        except NoSuchElementException as err:
            print(err)

    i = 0
    keepScrolling = True
    while keepScrolling:
        time.sleep(3)
        divSideBar.send_keys(Keys.PAGE_DOWN)
        time.sleep(3)
        divSideBar.send_keys(Keys.PAGE_DOWN)
        time.sleep(3)
        html = driver.find_element(By.TAG_NAME, "html").get_attribute("outerHTML")
        links_ = divSideBar.find_elements(By.TAG_NAME, "a")
        
                
        for ind, element in enumerate(links_):
            time.sleep(2)
            print("==================☁️☁️☁️☁️☁️links☁️☁️☁️☁️☁️===========")    
            logging.warning(f"link-{ind}=>{element.get_attribute('href')}")
            print("==================☁️☁️☁️☁️☁️links☁️☁️☁️☁️☁️===========")  
              

            if "place" in element.get_attribute("href"):
                try:
                    links.append(element.get_attribute("href"))
                except Exception as error:
                    print(error)
            
            
            if len(links) == 1:
                break

        if len(links) == 1:
                break        
        # if html.find("You've reached the end of the list.") != -1:
            # keepScrolling = False
        # elif html.find("Umefikia mwisho wa orodha.") != -1:
            # keepScrolling = False

       
    driver.quit()
    return links



