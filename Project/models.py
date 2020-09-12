from pymongo import MongoClient
from django.db import models
from . import settings

mongodb = MongoClient()
db = mongodb[settings.app_settings["db_name"]]
db.authenticate(
    settings.app_settings["mongodb_user"], settings.app_settings["mongodb_pw"]
)

collection = getattr(db, settings.app_settings["collection_name"])

fieldnames = set()
for item in collection.find():
    fieldnames = fieldnames.union(item["field_order"])

if settings.app_settings["browse_fields"] is None:
    settings.app_settings["browse_fields"] = list(models.fieldnames)

# handle missing status or notes fields
collection.update_many({"status": None}, {"$set": {"status": "triage"}})
collection.update_many({"notes": None}, {"$set": {"notes": ""}})


def count_all_field_instances(field):
    return {
        item["_id"]: item["count"]
        for item in collection.aggregate(
            [
                {"$unwind": f"${field}"},
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        )
    }


browse_counts = {
    field: count_all_field_instances(field)
    for field in settings.app_settings["browse_fields"]
}


def statistics():
    return {
        "counts": {
            status: collection.count_documents({"status": status})
            for status in collection.distinct("status")
        }
    }


def get_papers(fieldname, fieldvalue):
    return list(collection.find({fieldname: fieldvalue}))
