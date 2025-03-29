
# FastAPI_ChatBot

A chatbot powered by FastAPI and Groq's Llama 3.1-8B-Instant model. This project provides a conversational AI API with structured conversation management and real-time responses.

## Features
- FastAPI Framework for high-performance APIs
- Integration with Groq API for AI-powered conversations
- Real-time chat functionality
- CORS enabled for frontend integration

## Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/FastAPI_ChatBot.git
    cd FastAPI_ChatBot
    ```

2. Create a virtual environment:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up your `.env` file with your Groq API key:
    ```
    GROQ_API_KEY=your_groq_api_key_here
    ```

5. Run the server:
    ```sh
    uvicorn app.main:app --reload
    ```

6. Visit `http://127.0.0.1:8000/docs` for the Swagger UI.

7. Project Structure
   FastAPI_ChatBot/
│── app/
│   ├── api/v1/endpoints/
│   │   ├── chat.py
│   │   ├── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   ├── __init__.py
│   ├── models/
│   │   ├── conversation.py
│   │   ├── __init__.py
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── __init__.py
│   ├── services/
│   │   ├── groq_service.py
│   │   ├── __init__.py
│   ├── main.py
│── .env
│── requirements.txt
│── README.md
│── LICENSE


## License
This project is licensed under the MIT License.
