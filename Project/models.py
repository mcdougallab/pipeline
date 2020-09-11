from pymongo import MongoClient, ReturnDocument
from django.db import models
from . import settings

mongodb = MongoClient()
db = mongodb[settings.app_settings["db_name"]]
db.authenticate(
    settings.app_settings["mongodb_user"], settings.app_settings["mongodb_pw"]
)

collection = getattr(db, settings.app_settings["collection_name"])

# handle missing status or notes fields
collection.update_many({"status": None}, {"$set": {"status": "triage"}})
collection.update_many({"notes": None}, {"$set": {"notes": ""}})


def statistics():
    return {
        "counts": {
            status: collection.count_documents({"status": status})
            for status in collection.distinct("status")
        }
    }
