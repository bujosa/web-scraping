import scrapy
import pymongo
import dns
import re
from scrapy.crawler import CrawlerProcess
import pprint
import os
from dotenv import load_dotenv

load_dotenv()

dbName = 'v5'
dbConnectionString = os.environ('MONGO_URL')


class SupercarrosListCrawlerSpider(scrapy.Spider):

    name = 'superCarrosListCrawler'

    start_urls = ['https://www.supercarros.com/']

    def parse(self, response):

        urls = response.css(
            '#header-nav > ul > li:nth-child(1) > ul > li > a::attr(href)').extract()

        with open('output.txt', 'w') as file:
            for url in urls:
                file.write(f'{url}\n')

        urls = response.css(
            '#header-nav > ul > li:nth-child(3) > ul > li > a::attr(href)').extract()

        with open('directorio.txt', 'w') as file:
            for url in urls:
                file.write(f'{url}\n')


class SuperCarrosUtils():

    def splitUrl(self, url):
        splittedUrl = list(re.split(r'[^\w]', url))

        temp = list()
        for splice in splittedUrl:
            if(splice != ''):
                temp.append(splice)

        splittedUrl = temp
        redirect = splittedUrl[4]
        return redirect


class VehiclesCrawlerSpider(scrapy.Spider):

    name = 'VehiclesCrawler'

    allowed_domains = ['www.supercarros.com']


    # start_urls = [
    #     'https://www.supercarros.com/']

    def __init__(self, **kwargs):
        """TODO sostituisci con self.getStartUrls()"""
        self.start_urls = self.getStartUrls()
        super().__init__(**kwargs)

    def getStartUrls(self):
        baseUrl = 'https://www.supercarros.com/buscar/?Brand='

        redirects = list()

        for i in range(0,2000):
            
            redirects.append(f"{baseUrl}{i}")
        # redirects = ["https://www.supercarros.com/carros/"]
        # with open('output.txt', 'r') as file:
        #     urls = file.readlines()
        #     for url in urls:
        #         # print(f'REDIRECT URL IS {url[:-1]}')
        #         redirects.append(baseUrl + url[:-1])
        #     # print(f'URL LIST IS {redirects}')

        return redirects

    def vehicleParse(self, response):
        vehicleDataManager().addCar(response)

    def parse(self, response):
        # gets all the vehicles urls in the page
        urls = response.css(
            '#bigsearch-results-inner-results > ul > li > div > a::attr(href)').extract()

        # Visits all the vehicles in a page
        for url in urls:
            yield response.follow(url, self.vehicleParse)

        # gets the list of the pagination bar
        nextPages = response.css(
            "#bigsearch-results-inner-lowerbar-pages > ul > li > a::attr(href)").extract()

        # gets the length of the pagination bar
        nextPagesLen = len(nextPages)

        # gets the url for the next page
        nextPage = nextPages[nextPagesLen - 1]

        # goes to the next page
        if(nextPage != None):
            yield response.follow(nextPage, self.parse)


class vehicleDataManager():

    def __init__(self):
        self.connection = pymongo.MongoClient(
            dbConnectionString
        )

        db = self.connection[dbName]
        self.collection = db['Vehicles']

    def addCar(self, vehiclePage):
        vehicleObject = self.vehicleDataExtractor(vehiclePage)
        self.collection.insert_one(vehicleObject)

    def vehicleDataExtractor(self, vehiclePage):
        vehicleManufacturer = SuperCarrosUtils().splitUrl(vehiclePage.url)

        try:
            vehicleDealerName = vehiclePage.css(
                '#detail-right > h3::text')[0].extract()
        except:
            print(f'ERROR IN PAGE {vehiclePage.url}\n')
            return None

        
        # print("DATA")
        vehicleOwnerData = vehiclePage.css('#detail-right > ul > li')

        child_elements = len(vehicleOwnerData)

        ownerData= dict()

        for i in range(0,child_elements):
            test_label = vehiclePage.css(f"#detail-right > ul > li:nth-child({i}) > label::text").extract()
            elementData = vehiclePage.css(f"#detail-right > ul > li:nth-child({i})::text").extract()
            secondaryElementData = vehiclePage.css(f"#detail-right > ul > li:nth-child({i}) > a::text").extract()
            completeData = vehiclePage.css(f"#detail-right > ul > li:nth-child({i})").extract()

            # print("SECTION DATA")
            # print(test_label)
            # print(elementData)
            # print(secondaryElementData)
            # print(completeData)

            if(len(test_label) != 0):

                labelKey = test_label[0]

                labelValue = ''

                if(len(elementData)!=0):
                    labelValue = elementData[0] if len(elementData)==1 else " ".join(elementData)
                elif(len(secondaryElementData)!=0):
                    labelValue = secondaryElementData[0] if len(secondaryElementData)==1 else " ".join(secondaryElementData)
                
                ownerData[labelKey] = labelValue

        # pprint.pprint(ownerData)

        vehicleDealerName = vehiclePage.css(
            '#detail-right > h3::text')[0].extract()
        vehicleData = vehiclePage.css('#detail-left')

        vehicleName = vehicleData.css("h1::text")[0].extract()

        # print(vehicleData.css(
        #     '#detail-ad-header > div'))

        vehicleInfoHeader : str = vehicleData.css(
            '#detail-ad-header > div')

        vehicleInsertionId = vehicleInfoHeader.css(
            ' b::text')[0].extract()[1:]
        
        # print(vehicleInfoHeader.extract()[0].split("."))

        detail = vehicleInfoHeader.extract()[0].split(".")

        vehicleViews = 0
        # print(detail)
        if(len(detail)>2):
            visits:str = detail[1].split()[-2]

            vehicleViews = visits

        vehicleSpecsDetail = vehicleData.css(
            '.detail-ad-info-specs-block table td::text').extract()
        vehicleSpecsLabels = vehicleData.css(
            '.detail-ad-info-specs-block table td label::text').extract()
        vehicleAccessories = vehicleData.css(
            '.detail-ad-info-specs-block ul li::text').extract()
        vehicleImages = vehicleData.css(
            '#detail-ad-info-photos > ul > li > a > img::attr(src)').extract()

        # creates a dictionary using the items in vehicleSpecLabels as Key
        # and the items in vehicleSpecDetail as value
        vehicleSpecs = dict(zip(vehicleSpecsLabels, vehicleSpecsDetail))

        if(len(vehicleAccessories) > 0):
            vehicleAccessories.pop()
        if(len(vehicleAccessories) > 0):
            vehicleAccessories.pop()

        vehicle = {
            "vehicleInsertionId": vehicleInsertionId,
            "vehicleName": vehicleName,
            "vehicleManufacturer": vehicleManufacturer,
            "vehicleDealerName": vehicleDealerName,
            "vehicleSpecs": vehicleSpecs,
            "vehicleAccessories": vehicleAccessories,
            "vehicleImages": vehicleImages,
            "vehicleViews": vehicleViews,
            "ownerData": ownerData
        }
        # print(f'VEHICLE IS {vehicle}')
        return vehicle

# #detail-right > ul
# #detail-right > ul > li:nth-child(1)


class DealerCrawlerSpider(scrapy.Spider):

    name = 'superCarrosDealerCrawler'

    start_urls = [
        'https://www.supercarros.com/Directorio/Dealers/?PagingPageSkip=0']

    def dealerParse(self, response):
        dealerDetail = response.css('#detail-right')
        DealerDataManager().addDealer(dealerDetail)

    def parse(self, response):

        urls = response.css(
            '#dealer-results > ul > li > div > a::attr(href)').extract()

        for url in urls:
            yield response.follow(url, self.dealerParse)

        nextPage = response.css(
            "#dealer-results > div.generic-results-bar-pages.centered > ul > li:nth-child(8) > a::attr(href)")[0].extract()

        # print(nextPage)
        if(nextPage != None):
            yield response.follow(nextPage, self.parse)


class DealerDataManager():

    def __init__(self):
        self.connection = pymongo.MongoClient(
            dbConnectionString
        )

        db = self.connection[dbName]
        self.collection = db['Dealers']

    def addDealer(self, dealer):
        dealerObject = self.dealerDataExtractor(dealer)
        self.collection.insert_one(dealerObject)

    def dealerDataExtractor(self, dealerDetail):

        if(len(dealerDetail.css("#detail-right h3::text")) != 0):
            dealerName = dealerDetail.css(
                "#detail-right h3::text")[0].extract()
            dealerData = dealerDetail.css("#detail-right li::text").extract()

            temp = list()

            for data in dealerData:
                # removes leading and trailing whitespaces
                data = data.strip()
                if(data != ""):
                    temp.append(data)

            dealerData = temp

            dealer = {
                "dealerName": dealerName,
                "dealerData": dealerData
            }

            return dealer


# class PlaceDataManager():

#     def __init__(self):
#         self.connection = pymongo.MongoClient(
#             dbConnectionString
#         )

#         db = self.connection[dbName]
#         self.collection = db['Places']

#     def addPlace(self, place):
#         placeObject = self.dealerDataExtractor(place)
#         self.collection.insert_one(placeObject)

#     def dealerDataExtractor(self, place):

#         placeName = place.css('#dirinfo-header > h1::text')[0].extract()

#         placeData = place.css(
#             "#dirinfo-info-specs > div:nth-child(1) > table > tr > td::text").extract()

#         placeDataLabel = place.css(
#             "#dirinfo-info-specs > div:nth-child(1) > table > tr > td > label::text").extract()

#         placeDataDetail = dict(zip(placeDataLabel, placeData))

#         place = {
#             'placeName': placeName,
#             'placeDataDetail': placeDataDetail
#         }

#         return place


# class PlacesCrawlerSpider(scrapy.Spider):

#     name = 'superCarrosPlaceCrawler'

#     allowed_domains = ['www.supercarros.com']
#     baseUrl = 'https://www.supercarros.com'

#     def __init__(self, **kwargs):
#         self.start_urls = self.getStartUrls()
#         super().__init__(**kwargs)

#     def getStartUrls(self):
#         redirects = []
#         with open('directorio.txt', 'r') as file:
#             urls = file.readlines()
#             flag = False
#             for url in urls:
#                 # print(f'REDIRECT URL IS {url[:-1]}')
#                 if(flag):
#                     redirects.append(self.baseUrl + url[:-1])
#                 flag = True
#             print(f'URL LIST IS {redirects}')

#         return redirects

#     def directorioParser(self, response):
#         placeDataDetail = response.css('#content')
#         PlaceDataManager().addPlace(placeDataDetail)

#     def parse(self, response):

#         urls = response.css(
#             "#dealer-results > ul > li > div > a::attr(href)").extract()

#         # print(urls)
#         for url in urls:
#             yield response.follow(url, self.directorioParser)

#         nextPages = response.css(
#             "#dealer-results > div.generic-results-bar-pages.centered > ul > li > a::attr(href)").extract()

#         # gets the length of the pagination bar
#         nextPagesLen = len(nextPages)

#         # gets the url for the next page
#         nextPage = nextPages[nextPagesLen - 1]

#         # goes to the next page
#         if(nextPage != None):
#             yield response.follow(nextPage, self.parse)


vehicleGetter = CrawlerProcess()
# vehicleGetter.crawl(SupercarrosListCrawlerSpider)
vehicleGetter.crawl(VehiclesCrawlerSpider)
# vehicleGetter.crawl(DealerCrawlerSpider)
# vehicleGetter.crawl(PlacesCrawlerSpider)
vehicleGetter.start()
