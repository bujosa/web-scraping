from bs4 import BeautifulSoup
import requests
import pymongo
import math
from datetime import datetime
from datetime import timedelta

# Request to mercado mercado libre RD
response = requests.get("https://carros.mercadolibre.com.do/autos-camionetas/_FiltersAvailableSidebar?filter=VEHICLE_YEAR")

mercadoLibre = response.text

soup = BeautifulSoup(mercadoLibre, "html.parser")

# Constants variables
max_vehicle_per_page = 48
limit_car_per_year = 1969

#Fields
fields = { "year":"Año", "brand": "Marca", "model": "Modelo", "fuelType": "Tipo de combustible", "transmission": "Transmisión", "bodyStyle": "Tipo de carrocería",  "doors":"Puertas",  "engine": "Motor",  "mileage": "Kilómetros", "color": "Color", "dólares": "USD" , "pesos": "DOP"}

count = 0

def convert_url(url):
    result = url.split("?")
    return result[0]

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

def days_section(soup):
    title = soup.find("span", class_="ui-pdp-subtitle")

    if title == None:
        return None

    date = title.text.split("Publicado hace ")[1]
    keys = date.split(" ")

    if keys[1] == 'días' or keys[1] == 'día' :
          return int(keys[0])
    elif keys[1] == "año" or keys[1] == 'años' :
      return int(keys[0]) * 365
    else:  
      return int(keys[0]) * 30

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

    if picture_section == None:
        return
    
    pictures, len_pictures = get_gallery_pictures(soup)

    if len_pictures < 4:
        return

    replace_text = "Imagen 1 de " + str(len_pictures) + " de "
    
    title = picture_section.get("alt").replace(replace_text, "").replace("  ", " ")

    if title == None:
        return
    
    brand = title.split(" ")[0]

    price, currency = price_section(soup)

    if price == None:
        return

    days = days_section(soup)
    
    if days > 7:
        return

    sellerType = get_seller_type(soup)

    if sellerType != 'Particular':
        return

    data_sheet_table = data_sheet(soup)

    model = get_model(data_sheet_table, title, brand)

    if key_error(data_sheet_table, "brand") != None:
        brand = key_error(data_sheet_table, "brand")
     
    if key_error(data_sheet_table, "model") != None:
        model = key_error(data_sheet_table, "model")

    # vehicle brand and model validation
    if brand == None or model == None:
        return

    pictures = replace_pictures(pictures)

    vehicle = {
       "title":title, 
       "brand": brand,
       "model": model,
       "price": price*0.95, 
       "originalPrice": price,
       "currency": currency,
       "mainPicture": pictures[0],
       "pictures": pictures[1:],
       "year": key_error(data_sheet_table, "year"),
       "fuelType": key_error(data_sheet_table, "fuelType"),
       "bodyStyle": key_error(data_sheet_table, "bodyStyle"),
       "transmission": key_error(data_sheet_table, "transmission"),
       "engine": key_error(data_sheet_table, "engine"),
       "doors": key_error(data_sheet_table, "doors"),
       "mileage": key_error(data_sheet_table, "mileage"),
       "color": key_error(data_sheet_table, "color"),
       "vehicle_url": url,
       "country": "Republica Dominicana",
       "state": state_section(soup),
       "seller": get_seller(soup),
       "sellerType": sellerType,
       "createdAt": datetime.now().isoformat(),
       "postCreatedAt":  (datetime.now() - timedelta(days=days)).isoformat(),
    }

    global count
    count += 1
    print(count)
    print(url)

    VehicleDataManager().addCar(vehicle)

def get_car_url(key, value):
    year_specific_urls = get_array_of_url(key, value)

    for specific_page in year_specific_urls:
        response = requests.get(specific_page)
        car_page = response.text
        soup = BeautifulSoup(car_page, "html.parser")

        validator = soup.find("svg", class_="ui-search-icon ui-search-icon--not-found ui-search-rescue__icon")
        
        if validator != None:
            break

        urls = soup.find("section", class_="ui-search-results")

        if urls == None:
            break
        else:
            urls = urls.find_all("li", class_="ui-search-layout__item")

        for url in urls:
            car_url = url.find("a", class_="ui-search-result__content ui-search-link").get("href")
            get_car_information(car_url)

# This function is used to get pictures from the gallery and get the number of pictures
def get_gallery_pictures(soup):
    pictures = []
    try:
        gallery_pictures = soup.find("div", class_="ui-pdp-gallery__column").find_all("span", class_="ui-pdp-gallery__wrapper")
        for picture in gallery_pictures:
            pictures.append(picture.find("img", class_="ui-pdp-image").get("data-src").replace("R.jpg", "F.jpg").replace("O.jpg", "F.jpg"))
        
        if len(pictures) > 5:
            return pictures[0:4], len(pictures)
        return pictures, len(pictures)
    except:
        return [], len(pictures)

def get_key(key):
    return fields[key]

def get_seller(soup):
    try:
        seller = soup.find("h3", class_="ui-pdp-color--BLACK ui-pdp-size--LARGE ui-pdp-family--REGULAR").text
        return seller
    except:
        return ''

def get_seller_type(soup):
    try:
        sellerType = soup.find("p", class_="ui-pdp-color--GRAY ui-pdp-family--REGULAR ui-vip-profile-info__subtitle").text
        return sellerType
    except:
        return 'Particular'

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

def get_year_url(soup):
    year_href = {}

    try: 
        year_div = soup.find(class_="ui-search-search-modal-grid-columns").find_all("a", class_="ui-search-search-modal-filter ui-search-link")
    except:
        return year_href

    for year in year_div:
        key = year.get("href")
        
        value_tmp = year.find("span", class_="ui-search-search-modal-filter-match-count").text
        
        value = int(value_tmp.replace("(","").replace(")","").replace(",",""))

        url = convert_url(key)

        if value > limit_car_per_year:
            value = limit_car_per_year

        year_href[url] = value

    return year_href

# This function is used to get data from the data sheet
def key_error(data, key):
    try:
        if key == "year" or key == "mileage":
            return int(data[fields[key]].replace(" km",""))
        else:
            return data[fields[key]]
    except:
        return None
        
# This function is used to get the price of the car and the currency
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

# This function is used to get the state of the car
def state_section(soup):
    try: 
        seller_info = soup.findAll("div", class_="ui-seller-info__status-info")
        for seller_info_status in seller_info:
            title = seller_info_status.find("h3", class_="ui-seller-info__status-info__title ui-vip-seller-profile__title").text
            if title == "Ubicación del vehículo":
                return seller_info_status.find("p", class_="ui-seller-info__status-info__subtitle").text.split(" - ")[1]
    except:
        return ''

def remove_background_picture(url):
    try: 
        return response.text
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

def replace_pictures(pictures_to_replace):
    pictures = []
    for picture in pictures_to_replace:
        picture_with_background_removed = remove_background_picture(picture)
        pictures.append(picture_with_background_removed)

    return pictures

#Vehicle data manager class
class VehicleDataManager():
    def __init__(self): 
            self.connection = pymongo.MongoClient("localhost:27017")
            db = self.connection["UPLOAD_PICTURE_TEST"]
            self.collection = db['2_Diciembre_2021']

    def addCar(self, vehicleObject):
        self.collection.insert_one(vehicleObject)

year_url_and_count = get_year_url(soup)

for key in year_url_and_count:
    get_car_url(key, year_url_and_count[key])

# get_car_information("https://carro.mercadolibre.com.do/MRD-504456942-honda-crv-americana-_JM#position=2&search_layout=grid&type=item&tracking_id=d980975f-41a5-45c3-8c35-1045c5af0526")