import os

# API Version information
API_VERSION = "0.3.0"
BUILD_DATE = "2025-04-13"  # Update this when making significant changes

# File storage
STATIC_DIR = "static"

# Settings
DEFAULT_NUM_SEARCH_RESULTS = 4  # Number of search results to return by default

# Get env vars with defaults
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0") 