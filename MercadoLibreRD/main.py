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

def get_car_url(key, value):
    brand_specific_urls = get_array_of_url(key, value)

    for specific_page in brand_specific_urls:
        response = requests.get(specific_page)
        car_page = response.text
        soup = BeautifulSoup(car_page, "html.parser")

        validator = soup.find("svg", class_="ui-search-icon ui-search-icon--not-found ui-search-rescue__icon")
        
        if validator != None:
            break

        urls = soup.find("section", class_="ui-search-results ui-search-results--without-disclaimer").find_all("li", class_="ui-search-layout__item")

        for url in urls:
            car_url = url.find("a", class_="ui-search-result__content ui-search-link").get("href")
            get_car_information(car_url)

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
            self.collection = db['Cars']

    def addCar(self, vehicleObject):
        self.collection.insert_one(vehicleObject)

year_url_and_count = get_year_url(soup)

for key in year_url_and_count:
    get_car_url(key, year_url_and_count[key])