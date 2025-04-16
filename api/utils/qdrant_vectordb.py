from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from langchain_openai.embeddings import OpenAIEmbeddings
import tiktoken

def tiktoken_len(text):
    tokens = tiktoken.encoding_for_model("gpt-4o-mini").encode(
        text,
    )
    return len(tokens)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 100,
    chunk_overlap = 0,
    length_function = tiktoken_len,
)

client = QdrantClient(":memory:")
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

def create_collection(collection_name: str) -> QdrantVectorStore:
    client.create_collection(
        client=client,
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
        
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embedding_model,
    )

    return vector_store

def create_vector_store(collection_name: str, document: str):
    texts = text_splitter.split_text(document)
    vector_store = create_collection(collection_name)
    vector_store.add_texts(texts=texts)
    return vector_store


def get_vector_store(collection_name: str):
    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embedding_model,
    )

def retrieve_from_vector_store(collection_name: str, query: str):
    vector_store = get_vector_store(collection_name)
    return vector_store.similarity_search(query)

def delete_collection(collection_name: str):
    client.delete_collection(collection_name=collection_name)
