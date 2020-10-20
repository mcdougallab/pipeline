"""example of loading data from a CSV file into the pipeline"""

import pandas as pd
import pprint
from pymongo import MongoClient, ReturnDocument
import sys

try:
    import tqdm

    progress_bar = tqdm.tqdm
except:
    progress_bar = lambda x: x

# hacky way of loading settings from the project folder
old_path = list(sys.path)
sys.path = ["../Project"] + old_path
import settings

sys.path = old_path

mongodb = MongoClient()
db = mongodb[settings.app_settings["db_name"]]
db.authenticate(
    settings.app_settings["mongodb_user"], settings.app_settings["mongodb_pw"]
)

# throw away the old collection
db.drop_collection(settings.app_settings["collection_name"])

# and prepare to start building it again
collection = getattr(db, settings.app_settings["collection_name"])


def keep_rule(row):
    """returns True if we should keep the row (and move it into the database) else False"""
    return row.license in [
        "green-oa",
        "cc-by",
        "cc-by-nc",
        "cc0",
        "gold-oa",
        "medrxiv",
        "biorxiv",
        "arxiv",
    ]


def tags(row):
    """very simple example of populating a list of tags from an abstract"""
    abstract = f" {row.abstract.lower().replace('.', ' ').replace(',', ' ').replace(';', ' ')} "

    return [
        tag
        for tag, terms in options["tag_rules"].items()
        if any(f" {term} " in abstract for term in terms)
    ]


options = {
    "csvfile": "/home/bitnami/2020-10-19/metadata.csv",
    "keep_rule": lambda row: row.license
    in [
        "green-oa",
        "cc-by",
        "cc-by-nc",
        "cc0",
        "gold-oa",
        "medrxiv",
        "biorxiv",
        "arxiv",
    ],
    "title": "title",
    "url": "url",
    "fields": ["authors", "journal", "tags", "license", "abstract"],
    "derived_fields": {
        "authors": lambda row: [person.strip() for person in row.authors.split(";")],
        "tags": tags,
    },
    "tag_rules": {
        "brain": ["brain", "neurological", "neuron", "neurons"],
        "heart": ["heart", "cardiac"],
        "kindey": ["kidney"],
        "liver": ["liver"],
        "lung": ["lung", "pulmonary"],
        "artery": ["artery"],
        "skin": ["skin"],
        "bone": ["bone"],
        "upregulated": ["upregulated", "up-regulated"],
        "downregulated": ["downregulated", "down-regulated"],
        "rnaseq": ["rnaseq", "rna-seq"],
        "immune response": ["immune response"],
        "t-cell": ["t cell", "t cells", "t-cell", "t-cells"],
        "b-cell": ["b cell", "b cells", "b-cell", "b-cells"],
        "virus": ["virus", "viral"],
        "human": ["human", "humans", "patient", "patients"],
        "antibody": ["antibody", "antibodies"],
        "treatment": ["treatment", "medicine"],
        "mouse": ["mouse", "mice"],
        "macrophage": ["macrophage", "macrophages"],
        "protein": ["protein", "proteins"],
        "gene": ["gene", "genes", "genetic"],
    },
}


def parse(row):
    result = {
        "title": getattr(row, options["title"]),
        "url": getattr(row, options["url"]),
        "field_order": list(options["fields"]),
    }

    for field in options["fields"]:
        if field in options["derived_fields"]:
            value = options["derived_fields"][field](row)
        else:
            value = getattr(row, field)
        result[field] = value
    return result


data = pd.read_csv(options["csvfile"])
for row in progress_bar(data.itertuples()):
    # a better solution would be to not fail silently
    if options["keep_rule"](row):
        try:
            collection.insert_one(parse(row))
        except:
            pass

# setup the status indexing
db.collection.create_index([("status", 1)])

# setup the field indexing
for field in options["fields"]:
    db.collection.create_index([(field, 1)])
