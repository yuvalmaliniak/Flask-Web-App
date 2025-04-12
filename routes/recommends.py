from flask.cli import load_dotenv
from flask_restful import Resource
from flask import request, current_app as app
from data_validations import validate_jwt_token
from Utils.db import get_tasks_collection, get_recommendations_collection
from openai import OpenAI
import dotenv, os

load_dotenv()

ai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

tasks = get_tasks_collection()
recommendations = get_recommendations_collection()

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
            if task.get("description") == "" or task.get("title") == "":
                return {"error": "Task description and title is required"}, 400
            existing_recs = recommendations.find_one({
                "user_id": user_id,
                "task_id": task_id
            })
            if existing_recs:
                continue
            description = task.get("description")
            title = task.get("title")

            # Ask OpenAI
            try:
                response = ai_client.responses.create(
                    model="gpt-3.5-turbo",
                    instructions="You're a productivity assistant for task management.",
                    input=f"Give a recommendation for the task titled : {title} with description:  {description}. Do it in maximum of 3 sentences.",
                )
                print(response.output_text)
                print(f"type of response: {type(response.output_text)}")
                recommendation = response.output_text
                # Store in DB
                recommendations.insert_one({
                    "user_id": user_id,
                    "task_id": task_id,
                    "description": description,
                    "recommendation": recommendation
                })



            except Exception as e:
                return {"error": f"AI service failed: {str(e)}"}, 500

        recs = recommendations.find({"user_id": user_id})
        output = [
            {"_id": str(r["_id"]), **{k: v for k, v in r.items() if k != "_id"}}
            for r in recs
        ]
        return output, 200
