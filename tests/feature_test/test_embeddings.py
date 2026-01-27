"""
Quick test to verify DIAL Embeddings setup
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
print(f"Loading .env from: {env_path}")
print(f".env exists: {env_path.exists()}")
load_dotenv(env_path)

from langchain_openai import AzureOpenAIEmbeddings

print("\n" + "="*60)
print("Testing DIAL Embeddings Setup")
print("="*60)

# Check environment variables
dial_key = os.getenv('DIAL_API_KEY')
dial_endpoint = os.getenv('AZURE_ENDPOINT')
api_version = os.getenv('API_VERSION', '2024-02-01')
embedding_model = os.getenv('AZURE_EMBEDDING_DEPLOYMENT', 'text-embedding-005')

print(f"\nDIAL Endpoint: {dial_endpoint}")
print(f"API Version: {api_version}")
print(f"Embedding Model: {embedding_model}")

if dial_key:
    print(f"DIAL API Key: {dial_key[:8]}...{dial_key[-4:] if len(dial_key) > 12 else '***'}")
else:
    print("❌ DIAL API Key: NOT SET")
    sys.exit(1)

if not dial_endpoint:
    print("❌ DIAL Endpoint: NOT SET")
    sys.exit(1)

print("\n" + "="*60)
print("Testing Embeddings")
print("="*60)

try:
    # Use AzureOpenAIEmbeddings for DIAL (Azure-style auth with api-key header)
    embeddings = AzureOpenAIEmbeddings(
        api_key=dial_key,
        azure_endpoint=dial_endpoint,
        api_version=api_version,
        model=embedding_model,
        check_embedding_ctx_length=False  # Required for text-embedding-005
    )
    
    # Test embedding
    print("\nGenerating test embedding...")
    test_text = "This is a test"
    result = embeddings.embed_query(test_text)
    
    print(f"✅ Success! Embedding dimension: {len(result)}")
    print(f"First 5 values: {result[:5]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()