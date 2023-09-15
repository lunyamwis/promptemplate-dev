import logging
import scrapy
import time
import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import HtmlResponse
from selenium.webdriver.common.by import By
from boostedchatScrapper.items import StyleSeatItem
from urllib.parse import urlparse, parse_qs
from .helpers.styleseat_dynamic_actions import generate_styleseat_links
from .helpers.utils import click_element,generate_html
from ..http import SeleniumRequest

CLEAN_STRING = re.compile(r"[\']")

class StyleseatSpider(CrawlSpider):
    name = "styleseat"
    allowed_domains = ["www.styleseat.com"]
    base_url = "https://www.styleseat.com"
    start_urls = ["https://www.styleseat.com/m/search/wilmington-nc/natural-hair"]
    start_url = "https://www.styleseat.com/m/v/barberpaul"

    rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse", follow=True),)

    def start_requests(self):
        
        # urls = generate_styleseat_links(self.start_urls[0])
        # for url in urls:
        #     page  = generate_html(url)

        url = self.start_url
        yield SeleniumRequest(
                url = url,
                callback = self.parse
            )

    


    def parse(self, response):
        styleseat_item = StyleSeatItem()
        resp_meta = {}
        print("==================☁️☁️meta_driver☁️☁️===========")
        print(response.request.meta)
        print("==================☁️☁️meta_driver☁️☁️===========")
        time.sleep(5)
        styleseat_item["name"] = "styleseat"
        resp_meta["name"] = "styleseat"
        resp_meta["secondary_name"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//h1[@data-testid="proName"]').text
        print(f"resp_meta------------------------------->{resp_meta}")
        resp_meta["logo_url"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[contains(@class,"avatar-icon")]').get_attribute("style")
        resp_meta["profileUrl"] = response.url
        print(f"resp_meta------------------------------->{resp_meta}")
        resp_meta["category"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="proProfession"]').text
        try:
            resp_meta["igname"] = response.request.meta['driver'].find_element(by=By.XPATH, value='///div[@data-testid="instagram-link"]/div[2]').text
        except Exception as error:
            print(error)
        resp_meta["businessName"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="proBusinessName"]').text
        resp_meta["ratings"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="rating-stars"]').text
        resp_meta["serviceTitle"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//h4[@data-testid="serviceTitle"]')]
        resp_meta["serviceDetails"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="serviceDetails"]')]
        resp_meta["descriptionSection"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="description_section"]')]
        print(f"resp_meta------------------------------->{resp_meta}")
        resp_meta['address'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="address-component"]').text
        resp_meta['google_link_address'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@class="css-1dbjc4n"]/a').get_attribute("href")
        resp_meta['phone_number'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@class="css-1dbjc4n"]/a/../div').text
        resp_meta['business_hours_sunday'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="day-Sunday-value"]').text
        resp_meta['business_hours_monday'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="day-Monday-value"]').text
        resp_meta['business_hours_tuesday'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="day-Tuesday-value"]').text
        resp_meta['business_hours_wednesday'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="day-Wednesday-value"]').text
        resp_meta['business_hours_thursday'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="day-Thursday-value"]').text
        resp_meta['business_hours_friday'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="day-Friday-value"]').text
        resp_meta['business_hours_saturday'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="day-Saturday-value"]').text
        resp_meta['cancellation_policy'] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="cancellationPolicy--text"]').text
        print(f"resp_meta------------------------------->{resp_meta}")
        time.sleep(2)

        print("==================☁️☁️reviews_page☁️☁️===========")
        
        response.request.meta['driver'].get(response.url)   
        
        reviews = []
        time.sleep(6)
        try:
        
            response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="tab-navigation-Reviews"]/div').click()
            time.sleep(5)
            # import pdb;pdb.set_trace()
            for elem in response.request.meta['driver'].find_elements(by=By.XPATH,value='//div[@data-testid="review__review-container"]'):
                try:
                    review = {
                        "reviews" : elem.find_element(by=By.XPATH, value='//div[@data-testid="review-star-summary"]').text,
                        "clientPhotosNo" : elem.find_element(by=By.XPATH, value='//h3[@role="heading"]').text,    
                        "review_text" : elem.find_element(by=By.XPATH, value='//div[@data-testid="review__review-text"]/div/div').text,
                        "aboutClientAdjectives" : elem.find_element(by=By.XPATH, value='//div[@data-testid="review__about-provider"]').text,
                        "aboutClientLocation" : elem.find_element(by=By.XPATH, value='//div[@data-testid="review__about-location"]').text,
                        "reviewerNameAndDate" :elem.find_element(by=By.XPATH, value='//div[@data-testid="review__reviewer-name"]').text,
                        "reviewServiceName" : elem.find_element(by=By.XPATH, value='//div[@data-testid="review__service-name"]').text,
                    }
                except Exception as error:
                    print(error)
                reviews.append(review)
            print("==================☁️☁️client_adjectives☁️☁️===========")
            print(reviews)
            print("==================☁️☁️client_adjectives☁️☁️===========")
        except Exception as error:
            print(error)

        resp_meta['reviews'] = reviews
        response.request.meta['driver'].get(response.url)
        time.sleep(5)
        
        try:
            response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="tab-navigation-About"]/div').click()
            time.sleep(5)
            resp_meta["aboutName"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="pro-greeting"]')]
            resp_meta["joined"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div/[@data-testid="provider-info-joined-on-text"]')]
            resp_meta["verifiedAndNoBookedClients"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="profile-highlights-explainer"]')]
            resp_meta["infoAboutMe"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="provider-info-about-me-section"]')]
        except Exception as error:
            print(error)

        try:
            response.request.meta['driver'].get(response.url)
            time.sleep(5)
            response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="tab-navigation-Products"]/div').click()
            resp_meta["productTitle"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="product-title"]')]
            resp_meta["productDetails"] = [elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="expandable-text-content"]')]
        
        except Exception as error:
            print(error)

        if response.url:
            resp_meta["gallery_image_urls"] = [elem.get_attribute("src") for elem in response.request.meta['driver'].find_elements(by=By.TAG_NAME, value='img')]
        
        response.request.meta['driver'].get(response.url)
        time.sleep(5)
        try:
            response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="tab-navigation-Services"]/div').click()
            time.sleep(5)
            time_urls = [x.get_attribute("href") for x in response.request.meta['driver'].find_elements(by=By.XPATH, value='//a[@data-testid="bookButton"]')] 
            print("==================☁️☁️time_urls☁️☁️===========")
            print(time_urls)
            print("==================☁️☁️time_urls☁️☁️===========")
        except Exception as error:
            print(error)


        # available_dates = []
        # available_dates_slots = []
        # available_dates_slots_booked = []
        # unavailable_dates = []
        # for i,url in enumerate(time_urls):
        #     time.sleep(7)
        #     response.request.meta['driver'].get(url)
        #     time.sleep(7)
        #     try:

        #         available_dates.append([elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="sunshine-dot"]/../../../div')])
        #         unavailable_dates.append([elem.text for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@style, "text-decoration-line: line-through;")]/../../../div')])
        #         print("==================☁️☁️☁️☁️availabledates☁️☁️☁️☁️===========")
        #         print(available_dates)
        #         print("==================☁️☁️☁️☁️availabledates☁️☁️☁️☁️===========")
        #         for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="sunshine-dot"]/../../../div'):
        #             elem.click()
        #             time.sleep(7)
        #             available_dates_slots.append([el.text for el in response.request.meta['driver'].find_elements(by=By.XPATH,value='//button[@class="ss-button medium text-light"]')])
        #             try:
        #                 booked_elements = []
        #                 for i in range(100):
        #                     try:
        #                         booked_elements.append(response.request.meta['driver'].find_element(by=By.XPATH,value=f'//div[@data-testid="bookedtimepill-{i}"]/div'))
        #                     except Exception as error:
        #                         print(error)
        #                     for booked_element in booked_elements:
        #                         try:
        #                             available_dates_slots_booked.append(booked_element.text)
        #                         except Exception as error:
        #                             print(error)
                                
        #             except Exception as error:
        #                 print(error)
        #             print("==================☁️☁️☁️☁️available_dates_slots☁️☁️☁️☁️===========")
        #             print(available_dates_slots)
        #             print("==================☁️☁️☁️☁️available_dates_slots☁️☁️☁️☁️===========")
        #             print("==================☁️☁️☁️☁️available_dates_slots_booked☁️☁️☁️☁️===========")
        #             print(available_dates_slots_booked)
        #             print("==================☁️☁️☁️☁️available_dates_slots_booked☁️☁️☁️☁️===========")
        #             time.sleep(5)
        #             response.request.meta['driver'].get(url)
        #             time.sleep(7)


        #     except Exception as error:
        #         print(error)

        # resp_meta["availableDates"] = available_dates
        # resp_meta["availableDateSlots"] = available_dates_slots
        # resp_meta["availableDateSlotsBooked"] = available_dates_slots_booked
        # resp_meta["unavailableDates"] = unavailable_dates


        styleseat_item["resp_meta"] = resp_meta
        yield resp_meta
        

    def parse_dates(self,response):
        item = {}
        item["availableDates"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="sunshine-dot"]/../../../div')]
        item["unavailableDates"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[contains(@style, "text-decoration-line: line-through;")]/../../../div')]
        yield item


    def parse_reviews(self,response):
        item = {}
        item["reviews"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="review-star-summary"]').text
        item["clientPhotosNo"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//h3[@role="heading"]').text
        
            
        item["aboutClientAdjectives"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="review__about-provider"]')]
        item["aboutClientLocation"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="review__about-location"]')]
        item["reviewerNameAndDate"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="review__reviewer-name"]')]
        item["reviewServiceName"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="review__service-name"]')]
        
        yield item
 
    def parse_about(self,response):
        item = {}
        try:
            item["aboutName"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="pro-greeting"]')]
            item["joined"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div/[@data-testid="provider-info-joined-on-text"]')]
            item["verifiedAndNoBookedClients"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="profile-highlights-explainer"]')]
            item["infoAboutMe"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="provider-info-about-me-section"]')]
        except Exception as error:
            print(error)
        yield item


    def parse_products(self,response):
        item = {}
        item["productTitle"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="product-title"]')]
        item["productDetails"] = [CLEAN_STRING.sub("",elem.text) for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="expandable-text-content"]')]
        yield item


    def parse_client_images(self,response):
        item = {}
        item["client_image_urls"] = [elem.get_attribute("src") for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="modal-box-scroll-view"]//img')]
        yield item

    def parse_gallery(self,response):
        item = {}
        item["gallery_image_urls"] = [elem.get_attribute("src") for elem in response.request.meta['driver'].find_elements(by=By.XPATH, value='//div[@data-testid="modal-box-scroll-view"]//img')]
        yield item
