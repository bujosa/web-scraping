from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import pymongo
import dns

dbName = 'VinPlus'
dbConnectionString = "YOUR_DATA_BASE_URI"
URL = "http://www.vinplus.mx/index.php"

s = requests.Session()

response = requests.get(URL)

mercadoLibre = response.text

soup = BeautifulSoup(mercadoLibre, "html.parser")

form = soup.find("form")

fields = form.findAll('input')

formdata = dict( (field.get('name'), field.get('value')) for field in fields)

formdata['Vin'] = u'LSGHD52H4LD039408'
formdata[None] = u'LSGHD52H4LD039408'

posturl = urljoin(URL, form['action'])

r = s.post(posturl, data=formdata)

soup = BeautifulSoup( r.text, "html.parser")

print(soup)

form = soup.find("form")


