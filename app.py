from flask import Flask,render_template
from flask.cli import load_dotenv
from flask_restful import Api
import logging, os
from logging.handlers import RotatingFileHandler
from Utils.db import db_init
from flask_cors import CORS
import dotenv
from Utils.limiter import limiter
from routes.auth import Register, Login
from routes.tasks import Tasks, SingleTask
from routes.recommends import Recommend
load_dotenv()

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

db = db_init()
users = db['users']
tasks = db['tasks']
recommendations = db['recommendations']
# To change:
#CORS(app,origins=["http://localhost:3000"], supports_credentials=True)
@app.route('/')
def home():
    return render_template('login.html')

limiter.init_app(app)




api.add_resource(Register, "/api/auth/register")
api.add_resource(Login, "/api/auth/login")
api.add_resource(Tasks, "/api/tasks")
api.add_resource(SingleTask, "/api/tasks/<string:task_id>")
api.add_resource(Recommend, "/api/ai/recommend")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
