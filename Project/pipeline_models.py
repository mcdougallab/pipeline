from pymongo import MongoClient
from bson.objectid import ObjectId
from django.db import models
import datetime
from . import settings
import json

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


def paper_by_id(paper_id):
    return collection.find_one({"_id": ObjectId(paper_id)})


def papers_by_status(status):
    return collection.find({"status": status})


def update(paper_id, username, **kwargs):
    new_values = {item: value for item, value in kwargs.items() if value is not None}
    if new_values:
        collection.update_many({"_id": ObjectId(paper_id)}, {"$set": new_values})
        now = datetime.datetime.now().isoformat()
        collection.update_many(
            {"_id": ObjectId(paper_id)},
            {"$push": {"log": {"username": username, "time": now, "data": new_values}}},
        )


def update_userdata(paper_id, userdata):
    logfile = settings.app_settings["userentry"].get("logfile")
    if logfile:
        with open(logfile, "a") as f:
            f.write(
                json.dumps(
                    {
                        "paperid": paper_id,
                        "time": datetime.datetime.now().isoformat(),
                        "userdata": json.dumps(userdata),
                    }
                )
                + "\n"
            )
    collection.update_many(
        {"_id": ObjectId(paper_id)}, {"$set": {"userdata": userdata}}
    )


def get_userdata(paper_id):
    return paper_by_id(paper_id).get("userdata", {})


def query(pattern):
    if "_id" in pattern:
        pattern["_id"] = ObjectId(pattern["_id"])
    return collection.find(pattern)
