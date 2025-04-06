
# 🗺️ FastAPI ChatBot (Maps-Only) using Groq API

[![Build Status](https://img.shields.io/github/workflow/status/yourusername/FastAPI_ChatBot/CI)](https://github.com/yourusername/FastAPI_ChatBot/actions) 
[![License](https://img.shields.io/github/license/yourusername/FastAPI_ChatBot)](https://github.com/yourusername/FastAPI_ChatBot/blob/main/LICENSE)
[![Python Version](https://img.shields.io/pypi/pyversions/fastapi)](https://www.python.org/)

A FastAPI-based chatbot that utilizes the **Groq API** (LLaMA-3.1-8b-instant) to answer **location, map, and navigation-related** queries. It is designed to provide accurate directions, maps, and place information—focusing strictly on **map-related responses**.

---

## 🚀 Features

- 🤖 **Groq-powered ChatBot** using **LLaMA-3** API for intelligent responses
- 🌍 Provides **map and location-based responses only** 
- ⚡ Built with **FastAPI** for fast and asynchronous web handling
- 🔐 Secure environment variables for API key storage
- 📦 Modular architecture for easy extensions and scaling

---

## 📂 Project Structure

```
FastAPI_ChatBot/
├── app/
│   ├── api/v1/endpoints/        # API route handlers
│   │   └── chat.py
│   ├── core/                    # Configuration
│   │   └── config.py
│   ├── models/                  # Conversation history (optional memory logic)
│   │   └── conversation.py
│   ├── schemas/                 # Request/response models
│   │   └── chat.py
│   ├── services/                # Groq API integration
│   │   └── groq_service.py
│   └── main.py                  # App entry point
├── .env                         # (Not committed) Store secrets here
├── .env.example                 # Template for environment variables
├── requirements.txt             # Python dependencies
├── README.md
└── LICENSE
```

---

## 📦 Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/FastAPI_ChatBot.git
cd FastAPI_ChatBot
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the root directory and add your **Groq API Key** as follows:

```env
# .env
GROQ_API_KEY=your_actual_groq_api_key_here
```

You can use the `.env.example` file as a template.

---

## ▶️ Run the App

To run the FastAPI server with hot-reload:

```bash
uvicorn app.main:app --reload
```

You can then access the **API documentation** at:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧠 API Usage

### Request Format:

Make a `POST` request to `/chat/` with the following JSON payload:

```json
POST /chat/
{
  "message": "How do I get to Kathmandu Durbar Square?",
  "role": "user",
  "conversation_id": "12345"
}
```

### Response Format:

```json
{
  "response": "Kathmandu Durbar Square is located in the heart of Kathmandu. From Thamel, it’s around 15 minutes by foot...",
  "conversation_id": "12345"
}
```

---

### Notes:
- **This chatbot is strictly limited to answering location and map-based questions**.
- The bot will not respond to general queries or anything beyond location/navigation-related topics.

---

## 🛠️ Technologies Used

- 🐍 Python 3.10+
- ⚡ FastAPI for building the API
- 🧠 Groq API (LLaMA-3.1-8b-instant) for natural language processing
- 🧩 Pydantic for data validation
- 📦 Uvicorn as the ASGI server for FastAPI

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙋‍♂️ Author

**Dikshanta** – [@yourgithub](https://github.com/yourgithub)

---

## 🌟 Star this repo if it helped you!

```
⭐ Let's build smarter location-based bots with FastAPI + Groq!
```
---

## 📝 Contributions

Feel free to fork this repo, create a branch, and submit pull requests if you'd like to contribute improvements or new features!

```

---

Let me know if you'd like further tweaks or additions! This `README.md` includes setup instructions, project structure, and API usage along with useful badges for your GitHub project.
