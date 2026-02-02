import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DIAL_API_KEY: str = os.getenv("DIAL_API_KEY")
    AZURE_ENDPOINT: str = os.getenv("AZURE_ENDPOINT")
    API_VERSION: str = os.getenv("API_VERSION")
    EMBEDDING_DEPLOYMENT: str = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX", "ai-ops-history")
    
    # Per-agent model mapping
    AGENT_MODELS = {
        "supervisor": "gpt-4",
        "sales": "gpt-4",
        "inventory": "gpt-4",
        "marketing": "gpt-4",
        "support": "gpt-4",
        "reflection": "gpt-4",
        "general": "gpt-4",
    }

    @classmethod
    def validate(cls):
        if not cls.DIAL_API_KEY:
            raise RuntimeError("DIAL_API_KEY not found in environment variables.")

    
    # ==================== DATABASE CONFIGURATION ====================

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # ==================== LANGFUSE CONFIGURATION ====================
    
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_BASE_URL: str = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    
    # Fixed Session and User IDs for tracing
    LANGFUSE_SESSION_ID: str = "e-Commerce Multi Agents"
    LANGFUSE_USER_ID: str = "001"

Settings.validate()