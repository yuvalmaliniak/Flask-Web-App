from flask import Flask,jsonify,request,render_template
from pymongo import MongoClient
from flask_restful import Resource, Api, reqparse
import hashlib, os
from bson import ObjectId
from data_validations import validate_register_data
app = Flask(__name__)
api = Api(app)

connection_string = "mongodb://localhost:27017/"
client = MongoClient(connection_string)

db = client['task_manager']
users = db['users']
tasks = db['tasks']
@app.route('/')
def home():
    return render_template('login.html')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class Register(Resource):
    def post(self):
        if not request.is_json or request.headers.get('Content-Type') != 'application/json':
            return {"error": "Unsupported media type"}, 415
        data = request.get_json()
        valid_creds , msg = validate_register_data(data)
        if not valid_creds:
            return {"error": msg}, 400

        username = data.get("username")
        password = hash_password(data.get("password"))
        if users.find_one({"username": username}):
            return {"message": "User already exists"}, 400
        users.insert_one({"username": username, "password": password})
        return {"message": "User registered"}, 201


api.add_resource(Register, "/api/auth/register")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
