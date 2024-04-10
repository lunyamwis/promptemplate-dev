import time
import urllib.parse
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .utils import setup_driver
from boostedchatScrapper.models import Link



def generate_gmap_links(url,area):
    driver = setup_driver()
    google_maps_url = (
            url
            + urllib.parse.quote_plus(area)
            + "?hl=en"
    )
    driver.get(google_maps_url)
    links = []
    time.sleep(7)  # Wait for the page to load dynamically
    divSideBar = None
    try:
        divSideBar = driver.find_element(
            By.CSS_SELECTOR, f"div[aria-label='Results for {area}']"
        )
    except NoSuchElementException as err:
        print("************************search box not found**********************************")

   
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
                    # Link.objects.create(url=element.get_attribute("href"),name='gmaps')
                except Exception as error:
                    print(error)
                    
        if html.find("You've reached the end of the list.") != -1:
            keepScrolling = False
        
       
    driver.quit()
    
    return links



