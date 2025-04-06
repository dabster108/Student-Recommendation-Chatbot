from dotenv import load_dotenv
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("API key for Groq is missing. Please set the GROQ_API_KEY in the .env file.")




# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")