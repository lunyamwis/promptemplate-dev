import logging
import scrapy
import time
import re
import math

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import HtmlResponse
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.by import By
from boostedchatScrapper.items import StyleSeatItem
from urllib.parse import urlparse, parse_qs
from .helpers.styleseat_dynamic_actions import generate_styleseat_links
from .helpers.utils import click_element,generate_html
from ..http import SeleniumRequest

CLEAN_STRING = re.compile(r"[\']")

class MindBodyOnlineSpider(CrawlSpider):
    name = "mindbodyonline"
    allowed_domains = ["www.mindbodyonline.com"]
    base_url = "https://www.mindbodyonline.com"
    start_urls = [
        "https://www.mindbodyonline.com/explore/locations/f45-training-kirkland-moss-bay",
        "https://www.mindbodyonline.com/explore/locations/pura-buena-onda-north-park",
        "https://www.mindbodyonline.com/explore/locations/breath-oneness",
        "https://www.mindbodyonline.com/explore/locations/move-massage-fitness-lifestyle"
    ]
    
    rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse", follow=True),)

    def start_requests(self):
        
        # urls = generate_styleseat_links(self.start_urls[0])
        # for url in urls:
        #     page  = generate_html(url)
        threads = []
        # with ThreadPoolExecutor(max_workers=10) as executor:
        #     for url in self.start_urls:
        #         requests = SeleniumRequest(
        #             url = url,
        #             callback = self.parse
        #         )
        #         threads.append(
        #             executor.submit(
        #                 requests, url, self.parse
        #             )
        #         )

        #     for t in as_completed(threads):
        #         yield t.result()
                
        for url in self.start_urls:
            yield SeleniumRequest(
                    url = url,
                    callback = self.parse
                )

    


    def parse(self, response):
        # styleseat_item = StyleSeatItem()
        resp_meta = {}
        print("==================☁️☁️meta_driver☁️☁️===========")
        print(response.request.meta)
        print("==================☁️☁️meta_driver☁️☁️===========")
        # time.sleep(10)
        # resp_meta["secondary_name"] = response.request.meta['driver'].find_element(by=By.XPATH, value='//h2[@class="is-marginless"]').text
        # resp_meta["address"] = response.request.meta['driver'].find_element(by=By.XPATH, value='DetailHeader_address__3jDc1').text
        resp_meta["gmaps_link"] = response.request.meta['driver'].find_element(by=By.XPATH,value='//a[@class="StudioAddress_link__3HM2W is-inline-block"]').get_attribute("href")
        print(f"resp_meta------------------------------->{resp_meta}")
        
        yield resp_meta
        

   