import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_bdrUhSniq75c@ep-square-queen-a1a46t2r-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

OPENROUTER_API_KEY_1 = os.getenv("OPENROUTER_API_KEY_1")
OPENROUTER_API_KEY_2 = os.getenv("OPENROUTER_API_KEY_2")
OPENROUTER_API_KEY_3 = os.getenv("OPENROUTER_API_KEY_3")
OPENROUTER_API_KEY_4 = os.getenv("OPENROUTER_API_KEY_4")
OPENROUTER_API_KEY_5 = os.getenv("OPENROUTER_API_KEY_5")
OPENROUTER_API_KEY_6 = os.getenv("OPENROUTER_API_KEY_6")
OPENROUTER_API_KEY_7 = os.getenv("OPENROUTER_API_KEY_7")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-3-flash-preview")


KEY_ID = os.getenv("keyId")
APPLICATION_KEY = os.getenv("keyName")
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
BUCKET_NAME = os.getenv("BUCKET_NAME")
