import datetime
import json

from bson.objectid import ObjectId
from pymongo import MongoClient

from . import settings

mongodb = MongoClient()
db = mongodb[settings.app_settings["db_name"]]
db.authenticate(
    settings.app_settings["mongodb_user"], settings.app_settings["mongodb_pw"]
)

collection = getattr(db, settings.app_settings["collection_name"])


fieldnames = set()
for item in collection.find():
    fieldnames = fieldnames.union(item.get("field_order", []))

if settings.app_settings["browse_fields"] is None:
    settings.app_settings["browse_fields"] = list(fieldnames)

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
    inp = ""
    if fieldvalue == 'NaN':
        fieldvalue = '{ "$eq": NaN }'
        inp = "{\"" + fieldname + "\" : " + fieldvalue + "}"
    else:
        inp =  "{\"" + fieldname + "\" : \"" + fieldvalue + "\"}"
    patt = json.loads(inp)
    return list(collection.find(patt))
#return list(collection.find({fieldname: fieldvalue}))
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

def update_userdata(paper_id, userdata, new_status="user-submitted"):
    if paper_id != "new":
        collection.update_many(
            {"_id": ObjectId(paper_id)},
            {"$set": {"userdata": userdata, "status": new_status}},
        )
    else:
        result = collection.insert_one({"userdata": userdata})
        paper_id = str(result.inserted_id)
    userdataexists = collection.find(
        {"_id": ObjectId(paper_id), "userdata": {"$exists": True}}
    )
    if userdataexists.count() > 0:
        collection.find_one_and_update(
            {"_id": ObjectId(paper_id)},
            {"$currentDate": {"change_date": True}},
            upsert=True,
        )
    else:
        collection.find_one_and_update(
            {"_id": ObjectId(paper_id)},
            {"$currentDate": {"init_date": True}},
            upsert=True,
        )
    logfile = settings.app_settings["userentry"].get("logfile")
    if logfile:
        with open(logfile, "a") as f:
            f.write(
                json.dumps(
                    {
                        "paperid": paper_id,
                        "time": datetime.datetime.now().isoformat(),
                        "userdata": userdata,
                    }
                )
                + "\n"
            )


def get_userdata(paper_id, private_user):
    result = paper_by_id(paper_id).get("userdata", {})
    if not private_user:
        for field_val in settings.app_settings.get("private_data_fields", []):
            result["global_fields"].pop(field_val)
    return result

def query(pattern):
    if "_id" in pattern:
        pattern["_id"] = ObjectId(pattern["_id"])
    return collection.find(pattern)

def getdocsforuserdata():
    my_query = []
    for field_data in settings.app_settings["userentry"].get("fields", []):
        my_field_name = field_data["field"]
        my_query.append({f"{my_field_name}": {"$exists": True, "$ne": ""}})
    my_query = {"$or": my_query}
    my_query = {"$elemMatch": my_query}
    my_query = {"userdata.local_data": my_query}
    res = collection.find(my_query)
    results = []
    for item in res:
        item["_id"] = str(item["_id"])
        results.append(item)
    return results
