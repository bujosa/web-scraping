import scrapy
from scrapy.item import Item, Field
from scrapy.spiders import CrawlSpider
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor 
from scrapy.loader.processors import Join
from bs4 import BeautifulSoup


class Car(Item):
    price = Field()

class LibroAzul(CrawlSpider):
    name = "LibroAzul"
    allowed_domains = ["libroazul.com"]
    start_url = ['https://www.libroazul.com/detail.php?elem=']

    rules = (
        Rule(LinkExtractor(allow=r'/detail.php?elem=\d+', follow=True, callback='parse_items'))
    )

    def parse_items(self, response):
        item = scrapy.loader.ItemLoader(Car(), response)
        item.add_xpath('price', '//*[@id="content"]/div[2]/div/div[1]/div/div/div[1]/div[2]/text()')

        soup = BeautifulSoup(response.body)
        print(soup)