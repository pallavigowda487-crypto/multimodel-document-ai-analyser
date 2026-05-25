import os
from pymongo import MongoClient
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self.uri = os.environ.get("MONGODB_URI")
        self.client = None
        self.db = None
        
        if self.uri:
            try:
                self.client = MongoClient(self.uri)
                self.db = self.client["multimodal_ai_db"]
                
                # Collections
                self.users_col = self.db["users"]
                self.uploads_col = self.db["uploads"]
                self.summaries_col = self.db["summaries"]
                self.chats_col = self.db["chats"]
                
                # Setup indexes
                self.uploads_col.create_index("file_hash")
                
                logger.info("Connected to MongoDB successfully.")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
        else:
            logger.warning("MONGODB_URI not found. Database functionality will be disabled or run in mock mode.")

db_config = DatabaseConfig()

def save_upload_metadata(metadata: dict) -> str:
    """Save upload metadata and return the inserted ID."""
    if db_config.db is not None:
        result = db_config.uploads_col.insert_one(metadata)
        return str(result.inserted_id)
    return "mock_id"

def get_upload_by_hash(file_hash: str) -> dict:
    """Check if a file was already uploaded to avoid duplicate processing."""
    if db_config.db is not None:
        return db_config.uploads_col.find_one({"file_hash": file_hash})
    return None

def save_chat_message(session_id: str, role: str, content: str):
    """Store chat message."""
    if db_config.db is not None:
        db_config.chats_col.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content
        })

def get_chat_history(session_id: str) -> list:
    """Retrieve chat history for a session."""
    if db_config.db is not None:
        cursor = db_config.chats_col.find({"session_id": session_id}).sort("_id", 1)
        return list(cursor)
    return []

def save_summary(data: dict):
    """Store generated summary or analysis."""
    if db_config.db is not None:
        db_config.summaries_col.insert_one(data)
