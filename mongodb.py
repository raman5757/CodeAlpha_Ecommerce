from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["CodeAlpha_Ecommerce"]

users = db["users"]
products = db["products"]
cart = db["cart"]
orders = db["orders"]