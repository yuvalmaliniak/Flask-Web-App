from flask.cli import load_dotenv
from flask_restful import Resource
from flask import request, current_app as app
from data_validations import validate_jwt_token
from Utils.db import get_tasks_collection, get_recommendations_collection
from openai import OpenAI
import dotenv, os, re
from routes.telegram import send_telegram_message

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
                prompt = (
                    f"Analyze this task:\n"
                    f"Title: {title}\n"
                    f"Description: {description}\n\n"
                    f"Return in this format ONLY (make sure to add new line between the 3 things):\n"
                    f"- A short recommendation, max of 3 sentences\n"
                    f"- The category (e.g. coding, writing, planning) in 1 word\n"
                    f"- An estimated time to complete in hours"
                    f" Example:\n"
                    f"- I would do this by splitting to parts\n"
                    f"Category:House"
                    f"Time to complete(in hours): 2\n"
                )
                response = ai_client.responses.create(
                    model="gpt-3.5-turbo",
                    instructions="You're a productivity assistant for task management.",
                    input=prompt,
                )
                print(response.output_text)
                content = response.output_text
                # Extract recommendation before "Category:"
                recommendation_match = re.split(r"Category:", content, maxsplit=1)
                recommendation = recommendation_match[0].strip() if recommendation_match else content

                # Extract category
                category_match = re.search(r"Category:\s*(.+)", content)
                category = category_match.group(1).strip() if category_match else "unknown"

                # Extract time
                time_match = re.search(r"Time to complete.*?:\s*(.+)", content)
                estimated_time = time_match.group(1).strip() if time_match else "unknown"

                print(f"Recommendation: {recommendation}, Category: {category}, Time: {estimated_time}")
                # Store in DB
                recommendations.insert_one({
                    "user_id": user_id,
                    "task_id": task_id,
                    "title": title,
                    "description": description,
                    "recommendation": recommendation,
                    "category": category,
                    "estimated_time": estimated_time
                })
                send_telegram_message(f"🤖 AI insight ready for: {title}\n{recommendation}")


            except Exception as e:
                app.logger.error(f"OpenAI failed: {str(e)}")
                continue

        recs = recommendations.find({"user_id": user_id})
        output = [
            {"_id": str(r["_id"]), **{k: v for k, v in r.items() if k != "_id"}}
            for r in recs
        ]
        return output, 200

class WeeklySummary(Resource):
    def get(self):
        auth_header = request.headers.get("Authorization")
        validated, user_id = validate_jwt_token(auth_header)
        if not validated:
            return {"error": user_id}, 401

        user_tasks = tasks.find({"user_id": user_id})
        task_list = "\n".join(f"- {t['title']}: {t.get('description', '')}" for t in user_tasks)
        try:
            response = ai_client.responses.create(
                model="gpt-3.5-turbo",
                instructions="You're a productivity assistant for task management.",
                input=f"Summarize in maximum of 3 sentences these open tasks:\n{task_list}.",
            )
            summary = response.output_text
            send_telegram_message(f"🧠 Weekly Summary:\n{summary}")
        except Exception as e:
            return {"error": f"AI service failed: {str(e)}"}, 500

        return {"summary": summary}, 200

class Schedule(Resource):
    def get(self):
        auth_header = request.headers.get("Authorization")
        validated, user_id_or_msg = validate_jwt_token(auth_header)
        if not validated:
            return {"error": user_id_or_msg}, 401
        user_id = user_id_or_msg

        user_tasks = list(tasks.find({"user_id": user_id}))
        if not user_tasks:
            return {"message": "No tasks found to schedule."}, 404

        task_list = "\n".join(f"- {t['title']}: {t.get('description', '')}" for t in user_tasks)
        prompt = (f"Given the following tasks, suggest a 1-day schedule with time blocks. ONLY in the format like this:"
                  f" 09:00-10:00 Yoga\n"
                  f"list:\n{task_list}")

        try:
            response = ai_client.responses.create(
                model="gpt-3.5-turbo",
                instructions="You're a productivity assistant for task management.",
                input=prompt,
            )
            print(response.output_text)
            schedule = response.output_text
            send_telegram_message(f"📅 Your schedule for today:\n{schedule}")
            return {"schedule": schedule}, 200
        except Exception as e:
            return {"error": f"Scheduling failed: {str(e)}"}, 500
