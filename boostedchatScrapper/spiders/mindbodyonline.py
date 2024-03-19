import requests
import json
import scrapy
import os
from lxml import etree
from ..items import APIItem
from django.conf import settings
from boostedchatScrapper.models import ScrappedData
from asgiref.sync import sync_to_async


class MindbodySpider(scrapy.Spider):
    name = 'mindbodyonline'
    allowed_domains = ['mindbodyonline.com']

   

    def parse_locations(self, response):
        try:
            xml_content = response.body
        except Exception as err:
            print("xml content not found")
        root = etree.fromstring(xml_content)
        nsmap = root.nsmap
        nsmap['ns'] = nsmap.pop(None)
        item = APIItem()
        for url in root.xpath('//ns:url/ns:loc/text()', namespaces=nsmap):

            url_ = "https://prod-mkt-gateway.mindbody.io/v1/search/locations"
            location = url.split('/')[-1].strip().replace('\n', '')
            
            if len(location) > 2:
                payload = json.dumps({
                "sort": "",
                "page": {
                    "size": 1
                },
                "filter": {
                    "radius": 0,
                    "locationSlugs": [location]
                }
                })
                headers = {
                'Content-Type': 'application/json',
                'Cookie': '__cf_bm=eqo0_OXEeXogdNReThHcDerAZ5BqZDZWn9sf.mt7uD4-1710837347-1.0.1.1-ioSKKzmcmNHMOSl_HdwHuYUysSYwGiZCffIoCH1utX0lNtt8bp3oOd6TYFgs1q4wffArasNl.uTyFSdczY1vZg'
                }
                try:
                    response = requests.request("POST", url_, headers=headers, data=payload)
                    print(response.json())
                except Exception as error:
                    print(error)
                item['name'] = f'mindbodyonline/locations/{location}'
                item['response'] = response.json()
                
                yield item

    def parse_instructors(self, response):
        try:
            xml_content = response.body
        except Exception as err:
            print("xml content not found")
        root = etree.fromstring(xml_content)
        nsmap = root.nsmap
        nsmap['ns'] = nsmap.pop(None)
        item = APIItem()
        for url in root.xpath('//ns:url/ns:loc/text()', namespaces=nsmap):

            url_ = "https://prod-mkt-gateway.mindbody.io/v1/search/instructors"
            location = url.split('/')[-1].strip().replace('\n', '')
            if len(location) > 2:
                payload = json.dumps({
                "filter": {
                    "locationSlugs": [location]
                }
                })
                headers = {
                'Content-Type': 'application/json',
                'Cookie': '__cf_bm=eqo0_OXEeXogdNReThHcDerAZ5BqZDZWn9sf.mt7uD4-1710837347-1.0.1.1-ioSKKzmcmNHMOSl_HdwHuYUysSYwGiZCffIoCH1utX0lNtt8bp3oOd6TYFgs1q4wffArasNl.uTyFSdczY1vZg'
                }
                try:
                    response = requests.request("POST", url_, headers=headers, data=payload)
                    print(response.json())
                except Exception as error:
                    print(error)
                item['name'] = f'mindbodyonline/instructors/{location}'
                item['response'] = response.json()
                yield item
    

    def parse_availability(self, response):

        try:
            xml_content = response.body
        except Exception as err:
            print("xml content not found")
        root = etree.fromstring(xml_content)
        nsmap = root.nsmap
        nsmap['ns'] = nsmap.pop(None)
        item = APIItem()
        for url in root.xpath('//ns:url/ns:loc/text()', namespaces=nsmap):
            location = url.split('/')[-1].strip().replace('\n', '')
            url_ = f"https://prod-mkt-gateway.mindbody.io/v1/availability/location?filter.location_slug={location}&filter.timezone=America%2FLos_Angeles&filter.start_time_from=2024-03-19T11%3A04%3A18.927Z&filter.start_time_to=2024-04-09T06%3A59%3A59.999Z"
            if len(location) > 2:
                params = json.dumps({
                "filter": {
                    "locationSlugs": [location]
                }
                })
                headers = {
                'Content-Type': 'application/json',
                'Cookie': '__cf_bm=eqo0_OXEeXogdNReThHcDerAZ5BqZDZWn9sf.mt7uD4-1710837347-1.0.1.1-ioSKKzmcmNHMOSl_HdwHuYUysSYwGiZCffIoCH1utX0lNtt8bp3oOd6TYFgs1q4wffArasNl.uTyFSdczY1vZg'
                }
                try:
                    response = requests.request("GET", url_, headers=headers, params=params)
                    print(response.json())
                except Exception as error:
                    print(error)
                item['name'] = f'mindbodyonline/availability/{location}'
                item['response'] = response.json()
                yield item



        
    def start_requests(self):
    
        # Define the directory containing XML files
        xml_directory = settings.BASE_DIR/'sitemaps'

        # Fetch all XML files from the directory
        xml_files = [f for f in os.listdir(xml_directory) if f.endswith('.xml')]

        # Construct start_urls
        start_urls = [f'file://{xml_directory}/{filename}' for filename in xml_files]

        for url in start_urls:
            yield scrapy.Request(url, callback=self.parse_instructors, dont_filter=True)
            yield scrapy.Request(url, callback=self.parse_availability, dont_filter=True)
            yield scrapy.Request(url, callback=self.parse_locations, dont_filter=True)