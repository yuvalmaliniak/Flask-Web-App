from flask import Flask,jsonify,request,render_template
from pymongo import MongoClient
from flask_restful import Resource, Api, reqparse
import hashlib, os
from bson import ObjectId
from data_validations import validate_register_data
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
from flask_cors import CORS

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
        return {"message": "Login successful", "user_id": str(user["_id"])}, 200


api.add_resource(Register, "/api/auth/register")
api.add_resource(Login, "/api/auth/login")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
