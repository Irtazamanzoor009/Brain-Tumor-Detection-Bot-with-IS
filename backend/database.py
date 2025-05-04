from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["secure_app"]
users_collection = db["users"]
audit_logs = db["audit_logs"]
