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
fields = { "year":"Año", "fuelType": "Tipo de combustible", "transmission": "Transmisión", "bodyStyle": "Tipo de carrocería",  "doors":"Puertas",  "engine": "Motor",  "mileage": "Kilómetros", "color": "Color"}

# Get all the brand and find your url
def get_brand_url(soup):
    brand_href = {}
    brand_div = soup.find(class_="ui-search-search-modal-grid-columns").find_all("a", class_="ui-search-search-modal-filter ui-search-link")
    for brand in brand_div:
        key = brand.get("href")
        value_tmp = brand.find("span", class_="ui-search-search-modal-filter-match-count").text
        value = int(value_tmp.replace("(","").replace(")","").replace(",",""))

        url = convert_url(key)

        if value > limit_car_per_brand:
            value = limit_car_per_brand
        brand_href[url] = value

    return brand_href

def price_section(soup):
    price_section = soup.find("span", class_="price-tag-fraction")

    if price_section == None:
        return None

    price = int(price_section.text.replace(",",""))
    return price

# extract data on data_sheet
def data_sheet(soup):
    data = {}
    try: 
        columns = soup.find("tbody", class_="andes-table__body").find_all("tr")
    except: 
        return data

    for row in columns:
        key = row.find("th").text
        value = row.find("td").text
        print(key, value)
        data[key] = value
    
    return data

# WARNING comming soon
def get_model(dict, title, brand):
  model = title.replace(brand, "")
  print(model)
  for key in dict:
      if key == "Transmisión" or key == "Puertas":
          continue
      model = model.replace(dict[key], "")
  try:
      return model.split()[0]
  except: 
      return model 

def get_car_information(url):
    response = requests.get(url)
    vehicle_detail_page = response.text
    soup = BeautifulSoup(vehicle_detail_page, "html.parser")

    picture_section = soup.find("img", class_="ui-pdp-image ui-pdp-gallery__figure__image")

    price = price_section(soup)

    if picture_section == None:
        return

    title = picture_section.get("alt")

    if title == None:
        return

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
           

        
#Vehicle data manager
class VehicleDataManager():
    def __init__(self): 
            self.connection = pymongo.MongoClient(
                dbConnectionString
            )

            db = self.connection[dbName]
            self.collection = db['Vehicles']

    def addCar(self, vehicleObject):
        self.collection.insert_one(vehicleObject)

brand_url_and_count = get_brand_url(soup)

for key in brand_url_and_count:
    get_car_url(key, brand_url_and_count[key])
