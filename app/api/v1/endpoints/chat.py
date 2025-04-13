from fastapi import APIRouter, HTTPException
from app.schemas.chat import UserInput, CategorizedResponse
from app.services.groq_service import GroqService
import os
import json
from uuid import uuid4
import logging

router = APIRouter()
groq_service = GroqService()

# Create a logger to debug issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get absolute path for data store
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
DATA_STORE_PATH = os.path.join(BASE_DIR, 'app', 'output', 'data_store.json')

# Load data from the file to avoid data loss after server restart
def load_data():
    logger.info(f"Loading data from {DATA_STORE_PATH}")
    if os.path.exists(DATA_STORE_PATH):
        try:
            with open(DATA_STORE_PATH, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded data: {data}")
                return data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {}
    logger.warning(f"Data store file not found at {DATA_STORE_PATH}")
    return {}

# Save data to the file to persist it
def save_data():
    try:
        os.makedirs(os.path.dirname(DATA_STORE_PATH), exist_ok=True)
        with open(DATA_STORE_PATH, 'w') as f:
            json.dump(categorized_data_store, f, indent=4)
            logger.info(f"Data saved successfully to {DATA_STORE_PATH}")
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        raise Exception(f"Error saving data: {e}")

# Initialize categorized_data_store by loading from the file
categorized_data_store = load_data()

@router.post("/convert-text")
async def convert_text_to_response(user_input: UserInput):
    try:
        # Use the provided ID or generate a new one
        category_id = user_input.id if user_input.id else str(uuid4())

        # Get categorized response
        response = groq_service.get_response(user_input)

        # Add response to categorized_data_store
        categorized_data_store[category_id] = {
            "id": category_id,
            "text": user_input.text,
            "category": response["category"],
            "remarks": response["remarks"],
            "description": response["description"]
        }

        # Save data to file
        save_data()

        return {"message": "Response saved successfully", "id": category_id}

    except Exception as e:
        logger.error(f"Error in creating chat response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/response/{category_id}", response_model=CategorizedResponse)
async def get_chat_response(category_id: str):
    if category_id not in categorized_data_store:
        logger.error(f"Category ID {category_id} not found")
        raise HTTPException(status_code=404, detail="Category not found")

    # Return the categorized transaction data
    return categorized_data_store[category_id]
