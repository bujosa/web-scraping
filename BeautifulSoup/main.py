from bs4 import BeautifulSoup
import requests
import pymongo
import dns
import math

# Database Name and db connection string to mongo atlas
dbName = 'MercadoLibreMX'
dbConnectionString = "mongodb+srv://eljevas:RBuQdrNXtDaJggE0@scrapercluster.hhqge.mongodb.net/<dbname>?retryWrites=true&w=majority"

# Request to mercado mercado libre mx
response = requests.get("https://autos.mercadolibre.com.mx/_FiltersAvailableSidebar?filter=BRAND")

mercadoLibre = response.text

soup = BeautifulSoup(mercadoLibre, "html.parser")

max_vehicle_per_page = 48
limit_car_per_brand = 1969

# Get all the brand and find your url
def get_brand_url(soup):
    brand_href = {}
    brand_div = soup.find(class_="ui-search-search-modal-grid-columns").find_all("a", class_="ui-search-search-modal-filter ui-search-link")
    for brand in brand_div:
        key = brand.get("href")
        value_tmp = brand.find("span", class_="ui-search-search-modal-filter-match-count").text
        value = int(value_tmp.replace("(","").replace(")","").replace(",",""))
        if value > limit_car_per_brand:
            value = limit_car_per_brand
        brand_href[key] = value

    return brand_href

def get_car_url(key, value):
    url = convert_url(key)
    brand_specific_urls = get_array_of_url(url, value)
    for specific_page in brand_specific_urls:
        print(specific_page)
    return None

def get_car_information(soup):
    return None

# Transform url
def convert_url(url):
    result = url.split("?")
    return result[0]

def get_array_of_url(url, value):
    brand_url = []
    last_part = "_Desde_"
    brand_url.append(url)
    count = value/max_vehicle_per_page

    if count < 1 or value == max_vehicle_per_page: 
        return brand_url
    else:
        count = math.floor(count)
        for x in range(count+1):
            number = str(x*max_vehicle_per_page + 1)
            last_part_tmp = url+last_part+number
            brand_url.append(last_part_tmp)
    
    return brand_url

#Vehicle data manager
class VehicleDataManager():
    def __init__(self): 
            self.connection = pymongo.MongoClient(
                dbConnectionString
            )

            db = self.connection[dbName]
            self.collection = db['Vehicles']

    def addCar(self, vehiclePage):
        vehicleObject = self.vehicleDataExtractor(vehiclePage)
        self.collection.insert_one(vehicleObject)

brand_url_and_count = get_brand_url(soup)

for key in brand_url_and_count:
    get_car_url(key, brand_url_and_count[key])