import config

from pymongo import MongoClient

MONGODB_USERNAME = config.MONGODB_USERNAME
MONGODB_PASSWORD = config.MONGODB_PASSWORD

client = MongoClient("mongodb+srv://" + MONGODB_USERNAME + ":" + MONGODB_PASSWORD + "@cluster0.wdsdfvv.mongodb.net/?retryWrites=true&w=majority")
db = client.senior_project
userCollection = db.users

exampleDict = {
    "email": "example@gmail.com",
    "password": "xxxxxx",
    "api": {
        "bitkub": {
            "API_KEY": "xxxxxx",
            "API_SECRET": "xxxxxx"
        },
        "binance": {
            "API_KEY": "xxxxxx",
            "API_SECRET": "xxxxxx"
        }
    }
}

#print(db.list_collection_names())
#print(exampleDict)

#---insert_one---
# result = userCollection.insert_one(exampleDict)
# print(result.inserted_id)

#---find_one---
user = userCollection.find_one({"email": "example@gmail.com"})
del user["_id"]
print(user)

#---update_one---
# updatedAPI = {
#     "api": {
#         "bitkub": {
#             "API_KEY": "xxx",
#             "API_SECRET": "xxxxxx"
#         },
#         "binance": {
#             "API_KEY": "xxxxxx",
#             "API_SECRET": "xxxxxx"
#         }
#     }
# }
#---Use find_one together with update_one---
# user = userCollection.find_one({"email": "example@gmail.com"})
# updatedAPI = dict()
# updatedAPI["api"] = user["api"]
# updatedAPI["api"]["bitkub"]["API_KEY"] = "xxx"
# result = userCollection.update_one({"email": "example@gmail.com"}, {"$set": updatedAPI})
# print(result)

#---delete_one---
#result = userCollection.delete_one({"email": "example@gmail.com"})
#print(result)