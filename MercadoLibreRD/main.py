from bs4 import BeautifulSoup
import requests
import pymongo
import dns
import math

# Database Name and db connection string to mongo atlas
dbName = 'MercadoLibreRD'
dbConnectionString = "mongodb+srv://scraper-admin:6PoJcLydol0XuLdX@freecluster.jg51j.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

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
