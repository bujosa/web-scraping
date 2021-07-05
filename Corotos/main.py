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