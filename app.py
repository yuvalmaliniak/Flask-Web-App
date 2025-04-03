from flask import Flask,jsonify,request,render_template
from pymongo import MongoClient
from flask_restful import Resource, Api, reqparse
app = Flask(__name__)
api = Api(app)

connection_string = "mongodb://localhost:27017/"
client = MongoClient(connection_string)

db = client['task_manager']
users_collection = db['users']
tasks_collection = db['tasks']
@app.route('/')
def home():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
