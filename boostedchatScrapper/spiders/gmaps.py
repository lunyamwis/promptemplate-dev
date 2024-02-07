import logging
import scrapy
import time
import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import HtmlResponse
from selenium.webdriver.common.by import By
from .helpers.gmaps_dynamic_actions import generate_gmap_links
from .helpers.utils import click_element,generate_html
from ..http import SeleniumRequest
from boostedchatScrapper.items import GmapsItem
from .helpers.instagram_login_helper import login_user

CLEAN_STRING = re.compile(r"[\']")

class GmapsSpider(CrawlSpider):
    name = "gmaps"
    allowed_domains = ["www.google.com"]
    base_url = "https://www.google.com/maps/"
    start_urls = [
        "https://www.google.com/maps/"

    ]

    rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse", follow=True),)

    def start_requests(self):
        urls = generate_gmap_links(self.start_urls[0],"Barbers, Orlando, FL")
        for url in urls:
            page  = generate_html(url)
            print("==================☁️☁️generated_url☁️☁️===========")
            print(page.current_url)
            print("==================☁️☁️generated_url☁️☁️===========")
            yield SeleniumRequest(
                    url = page.current_url,
                    callback = self.parse
                )

    
    

    def parse(self, response):
        print("==================☁️☁️titles_page☁️☁️===========")
        resp_meta = {}
        item = GmapsItem()
        item["name"] = "google_maps"
        resp_meta["name"] = "google_maps"
        resp_meta["title"] = CLEAN_STRING.sub("", response.request.meta['driver'].title)
        time.sleep(4)
        resp_meta["main_image"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//button[contains(@class,"aoRNLd kn2E5e NMjTrf lvtCsd")]/img').get_attribute("src")
        resp_meta["business_name"] = CLEAN_STRING.sub("",response.request.meta['driver'].find_element(by=By.XPATH, value='//span[contains(@class,"a5H0ec")]/..').text)
        resp_meta["review"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[contains(@class,"F7nice")]/span[1]').text
        ig_info = []
        try:
            client = login_user(username='stella.elth', password='martinnyambane1996-')
            print(f"11111111111111111111111111111{resp_meta['business_name']}111111111111111111")
            users = client.search_users_v1(resp_meta["business_name"],count=5)
            for user in users:
                user_data = client.user_info_by_username(user.username)
                if user_data.public_phone_country_code == '1':
                    ig_info.append(user_data.dict())
        except Exception as error:
            print("==************************************==we were incapable of acquiring their instagram information==*****************************==")

        resp_meta["ig_info"] = ig_info
        print("==================☁️☁️resp_meta☁️☁️===========")
        print(f"resp_meta------------------------------->{resp_meta}")
        print("==================☁️☁️resp_meta☁️☁️===========")
        
        resp_meta["no_reviews"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[contains(@class,"F7nice")]/span[2]').text
        resp_meta["category"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//button[contains(@class,"DkEaL")]').text
        resp_meta["review_names"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"d4r55")]')]
        resp_meta["review_comments_given"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"MyEned")]/span')]
        resp_meta["review_rating_given"] = [elem.get_attribute("aria-label") for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//span[contains(@class,"kvMYJc")]')]
        resp_meta["review_time_given"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//span[contains(@class,"rsqaWe")]')]
        resp_meta["address"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"rogA2c")]/div')]
        print("==================☁️☁️resp_meta☁️☁️===========")
        print(f"resp_meta------------------------------->{resp_meta}")
        print("==================☁️☁️resp_meta☁️☁️===========")
        
        resp_meta["days_available"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//tr[contains(@class,"y0skZc")]/td/div')]
        resp_meta["times_available"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//tr[contains(@class,"y0skZc")]/td/ul/li')]

        print("==================☁️☁️resp_meta☁️☁️===========")
        print(f"resp_meta------------------------------->{resp_meta}")
        print("==================☁️☁️resp_meta☁️☁️===========")
        
        resp_meta["available_image_works"] = [elem.get_attribute("src") for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//img[contains(@class,"DaSXdd")]')]
        resp_meta["testimonial_wordings"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"ZXMsO")]')]
        resp_meta["testimonial_date"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"jrtH8d")]')]

        print("==================☁️☁️resp_meta☁️☁️===========")
        print(f"resp_meta------------------------------->{resp_meta}")
        print("==================☁️☁️resp_meta☁️☁️===========")
        
        try:
            
            resp_meta["is_booking_available"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//a[contains(@class,"A1zNzb")]').get_attribute("href")
            if resp_meta["is_booking_available"]:
                resp_meta["booking_header"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"XVS7ef")]')]
                resp_meta["booking_time"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"BRcyT JaMq2b")]')]
                resp_meta["booking_price"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"BRcyT JaMq2b")]/span')]
                resp_meta["booking_provider"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"NGLLDf")]/span')]
        except Exception as error:
            print("no booking available")

        try:
            response.request.meta['driver'].get(response.url)
            time.sleep(2)
            response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"Gpq6kf fontTitleSmall")]')[1].click() 
        except Exception as error:
            print(error)
        
        time.sleep(5)
        reviews_url = response.request.meta['driver'].current_url
        if reviews_url:
            resp_meta["review_names"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"d4r55")]')]
            resp_meta["review_content"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//span[contains(@class,"wiI7pd")]')]
            
        try:
            response.request.meta['driver'].get(response.url)
            time.sleep(2)
            response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"Gpq6kf fontTitleSmall")]')[2].click()
        except Exception as error:
            print(error)

        time.sleep(5)
        about_url = response.request.meta['driver'].current_url
        if about_url:
            resp_meta["tag_name"] =  [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//h2[contains(@class,"iL3Qke")]')]
            resp_meta["tag_detail"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//li[contains(@class,"hpLkke")]/span')]
        item["resp_meta"] = resp_meta
        yield resp_meta

    def parse_reviews(self,response):
        item = {}
        item["review_names"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"d4r55")]')]
        item["review_content"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//span[contains(@class,"wiI7pd")]')]
        print("==================☁️☁️reviews☁️☁️===========")
        print(f"reviews------------------------------->{item}")
        print("==================☁️☁️reviews☁️☁️===========")
        yield item


    def parse_booking_site(self,response):
        item = {}
        item["booking_header"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"XVS7ef")]')]
        item["booking_time"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"BRcyT JaMq2b")]')]
        item["booking_price"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"BRcyT JaMq2b")]/span')]
        item["booking_provider"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@class,"NGLLDf")]/span')]
        yield item
 
    def parse_about(self,response):
        item = {}
        item["tag_name"] =  [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//h2[contains(@class,"iL3Qke")]')]
        item["tag_detail"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//li[contains(@class,"hpLkke")]/span')]
        yield item


    