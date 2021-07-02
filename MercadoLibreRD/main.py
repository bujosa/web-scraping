from bs4 import BeautifulSoup
import requests
import pymongo
import dns
import math

# Database Name and db connection string to mongo atlas
dbName = 'MercadoLibreRD'
dbConnectionString = "mongodb+srv://scraper-admin:6PoJcLydol0XuLdX@freecluster.jg51j.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

# Request to mercado mercado libre mx
response = requests.get("https://vehiculos.mercadolibre.com.do/_FiltersAvailableSidebar?filter=VEHICLE_YEAR")

mercadoLibre = response.text

soup = BeautifulSoup(mercadoLibre, "html.parser")

# Constants variables
max_vehicle_per_page = 48
limit_car_per_year = 1969

#Fields
fields = { "year":"Año", "fuelType": "Tipo de combustible", "transmission": "Transmisión", "bodyStyle": "Tipo de carrocería",  "doors":"Puertas",  "engine": "Motor",  "mileage": "Kilómetros", "color": "Color"}

def get_year_url(soup):
    year_href = {}
    year_div = soup.find(class_="ui-search-search-modal-grid-columns").find_all("a", class_="ui-search-search-modal-filter ui-search-link")
    for year in year_div:
        key = year.get("href")
        value_tmp = year.find("span", class_="ui-search-search-modal-filter-match-count").text
        value = int(value_tmp.replace("(","").replace(")","").replace(",",""))

        url = convert_url(key)

        if value > limit_car_per_year:
            value = limit_car_per_year
        year_href_href[url] = value

    return year_href

def convert_url(url):
    result = url.split("?")
    return result[0]
#Vehicle data manager
class VehicleDataManager():
    def __init__(self): 
            self.connection = pymongo.MongoClient(
                dbConnectionString
            )

            db = self.connection[dbName]
            self.collection = db['Cars']

    def addCar(self, vehicleObject):
        self.collection.insert_one(vehicleObject)

year_url_and_count = get_year_url(soup)

for key in brand_url_and_count:
    get_car_url(key, brand_url_and_count[key])