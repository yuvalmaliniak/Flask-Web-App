from pymongo import MongoClient
import os
from flask import current_app as app

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["task_manager"]

def db_init():
    if "users" not in db.list_collection_names():
        db.create_collection("users")
    if "tasks" not in db.list_collection_names():
        db.create_collection("tasks")
    if "recommendations" not in db.list_collection_names():
        db.create_collection("recommendations")
    return db


def get_db():
    return db

def get_users_collection():
    return db["users"]

def get_tasks_collection():
    return db["tasks"]

def get_recommendations_collection():
    return db["recommendations"]