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

    def save_analysis(self, analysis: Dict[str, Any]):
        """Save a completed analysis to the vector DB."""
        doc = Document(
            page_content=json.dumps(analysis),
            metadata={
                "root_cause": analysis.get("root_cause", ""),
                "primary_cause": analysis.get("primary_cause", ""),
                "confidence": analysis.get("confidence", 0.0),
                "timestamp": analysis.get("timestamp", "")
            }
        )
        self.vectorstore.add_documents([doc])
    
    def search_similar_analyses(self, query: str, k: int = 5):
        """Search for similar past analyses."""
        results = self.vectorstore.similarity_search(query, k=k)
        return [json.loads(doc.page_content) for doc in results]