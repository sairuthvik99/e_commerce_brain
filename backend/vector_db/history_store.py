"""
History Store - Vector Database for storing analyses
"""

import json
from typing import Dict, Any
from langchain_openai import AzureOpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone
from backend.settings import Settings


class HistoryStore:
    """
    Stores completed analyses (root cause, agent findings, actions, context) in a Vector DB.
    """

    def __init__(self):
        # Use AzureOpenAIEmbeddings for DIAL (Azure-style auth)
        self.embeddings = AzureOpenAIEmbeddings(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.EMBEDDING_DEPLOYMENT,
            check_embedding_ctx_length=False  # Required for text-embedding-005
        )
        
        # Initialize Pinecone
        pc = Pinecone(api_key=Settings.PINECONE_API_KEY)
        self.index_name = Settings.PINECONE_INDEX
        self.index = pc.Index(self.index_name)
        
        # Initialize vector store
        self.vectorstore = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings
        )

    def _serialize_for_metadata(self, value: Any) -> Any:
        """
        Serialize a value for Pinecone metadata.
        Pinecone only accepts: string, number, boolean, or list of strings.
        Complex objects (dicts, nested lists) must be JSON-serialized.
        """
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            # Check if all items are strings
            if all(isinstance(item, str) for item in value):
                return value
            # Otherwise serialize to JSON string
            return json.dumps(value)
        if isinstance(value, dict):
            return json.dumps(value)
        # Fallback: convert to string
        return str(value)

    def save_analysis(self, analysis: Dict[str, Any]):
        """Save a completed analysis to the vector DB."""
        # Extract root_cause data - handle both dict and nested structures
        root_cause_data = analysis.get("root_cause", {})
        
        # Extract simple values for metadata (Pinecone requires simple types)
        primary_cause = ""
        confidence = 0.0
        
        if isinstance(root_cause_data, dict):
            primary_cause = root_cause_data.get("primary_cause", "")
            confidence = root_cause_data.get("confidence", 0.0)
            # Handle case where confidence might be nested
            if not isinstance(confidence, (int, float)):
                confidence = 0.0
        
        doc = Document(
            page_content=json.dumps(analysis),
            metadata={
                # Serialize complex objects to JSON strings
                "root_cause": self._serialize_for_metadata(root_cause_data),
                "primary_cause": str(primary_cause) if primary_cause else "",
                "confidence": float(confidence) if isinstance(confidence, (int, float)) else 0.0,
                "timestamp": str(analysis.get("timestamp", "")),
                "question": str(analysis.get("question", ""))[:500],  # Truncate for metadata limits
                "intent": str(analysis.get("intent", ""))
            }
        )
        self.vectorstore.add_documents([doc])
    
    def search_similar_analyses(self, query: str, k: int = 5):
        """Search for similar past analyses."""
        results = self.vectorstore.similarity_search(query, k=k)
        return [json.loads(doc.page_content) for doc in results]