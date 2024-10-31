import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # This reads from .env
YOUR_USERNAME = "Username"  # Replace with your actual username
CHAT_FILE = "chat.txt"  # Your chat file path

# Model settings
MODEL_NAME = "gpt-4o" 
MAX_TOKENS = 500  # Increased for longer responses
TEMPERATURE = 0.7
