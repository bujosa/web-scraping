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
fields = { "year":"Año", "brand": "Marca", "model": "Modelo", "fuelType": "Tipo de combustible", "transmission": "Transmisión", "bodyStyle": "Tipo de carrocería",  "doors":"Puertas",  "engine": "Motor",  "mileage": "Kilómetros", "color": "Color", "dólares": "USD" , "pesos": "DOP"}

count = 0

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
        year_href[url] = value

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

        urls = soup.find("section", class_="ui-search-results").find_all("li", class_="ui-search-layout__item")

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

def price_section(soup):
    price_section = soup.find("span", class_="price-tag-text-sr-only")

    if price_section == None:
        return None
    
    keys = price_section.text.split(" ")
    
    price = int(keys[0])
    currency = get_key(keys[1])
    
    if price > 200 and price < 999:
        return price*1000, "DOP"

    if price < 2000: 
        return None, None

    if price < 100000 and currency == "DOP": 
        currency =  "USD"

    return price, currency

def days_section(soup):
    title = soup.find("span", class_="ui-pdp-subtitle")

    if title == None:
        return None

    date = title.text.split("Publicado hace ")[1]
    keys = date.split(" ")

    if keys[1] == 'días' :
      return int(keys[0])
    else:
      return int(keys[0]) * 30

def get_model(dict, title, brand):
  if title == None:
    return None

  model = title.replace(brand, "")

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

    price, currency = price_section(soup)

    if picture_section == None:
        return

    originalMainPicture = picture_section.get("data-zoom")

    title = picture_section.get("alt")

    if title == None:
        return

    brand = title.split(" ")[0]

    days = days_section(soup)

    if days > 60 :
      return

    data_sheet_table = data_sheet(soup)

    if data_sheet_table == {}:
        return
    
    model = get_model(data_sheet_table, title, brand)

    if price == None:
        return
   
    if key_error(data_sheet_table, "brand") != None:
        brand = key_error(data_sheet_table, "brand")
     
    if key_error(data_sheet_table, "model") != None:
        model = key_error(data_sheet_table, "model")

    vehicle = {
       "title":title, 
       "brand": brand,
       "model": model,
       "price": price, 
       "currency": currency,
       "age": days,
       "mainPicture": "https://curbo-assets.nyc3.cdn.digitaloceanspaces.com/Curbo%20proximamente.svg",
       "originalMainPicture": originalMainPicture,
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

    global count
    count += 1
    print(count)

    VehicleDataManager().addCar(vehicle)

def data_sheet(soup):
    data = {}
    try: 
        columns = soup.find("tbody", class_="andes-table__body").find_all("tr")
    except: 
        return data

    for row in columns:
        key = row.find("th").text
        value = row.find("td").text
        data[key] = value
    
    return data

def get_key(key):
    return fields[key]

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

