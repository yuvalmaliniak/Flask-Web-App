# 🗂️ Flask Task Manager Web App

A full-stack Flask web application for managing tasks with user authentication, AI-powered recommendations, and Telegram alerts — deployed to AWS with Docker.

---

## 🚀 Features

- 🔐 User Registration & Login with JWT
- ✅ CRUD for tasks (Create, Read, Update, Delete)
- 🧠 OpenAI-powered task recommendations (category + time estimate)
- 🧾 Weekly task summary & 📅 daily schedule with AI
- 📦 MongoDB for data storage
- 🤖 Telegram notifications for AI insights
- 🌐 CORS-secured API access
- 🐳 Dockerized & deployed on AWS EC2

---

## 🧾 Tech Stack

- **Backend:** Python 3.12, Flask, Flask-RESTful
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MongoDB
- **AI:** OpenAI GPT-3.5 Turbo
- **Notifications:** Telegram Bot API
- **Infra:** Docker, Docker Compose, AWS EC2

---

---

## 📮 API Overview

| Endpoint                    | Method | Description                        |
|----------------------------|--------|------------------------------------|
| `/api/auth/register`       | POST   | Register new user                  |
| `/api/auth/login`          | POST   | Authenticate user                  |
| `/api/tasks`               | GET    | Get all tasks (authenticated user) |
| `/api/tasks`               | POST   | Add new task                       |
| `/api/tasks/<task_id>`     | GET    | Get specific task                  |
| `/api/tasks/<task_id>`     | PUT    | Update task                        |
| `/api/tasks/<task_id>`     | DELETE | Delete task                        |
| `/api/ai/recommend`        | POST   | AI-based task recommendations      |
| `/api/ai/weekly_summary`   | GET    | Weekly task summary (AI)           |
| `/api/ai/schedule`         | GET    | AI-generated daily schedule        |

---

## 🔐 .env Configuration

Create a `.env` file in the root folder with:

```env
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=0

JWT_SECRET=your_jwt_secret
OPENAI_API_KEY=your_openai_key
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

FRONTEND_ORIGIN=your_EC2_Public_IP
MONGO_URI=mongodb://mongo:27017/
```

## ☁️ AWS EC2 Deployment

### 1. Launch EC2 Instance
- Use **Ubuntu 22.04**
- Open ports:  
  - **22** (SSH)  
  - **8000** (Flask)  
  - **27017** (MongoDB, optional)
- Create and download a `.pem` key for SSH access

---

### 2. Connect to EC2

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```
### 3. Install Docker & Docker Compose

```bash
sudo apt update && sudo apt install -y docker.io git
```

### 4. Clone the repository

```bash
git clone https://github.com/yuvalmaliniak/Flask-Web-App.git
cd Flask-Web-App
```
### 5. Add your `.env` file

```bash
nano .env
# ADD the data from above
```

### 6. Build and run the Docker containers

```bash
sudo docker-compose up --build -d
```

### 7. Access the app
Open your browser and go to `http://<EC2_PUBLIC_IP>:8000`