import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

OPENROUTER_API_KEY_1 = os.getenv("OPENROUTER_API_KEY_1")
OPENROUTER_API_KEY_2 = os.getenv("OPENROUTER_API_KEY_2")
OPENROUTER_API_KEY_3 = os.getenv("OPENROUTER_API_KEY_3")
OPENROUTER_API_KEY_4 = os.getenv("OPENROUTER_API_KEY_4")
OPENROUTER_API_KEY_5 = os.getenv("OPENROUTER_API_KEY_5")
OPENROUTER_API_KEY_6 = os.getenv("OPENROUTER_API_KEY_6")
OPENROUTER_API_KEY_7 = os.getenv("OPENROUTER_API_KEY_7")


KEY_ID = os.getenv("keyId")
APPLICATION_KEY = os.getenv("keyName")
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
BUCKET_NAME = os.getenv("BUCKET_NAME")
