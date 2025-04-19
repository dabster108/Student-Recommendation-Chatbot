import json
import os
from app.models.conversation import Conversation
from app.core.config import GROQ_API_KEY
from groq import Groq
from app.schemas.chat import UserInput

# Ensure the output directory exists
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are ChatGPT, a helpful and intelligent assistant. "
        "You assist users by providing accurate and concise responses to their queries. "
        "Your goal is to understand the user's input and provide meaningful and contextually appropriate answers."
    )
}

class GroqService:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def categorize_transaction(self, description: str) -> dict:
        category = 'Other'
        remarks = 'General transaction'

        if 'Fund Transferred' in description:
            category = 'Transfer'
            remarks = 'Fund Transfer transaction'
        elif 'Topup' in description:
            category = 'Topup'
            remarks = 'Mobile Topup transaction'
        elif 'Paid for' in description:
            category = 'Payment'
            remarks = 'Payment transaction'
        
        return {
            'category': category,
            'description': description,
            'remarks': remarks
        }

    def get_response(self, user_input: UserInput) -> dict:
        conversation = Conversation()
        conversation.add_message(SYSTEM_PROMPT["role"], SYSTEM_PROMPT["content"])

        category_data = self.categorize_transaction(user_input.text)

        # Prepare the response
        response = {
            "id": user_input.id if user_input.id else str(uuid4()),
            "category": category_data['category'],
            "remarks": category_data['remarks'],
            "description": category_data['description']
        }

        # Save the response to a file
        file_path = os.path.join(OUTPUT_DIR, f"{response['id']}_converted.json")
        with open(file_path, 'w') as f:
            json.dump(response, f, indent=4)

        return response
