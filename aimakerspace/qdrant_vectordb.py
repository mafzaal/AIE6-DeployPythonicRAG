import numpy as np
from typing import List, Tuple, Callable, Dict, Any, Optional
import asyncio
import uuid

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from aimakerspace.openai_utils.embedding import EmbeddingModel


class QdrantVectorDatabase:
    """
    Qdrant vector database implementation that follows the same interface
    as the in-memory VectorDatabase class.
    """
    def __init__(self, 
                 collection_name: str = "documents", 
                 embedding_model: EmbeddingModel = None,
                 host: str = "localhost",
                 port: int = 6333,
                 grpc_port: int = 6334,
                 prefer_grpc: bool = True,
                 in_memory: bool = True):
        """
        Initialize QdrantVectorDatabase
        
        Args:
            collection_name: Name of the collection to use
            embedding_model: Embedding model to use
            host: Qdrant server host
            port: Qdrant server port
            grpc_port: Qdrant server gRPC port
            prefer_grpc: Whether to prefer gRPC over HTTP
            in_memory: Whether to use in-memory storage
        """
        self.collection_name = collection_name
        self.embedding_model = embedding_model or EmbeddingModel()
        self.in_memory = in_memory
        
        if in_memory:
            self.client = QdrantClient(":memory:")
            self.async_client = AsyncQdrantClient(":memory:")
        else:
            self.client = QdrantClient(
                host=host, 
                port=port,
                grpc_port=grpc_port,
                prefer_grpc=prefer_grpc
            )
            self.async_client = AsyncQdrantClient(
                host=host, 
                port=port,
                grpc_port=grpc_port,
                prefer_grpc=prefer_grpc
            )
            
        # Store mapping from keys to ids
        self.key_to_id: Dict[str, str] = {}
        self.id_to_key: Dict[str, str] = {}
        
        # Create collection if it doesn't exist
        vector_size = self.embedding_model.get_embedding_dimension()
        self._ensure_collection(vector_size)
        
    def _ensure_collection(self, vector_size: int):
        """Ensure collection exists"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                print(f"Creating collection {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Collection {self.collection_name} created successfully")
            else:
                print(f"Collection {self.collection_name} already exists")
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            # Create the collection anyway as a fallback
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection {self.collection_name} after error")
            except Exception as e2:
                print(f"Failed to create collection after error: {e2}")
    
    async def _async_ensure_collection(self, vector_size: int):
        """Ensure collection exists asynchronously"""
        try:
            collections = await self.async_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                print(f"Creating collection {self.collection_name} asynchronously")
                await self.async_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Collection {self.collection_name} created successfully")
            else:
                print(f"Collection {self.collection_name} already exists")
        except Exception as e:
            print(f"Error ensuring collection exists asynchronously: {e}")
            # Create the collection anyway as a fallback
            try:
                await self.async_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection {self.collection_name} after error")
            except Exception as e2:
                print(f"Failed to create collection after error: {e2}")
    
    def insert(self, key: str, vector: np.array) -> None:
        """Insert a vector into the database"""
        # Generate a unique ID for this key
        point_id = str(uuid.uuid4())
        
        # Store the mapping
        self.key_to_id[key] = point_id
        self.id_to_key[point_id] = key
        
        # Insert the point
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                    payload={"text": key}
                )
            ]
        )
    
    def search(
        self,
        query_vector: np.array,
        k: int,
        distance_measure: Callable = None,  # Ignored, Qdrant uses its own distance measure
    ) -> List[Tuple[str, float]]:
        """Search for similar vectors"""
        # Convert query_vector to list if it's a numpy array
        if hasattr(query_vector, 'tolist'):
            query_vector_list = query_vector.tolist()
        else:
            # If it's already a list or another iterable, convert to list to be safe
            query_vector_list = list(query_vector)
            
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector_list,
            limit=k
        )
        
        results = []
        for scored_point in search_result:
            point_id = scored_point.id
            score = scored_point.score
            # Get the key from the id
            if point_id in self.id_to_key:
                key = self.id_to_key[point_id]
                results.append((key, score))
        
        return results
    
    def search_by_text(
        self,
        query_text: str,
        k: int,
        distance_measure: Callable = None,  # Ignored, Qdrant uses its own distance measure
        return_as_text: bool = False,
    ) -> List[Tuple[str, float]]:
        """Search by text query"""
        query_vector = self.embedding_model.get_embedding(query_text)
        results = self.search(query_vector, k, distance_measure)
        return [result[0] for result in results] if return_as_text else results
    
    def retrieve_from_key(self, key: str) -> Optional[np.array]:
        """Retrieve a vector by key"""
        if key not in self.key_to_id:
            return None
        
        point_id = self.key_to_id[key]
        points = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[point_id]
        )
        
        if not points:
            return None
            
        return np.array(points[0].vector)
    
    async def abuild_from_list(self, list_of_text: List[str]) -> "QdrantVectorDatabase":
        """Build database from a list of texts"""
        # Ensure collection exists before inserting
        vector_size = self.embedding_model.get_embedding_dimension()
        await self._async_ensure_collection(vector_size)
        
        embeddings = await self.embedding_model.async_get_embeddings(list_of_text)
        
        # Generate unique IDs for each text
        point_ids = [str(uuid.uuid4()) for _ in range(len(list_of_text))]
        
        # Store mappings
        for text, point_id in zip(list_of_text, point_ids):
            self.key_to_id[text] = point_id
            self.id_to_key[point_id] = text
        
        # Prepare points for batch insertion
        points = [
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={"text": text}
            )
            for point_id, text, embedding in zip(point_ids, list_of_text, embeddings)
        ]
        
        # Use batched upsert for efficiency
        batch_size = 100
        try:
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                await self.async_client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            print(f"Successfully inserted {len(points)} points into collection {self.collection_name}")
        except Exception as e:
            print(f"Error inserting points: {e}")
            # Try recreating the collection and inserting again
            await self._async_ensure_collection(vector_size)
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                await self.async_client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
        
        return self
    
    def get_all_texts(self) -> List[str]:
        """
        Returns all the text documents stored in the vector database.
        
        Returns:
            List[str]: A list of all text documents
        """
        return list(self.key_to_id.keys()) 