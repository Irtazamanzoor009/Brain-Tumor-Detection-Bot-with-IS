import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
JWT_EXPIRATION_SECONDS = 3600
