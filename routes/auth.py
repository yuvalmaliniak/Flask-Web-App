from flask_restful import Resource
from flask import request, current_app as app
from Utils.db import get_users_collection
from Utils.jwt_utils import hash_password, generate_token
from Utils.data_validations import validate_register_data
from Utils.limiter import limiter

users = get_users_collection()
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
