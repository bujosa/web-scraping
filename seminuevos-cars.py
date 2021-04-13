from bs4 import BeautifulSoup
import requests

base_url = "https://www.seminuevos.com"
response = requests.get(base_url + "/usados/-/autos")
soup = BeautifulSoup(response.content, 'html.parser')
# print(soup.prettify())
# cars = soup.find_all(id="featuredUsed")
# cars2 = cars.find_all(id="card-info")
# links = cars2.find_all('a')
# print(links)
# print(soup.title)

# cars_links = soup.find_all("a", class_="vehicle-href")


def get_cars_href(soup):
    cars_href = []
    cars_list = soup.find(id="featuredUsed")
    cars_details = cars_list.find_all("div", class_="card-info card-content")
    for link in cars_details:
        a = link.find_all("a", class_="vehicle-href")
        # a.title
        cars_href.append(a[0].get("href"))
        # print(a[0].get("title"))
    # print(cars_links)
    # print(len(cars_href))
    # print(cars_href)
    # print("\n\n\n\n\n\n")
    return cars_href


def get_car_summary(soup):
    car_summary = {}
    car_summary_div = soup.find(id="summary").find("div", class_="row m-t")
    car_summary_children_divs = car_summary_div.find_all("div")

    for car_detail in car_summary_children_divs:
        detail_key = car_detail.small.contents[0]
        detail_value = car_detail.contents[-1].strip()

        car_summary[detail_key] = detail_value
        # print(detail_key, detail_value)

    return car_summary


def get_car_technical_data(soup):
    car_technical_data = {}
    car_technical_data_divs = soup.find(
        id="technicalData").find_all("div", class_="col l4 m6 s6")

    for car_detail in car_technical_data_divs:
        detail_key = car_detail.p.small.contents[0]
        detail_value = car_detail.p.span.contents[0]

        car_technical_data[detail_key] = detail_value

    return car_technical_data


def get_car_equipment(soup):
    # car_equipment_list = soup.find(id="equipment")
    car_equipment_list = soup.find(
        "div", class_="vehicle-info-content").find("section", class_="row m-t list-data tags")

    print(car_equipment_list)


cars_href = get_cars_href(soup)
response = requests.get(base_url + cars_href[0])
soup = BeautifulSoup(response.content, 'html.parser')

# print(get_car_summary(soup))
get_car_equipment(soup)

# print(get_car_technical_data(soup))
