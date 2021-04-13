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

#Fields
fields = { "year":"Año", "fuelType": "Tipo de combustible", "transmission": "Transmisión", "bodyStyle": "Tipo de carrocería",  "doors":"Puertas",  "engine": "Motor",  "mileage": "Kilómetros"}

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
        response = requests.get(specific_page)
        car_page = response.text
        soup = BeautifulSoup(car_page, "html.parser")
        get_car_information(soup)

def price_section(soup):
    price_section = soup.find("span", class_="price-tag-fraction")
    price = int(price_section.text.replace(",",""))
    return price

# extract data on data_sheet
def data_sheet(soup):
    data = {}
    columns = soup.find("tbody", class_="andes-table__body").find_all("tr")

    for row in columns:
        key = row.find("th").text
        value = row.find("td").text
        data[key] = value
    
    return data

# transform and get model
def get_model(dict, title, brand):
  model = title.replace(brand, "")
  for key in dict:
      if key == "Transmisión" or key == "Puertas":
          continue
      model = model.replace(dict[key], "")
  return model

def get_car_information(soup):
    picture_section = soup.find("img", class_="ui-pdp-image ui-pdp-gallery__figure__image")

    price = price_section(soup)
    title = picture_section.get("alt")
    brand = title.split(" ")[0]
    mainPicture = picture_section.get("data-zoom")
    
    data_sheet_table = data_sheet(soup)
    
    model = get_model(data_sheet_table, title, brand)

    vehicle = {
       "title":title, 
       "brand": brand,
       "model": model,
       "price": price, 
       "mainPicture": mainPicture,
       "year": data_sheet_table[fields["year"]],
       "fuelType": data_sheet_table[fields["fuelType"]],
       "bodyStyle": data_sheet_table[fields["bodyStyle"]],
       "transmission": data_sheet_table[fields["transmission"]],
       "engine": data_sheet_table[fields["engine"]],
       "doors": data_sheet_table[fields["doors"]],
       "mileage": data_sheet_table[fields["mileage"]],
    }
    
    print(vehicle)
    return vehicle

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

# brand_url_and_count = get_brand_url(soup)

# for key in brand_url_and_count:
#     get_car_url(key, brand_url_and_count[key])

response = requests.get("https://auto.mercadolibre.com.mx/MLM-891858876-mazda-cx-3-20-i-grand-touring-at-2016-_JM#position=47&type=item&tracking_id=bde0cb13-a342-4928-8705-6554ade7aa0f")

mercadoLibre = response.text

soup = BeautifulSoup(mercadoLibre, "html.parser")

get_car_information(soup)