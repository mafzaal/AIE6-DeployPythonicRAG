import os

# API Version information
API_VERSION = "0.3.0"
BUILD_DATE = "2025-04-13"  # Update this when making significant changes

# File storage
STATIC_DIR = "static"

# Settings
DEFAULT_NUM_SEARCH_RESULTS = 4  # Number of search results to return by default

# Qdrant settings
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", 6334))
QDRANT_PREFER_GRPC = os.getenv("QDRANT_PREFER_GRPC", "True").lower() == "true"
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")
QDRANT_IN_MEMORY = os.getenv("QDRANT_IN_MEMORY", "True").lower() == "true"

# Get env vars with defaults
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0") 