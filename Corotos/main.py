from bs4 import BeautifulSoup
import requests
import pymongo
import dns
import math

# Database Name and db connection string to mongo atlas
dbName = 'Corotos'
dbConnectionString = "YOUR_DATA_BASE_URL"

# Request to Corotos
response = requests.get("https://www.corotos.com.do/listings/mercedes-benz-e350-2014-avantgarde-01f8xrswtx6m2rd4f73cdse8h1?page=4&q%5Bcategory_slug_eq%5D=veh%C3%ADculos&render_time=2021-07-04T21%3A52%3A57.402212-04%3A00")

corotos = response.text

soup = BeautifulSoup(corotos, "html.parser")

#Fields
fields = { "year":"Año", "brand": "Marca", "model": "Modelo", "fuelType": "Tipo de combustible", "transmission": "Transmisión", "bodyStyle": "Tipo de carrocería",  "doors":"Puertas",  "engine": "Motor",  "mileage": "Kilómetros", "color": "Color", "dólares": "USD" , "pesos": "DOP"}

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
