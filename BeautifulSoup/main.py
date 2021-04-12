from bs4 import BeautifulSoup
import requests

# Request to azul
response = requests.get("")

azul = response.text
soup = BeautifulSoup(azul, "html.parser")
print(soup.title)
# print(soup.prettify())