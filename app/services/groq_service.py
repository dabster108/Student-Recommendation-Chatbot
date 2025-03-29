from app.models.conversation import Conversation
from app.core.config import GROQ_API_KEY
from groq import Groq

class GroqService:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def get_response(self, user_input: UserInput) -> str:
        conversation = Conversation()

        # Append user's message to conversation
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
