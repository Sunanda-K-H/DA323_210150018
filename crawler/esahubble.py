import scrapy
import re
import json
from hubble.items import HubbleItem


class EsahubbleSpider(scrapy.Spider):
    name = "esahubble"
    allowed_domains = ["esahubble.org"]
    start_urls = [
        "https://esahubble.org/images/archive/search/page/1/?minimum_size=0&ranking=0&facility=2&id=&release_id=&published_since_day=&published_since_month=&published_since_year=&published_until_day=&published_until_month=&published_until_year=&title=&subject_name=&description=&credit=&type=Observation&fov=0"
    ]

    def parse(self, response):
        script = response.xpath("//script[contains(., 'var images =')]/text()").get()
        pattern = re.compile(r"var images = (\[.*?\]);", re.DOTALL)
        match = pattern.search(script)

        if match:
            json_string = match.group(1)
            json_string = json_string.replace("'", '"')
            json_string = re.sub(r",\s*}", "}", json_string)
            json_string = re.sub(r",\s*]", "]", json_string)
            json_string = re.sub(r"([{,]\s*)(\w+)(\s*:)", r'\1"\2"\3', json_string)

            try:
                data = json.loads(json_string)
                for item_data in data:
                    item = HubbleItem()
                    item["image_urls"] = [item_data["src"]]
                    yield item
            except json.JSONDecodeError as e:
                self.logger.error("JSONDecodeError: %s", e)
                self.logger.error("JSONDecodeError at URL: %s", response.url)

            base_url = "https://esahubble.org/images/archive/search/page/"
            current_page_number = int(response.url.split("/page/")[1].split("/")[0])
            if current_page_number < 50:
                next_page_number = current_page_number + 1
                next_page_url = (
                    f"{base_url}{next_page_number}/?minimum_size=0&ranking=0&facility=2"
                )
                yield scrapy.Request(next_page_url, callback=self.parse)
