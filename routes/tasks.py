from flask_restful import Resource
from flask import request, current_app as app
from data_validations import validate_jwt_token
from Utils.db import get_tasks_collection
from bson import ObjectId
from routes.telegram import send_telegram_message

tasks = get_tasks_collection()
class Tasks(Resource):
    def get(self):
        auth_header = request.headers.get("Authorization")
        validated, userid_or_msg = validate_jwt_token(auth_header)
        if not validated:
            return userid_or_msg, 401
        user_id = userid_or_msg
        user_tasks = tasks.find({"user_id": user_id})
        return [{"_id": str(t["_id"]), **{k: v for k, v in t.items() if k != "_id"}} for t in user_tasks]

    def post(self):
        auth_header = request.headers.get("Authorization")
        validated, userid_or_msg = validate_jwt_token(auth_header)
        if not validated:
            return userid_or_msg, 401
        user_id = userid_or_msg

        data = request.get_json()
        title = data.get("title")
        description = data.get("description", "")

        if not title:
            return {"error": "Task title is required"}, 400

        task = {
            "title": title,
            "description": description,
            "user_id": user_id
        }
        result = tasks.insert_one(task)
        send_telegram_message(f"New task created: {title}\nTask Description: \n{description}")
        return {"message": "Task created", "task_id": str(result.inserted_id)}, 201

class SingleTask(Resource):
    def get(self, task_id):
        auth_header = request.headers.get("Authorization")
        validated, userid_or_msg = validate_jwt_token(auth_header)
        if not validated:
            return userid_or_msg, 401
        user_id = userid_or_msg

        task = tasks.find_one({"_id": ObjectId(task_id), "user_id": user_id})
        if not task:
            return {"error": "Task not found"}, 404
        return {"_id": str(task["_id"]), **{k: v for k, v in task.items() if k != "_id"}}

    def delete(self, task_id):
        auth_header = request.headers.get("Authorization")
        validated, userid_or_msg = validate_jwt_token(auth_header)
        if not validated:
            return userid_or_msg, 401
        user_id = userid_or_msg

        result = tasks.delete_one({"_id": ObjectId(task_id), "user_id": user_id})
        if result.deleted_count == 0:
            return {"error": "Task not found"}, 404
        return {"message": "Task deleted"}, 200

    def put(self, task_id):
        auth_header = request.headers.get("Authorization")
        validated, userid_or_msg = validate_jwt_token(auth_header)
        if not validated:
            return userid_or_msg, 401
        user_id = userid_or_msg

        data = request.get_json()
        title = data.get("title")
        description = data.get("description", "")

        if not title:
            return {"error": "Task title is required"}, 400

        result = tasks.update_one(
            {"_id": ObjectId(task_id), "user_id": user_id},
            {"$set": {"title": title, "description": description}}
        )
        if result.matched_count == 0:
            return {"error": "Task not found"}, 404
        return {"message": "Task updated"}, 200