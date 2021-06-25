import pymongo
import dns
import re
import pprint
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

options = Options()
# options.add_argument('--headless')
# options.add_argument('--disable-gpu')
DRIVER_PATH = './chromedriver'


driver = webdriver.Chrome(executable_path=DRIVER_PATH,options=options)

dbName = 'vin-plus'
dbConnectionString = "YOUR_DATA_BASE"
connection = pymongo.MongoClient(dbConnectionString)
db = connection[dbName]
collection = db['first-take']

redirects = list()
carUrls = list()

VIN_PLUS_URL = "http://www.vinplus.mx/index.php"

def testScraper():
    vinNumbers = ["LSGHD52H4LD039408","ASGHD52H4LD039408"]
    for vin in vinNumbers:
        driver.get(VIN_PLUS_URL)

        inputBox = driver.find_element_by_css_selector("#subheader > table > tbody > tr:nth-child(2) > td:nth-child(1) > form > input.vin")
        inputBox.send_keys(vin)
        inputBox.send_keys(Keys.ENTER)

        driver.implicitly_wait(10)

        dropDown = getDropDownElement(driver)

        if(dropDown!=None):
            print("MULTI OPTION PAGE")
            dropDown.click()

            driver.implicitly_wait(10)

            options:list = getOptions(driver.page_source)

            for option in options:
                stolenData:dict = stealCarData(driver.page_source, option)
                collection.insert_one(stolenData)
        else:
            print("SINGLE OPTION PAGE")
            stolenData:dict = stealSinglePageCarData(driver.page_source)
            collection.insert_one(stolenData)
        

    return None

def getDropDownElement(driver):
    try:
        dropDown = driver.find_element_by_css_selector("#selectVersionesWService")
        return dropDown
    except:
        return None

def getOptions(page:str):
    parsed_page = BeautifulSoup(page,"html.parser")
    raw_options = parsed_page.select("#selectVersionesWService")[0].find_all("option")

    ret: list = [int(option["value"]) for option in raw_options if option["value"]!=""]

    return ret

def stealCarData(page: str, option:int):
    parsed_page = BeautifulSoup(page,"html.parser")

    infoFields:list = parsed_page.select(f"#version_c{option}")[0].find_all("div", {"class": "col-xs-6"})

    return extractCarData(infoFields)

def stealSinglePageCarData(page: str):
    parsed_page = BeautifulSoup(page,"html.parser")

    infoFields:list = parsed_page.select("#table1")[0].find_all("div", {"class": "col-xs-6"})

    return extractCarData(infoFields)

def extractCarData(dataFields: list):

    carData: dict = {}
    dataLen = len(dataFields)
    index = 0
    while(index != dataLen):
        label = str(dataFields[index].text).strip()
        value = str(dataFields[index+1].text).strip()
        carData[label] = value
        index+=2
    
    pprint.pprint(carData)
    return carData

print("STARTING SCRAPER...")
testScraper()
driver.quit()
print("OK")
