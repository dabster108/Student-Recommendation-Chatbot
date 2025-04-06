from app.models.conversation import Conversation
from app.core.config import GROQ_API_KEY
from groq import Groq
from app.schemas.chat import UserInput


ALLOWED_KEYWORDS = [
    "location", "map", "navigate", "navigation", "how to go", "where is", "direction",
    "route", "travel", "distance", "address", "way", "path", "nearby", "place", "street"
]

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful assistant that only responds to questions related to maps, navigation, "
        "directions, and locations. Do not answer questions unrelated to places, routes, or geographic directions. "
        "If the query is outside this domain, respond with: "
        "'Sorry, I can only help with map and navigation-related questions.'"
    )
}


class GroqService:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def _is_valid_map_query(self, message: str) -> bool:
        message = message.lower()
        return any(keyword in message for keyword in ALLOWED_KEYWORDS)

    def get_response(self, user_input: UserInput) -> str:
        if not self._is_valid_map_query(user_input.message):
            return "Sorry, I can only help with map and navigation-related questions."

        conversation = Conversation()

        # Prepend the system prompt
        conversation.add_message(SYSTEM_PROMPT["role"], SYSTEM_PROMPT["content"])
        conversation.add_message(user_input.role, user_input.message)

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=conversation.get_messages(),
                temperature=1,
                max_tokens=1024,
                top_p=1,
                stream=True,
                stop=None,
            )

            response = ""
            for chunk in completion:
                response += chunk.choices[0].delta.content or ""

            return response

        except Exception as e:
            raise Exception(f"Error with Groq API: {str(e)}")
