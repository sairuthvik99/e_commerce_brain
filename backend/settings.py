import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DIAL_API_KEY: str = os.getenv("DIAL_API_KEY")
    AZURE_ENDPOINT: str = "https://ai-proxy.lab.epam.com"
    API_VERSION: str = "2024-02-01"
    
    # Per-agent model mapping
    AGENT_MODELS = {
        "supervisor": "gpt-4",
        "sales": "gpt-4",
        "inventory": "gpt-4",
        "marketing": "gpt-4",
        "support": "gpt-4",
        "reflection": "gpt-4",
    }

    @classmethod
    def validate(cls):
        if not cls.DIAL_API_KEY:
            raise RuntimeError("DIAL_API_KEY not found in environment variables.")

Settings.validate()