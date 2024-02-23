from scrapy.spiders import CrawlSpider
from scrapy.http import Response, Request
from typing import Iterable, Any

class WebCrawler(CrawlSpider):
    name = "webcrawler"
    allowed_domains = [""]
    base_url = ""
    start_urls = [""]

    def start_requests(self) -> Iterable[Request]:
        return super().start_requests()

    def parse(self, response: Response, **kwargs: Any) -> Any:
        return super().parse(response, **kwargs)