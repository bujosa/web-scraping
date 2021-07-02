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
    year_specific_urls = get_array_of_url(key, value)

    for specific_page in year_specific_urls:
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
    year_url = []
    last_part = "_Desde_"
    year_url.append(url)
    count = value/max_vehicle_per_page

    if count < 1 or value == max_vehicle_per_page: 
        return year_url
    else:
        count = math.floor(count)
        for x in range(count+1):
            number = str(x*max_vehicle_per_page + 1)
            last_part_tmp = url+last_part+number
            year_url.append(last_part_tmp)
    
    return year_url

def get_car_information(url):
    response = requests.get(url)
    vehicle_detail_page = response.text
    soup = BeautifulSoup(vehicle_detail_page, "html.parser")

    picture_section = soup.find("img", class_="ui-pdp-image ui-pdp-gallery__figure__image")

    # price = price_section(soup)

    if picture_section == None:
        return

    title = picture_section.get("alt")

    if title == None:
        return

    brand = title.split(" ")[0]

    mainPicture = picture_section.get("data-zoom")
    
    # data_sheet_table = data_sheet(soup)
    
    # model = get_model(data_sheet_table, title, brand)

    vehicle = {
       "title":title, 
       "brand": brand,
       "model": model,
       "price": price, 
       "mainPicture": mainPicture,
       "year": key_error(data_sheet_table, "year"),
       "fuelType": key_error(data_sheet_table, "fuelType"),
       "bodyStyle": key_error(data_sheet_table, "bodyStyle"),
       "transmission": key_error(data_sheet_table, "transmission"),
       "engine": key_error(data_sheet_table, "engine"),
       "doors": key_error(data_sheet_table, "doors"),
       "mileage": key_error(data_sheet_table, "mileage"),
       "color": key_error(data_sheet_table, "color"),
       "vehicle_url": url,
    }
    
    VehicleDataManager().addCar(vehicle)

def key_error(data, key):
    try:
        if key == "year" or key == "mileage":
            return int(data[fields[key]].replace(" km",""))
        else:
            return data[fields[key]]
    except:
        return None
        
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