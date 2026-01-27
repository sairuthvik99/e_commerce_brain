"""
Historical Case Retriever
"""

import json
from typing import List, Dict, Any
from langchain_openai import AzureOpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from backend.settings import Settings


class HistoricalCaseRetriever:
    """
    Retrieves similar past analyses from the Vector DB using semantic search.
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
        
        # Get the Pinecone index
        self.index = pc.Index(self.index_name)
        
        # Initialize vector store
        self.vectorstore = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings
        )

    def find_similar_cases(self, query: str, k: int = 3) -> List[str]:
        """Find k most similar past analyses."""
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
    
    def find_similar_cases_with_metadata(
        self, 
        query: str, 
        k: int = 3,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Find similar cases with metadata."""
        if filter_dict:
            docs = self.vectorstore.similarity_search(query, k=k, filter=filter_dict)
        else:
            docs = self.vectorstore.similarity_search(query, k=k)
        
        return [
            {
                "content": json.loads(doc.page_content) if doc.page_content else {},
                "metadata": doc.metadata
            }
            for doc in docs
        ]