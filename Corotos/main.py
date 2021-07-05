from bs4 import BeautifulSoup
import requests

class Corotos:
    __fields = { "year":"Año", "brand": "Marca", "model": "Modelo",
    "fuelType": "Combustible", "transmission": "Transmisión",
    "bodyStyle": "Tipo",  "doors":"Cantidad de puertas",  "engine": "Motor/CC",
    "mileage": "Kilometraje", "colorExterior": "Color exterior",
    "colorInterior": "Color interior",
    "driveTrain": "Tracción",
    "US$": "USD" , "RD$": "DOP"}
     
    def __data_sheet(self, soup):
        data = {}
        try: 
            columns = soup.find("ul", class_="post__specs").find_all("li")
        except: 
            return data

        for row in columns:
            key = row.find("span", class_="specs__label").text
            value = row.find("span", class_="specs__value").text
            data[key] = value
        
        return data

    def __get_key(self, str):
        return self.__fields[str]

    def __get_price_and_currency(self, str):
        array = str.split(' ')
        currency = self.__fields[array[0]]
        price = int(array[1].replace(",", ""))
        return price, currency

    def __get_main_picture(self, soup):
        try:
            carousel = soup.find("div", class_="carousel-cell")
            return carousel.find("img").get("src")
        except:
            return None

    def __get_date(self, str):
        date = str.replace("Publicado: ", "").replace(" de", "")
        return date
    
    def __key_error(self, data, key):
        try:
            return data[self.__fields[key]]
        except:
            return None

    def __header_section(self, soup):
        header = dict()

        post_details = soup.find("div", class_="post__details")

        if post_details == None:
            return None

        post_price = post_details.find("h2", class_="post__price")

        post_title = post_details.find("h1", class_="post__title")

        post_date = post_details.find("p", class_="post__date")

        if post_price == None or post_title == None or post_date == None:
            return None

        header["title"] = post_title.text

        price, currency =  self.__get_price_and_currency(post_price.text)
        
        header["price"] = price
        header["currency"] = currency

        header["date"] =  self.__get_date(post_date.text)

        return header

    def get_car_information(self, url):
        response = requests.get(url)
        vehicle_detail_page = response.text
        soup = BeautifulSoup(vehicle_detail_page, "html.parser")

        originalMainPicture = self.__get_main_picture(soup)

        header = self.__header_section(soup)

        if header == None:
            return 

        data_sheet_table = self.__data_sheet(soup)

        if data_sheet_table == {}:
            return

        vehicle = {
            "title":header["title"], 
            "brand": self.__key_error(data_sheet_table, "brand"),
            "model": self.__key_error(data_sheet_table, "model"),
            "price": header["price"], 
            "currency": header["currency"],
            "date": header["date"],
            "mainPicture": "https://curbo-assets.nyc3.cdn.digitaloceanspaces.com/Curbo%20proximamente.svg",
            "originalMainPicture": originalMainPicture,
            "year": self.__key_error(data_sheet_table, "year"),
            "fuelType": self.__key_error(data_sheet_table, "fuelType"),
            "bodyStyle": self.__key_error(data_sheet_table, "bodyStyle"),
            "driveTrain": self.__key_error(data_sheet_table, "driveTrain"),
            "transmission": self.__key_error(data_sheet_table, "transmission"),
            "engine": self.__key_error(data_sheet_table, "engine"),
            "doors": self.__key_error(data_sheet_table, "doors"),
            "mileage": self.__key_error(data_sheet_table, "mileage"),
            "colorExterior": self.__key_error(data_sheet_table, "colorExterior"),
            "colorInterior": self.__key_error(data_sheet_table, "colorInterior"),
            "vehicle_url": url,
        }

        return vehicle

vehicle = Corotos()

print(vehicle.get_car_information("https://www.corotos.com.do/listings/chevrolet-camaro-ss-2016-01f9tmddfe71fk4xc9skbj7t62?page=1&q%5Bcategory_slug_eq%5D=veh%C3%ADculos&render_time=2021-07-05T02%3A11%3A08.918255-04%3A00"))