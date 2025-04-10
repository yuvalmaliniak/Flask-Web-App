from flask import Flask,jsonify,request,render_template
from pymongo import MongoClient
from flask_restful import Resource, Api, reqparse
import hashlib, os
from bson import ObjectId
from data_validations import validate_register_data, validate_jwt_token, decode_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
import jwt
import datetime
import openai
from flask_cors import CORS

openai.api_key = os.getenv("OPENAI_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

def generate_token(user_id):
    payload = {
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

app = Flask(__name__)
api = Api(app)

if not os.path.exists("logs"):
    os.mkdir("logs")

handler = RotatingFileHandler('logs/app.log', maxBytes=1000000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

connection_string = "mongodb://localhost:27017/"
client = MongoClient(connection_string)

db = client['task_manager']
users = db['users']
tasks = db['tasks']
recommendations = db['recommendations']
# To change:
#CORS(app,origins=["http://localhost:3000"], supports_credentials=True)
@app.route('/')
def home():
    return render_template('login.html')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class Register(Resource):
    def post(self):
        if not request.is_json or request.headers.get('Content-Type') != 'application/json':
            error_msg = "Unsupported media type"
            app.logger.error(error_msg)
            return {"error": error_msg}, 415
        data = request.get_json()
        valid_creds , msg = validate_register_data(data)
        if not valid_creds:
            return {"error": msg}, 400

        username = data.get("username")
        password = hash_password(data.get("password"))
        if users.find_one({"username": username}):
            app.logger.info("User already exists")
            return {"message": "User already exists"}, 400
        result = users.insert_one({"username": username, "password": password})
        user_id = str(result.inserted_id)
        if not user_id:
            app.logger.error("Failed to register user")
            return {"message": "Failed to register user"}, 422
        app.logger.info(f"User {username} registered successfully")
        return {"message": "User registered", "user_id" : user_id }, 201

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

class Login(Resource):
    @limiter.limit("5 per minute")
    def post(self):
        data = request.get_json()
        user = users.find_one({
            "username": data.get("username"),
            "password": hash_password(data.get("password"))
        })
        if not user:
            app.logger.info("Invalid credentials")
            return {"message": "Invalid credentials"}, 401
        token = generate_token(user["_id"])
        return {"message": "Login successful", "user_id": str(user["_id"]),"token": token }, 200

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

class Recommend(Resource):
    def post(self):
        auth_header = request.headers.get("Authorization")
        validated, user_id_or_msg = validate_jwt_token(auth_header)
        if not validated:
            return {"error": user_id_or_msg}, 401
        user_id = user_id_or_msg

        # Validate input
        user_tasks = tasks.find({"user_id": user_id})
        for task in user_tasks:
            task_id = str(task.get("_id"))
            if task.get("description") == "":
                return {"error": "Task description is required"}, 400
            description = task.get("description")

            # Ask OpenAI
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You're a productivity assistant."},
                        {"role": "user", "content": f"Give a recommendation for: {description}"}
                    ]
                )
                recommendation = response["choices"][0]["message"]["content"]
                # Store in DB
                recommendations.insert_one({
                    "user_id": user_id,
                    "task_id": task_id,
                    "description": description,
                    "recommendation": recommendation
                })



            except Exception as e:
                return {"error": f"AI service failed: {str(e)}"}, 500

        return recommendations.find({"user_id": user_id}), 200

api.add_resource(Register, "/api/auth/register")
api.add_resource(Login, "/api/auth/login")
api.add_resource(Tasks, "/api/tasks")
api.add_resource(SingleTask, "/api/tasks/<string:task_id>")
api.add_resource(Recommend, "/api/ai/recommend")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
