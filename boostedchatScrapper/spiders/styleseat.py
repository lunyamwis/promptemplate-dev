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

    rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse", follow=True),)

    def start_requests(self):
        urls = generate_styleseat_links(self.start_urls[0])
        for url in urls:
            page  = generate_html(url)
            yield SeleniumRequest(
                    url = page.current_url,
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
        
            
        reviews_page = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="tab-navigation-Reviews"]/div').click()
        if reviews_page:
            yield SeleniumRequest(
                    url = response.request.meta['driver'].current_url,
                    callback = self.parse_reviews,
                    meta = resp_meta
                )

        about_page = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="tab-navigation-About"]/div').click()
        if about_page:
            yield SeleniumRequest(
                    url = response.request.meta['driver'].current_url,
                    callback = self.parse_about,
                    meta = resp_meta
                )

        try:
            products_page = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="tab-navigation-Products"]/div').click()
            if products_page:
                yield SeleniumRequest(
                        url = response.request.meta['driver'].current_url,
                        callback = self.parse_products,
                        meta = resp_meta
                    )
        except Exception as error:
            print(error)

        if response.url:
            parsed_url = urlparse(response.url)
            params = parse_qs(parsed_url.query)
            proId = params['proId'][0]
            print("==================☁️☁️proId☁️☁️===========")
            print(proId)
            print("==================☁️☁️proId☁️☁️===========")
            yield SeleniumRequest(
                url = f"{self.base_url}/m/p/{proId}/gallery",
                callback = self.parse_gallery
            )

        services_page = response.request.meta['driver'].find_element(by=By.XPATH, value='//div[@data-testid="tab-navigation-Services"]/div').click()
        if services_page:
            time_urls = [x.get_attribute("href") for x in response.request.meta['driver'].find_elements(by=By.XPATH, value='//a[@data-testid="bookButton"]')] 
            for url in time_urls:
                time.sleep(2)
                page  = generate_html(url)
                yield SeleniumRequest(
                        url = page.current_url, 
                        callback=self.parse_dates
                    )
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
