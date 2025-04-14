#!/bin/bash

echo "Starting Qdrant vector database..."

# Check if container is already running
if docker ps | grep -q "qdrant-server"; then
    echo "Qdrant is already running."
else
    # Create a Docker volume for persistence
    docker volume create qdrant_data

    # Run Qdrant
    docker run -d --name qdrant-server \
        -p 6333:6333 \
        -p 6334:6334 \
        -v qdrant_data:/qdrant/storage \
        -e QDRANT_ALLOW_ORIGIN="*" \
        qdrant/qdrant:latest

    echo "Qdrant started on ports 6333 (HTTP) and 6334 (gRPC)"
fi

echo "Qdrant is now available at http://localhost:6333"
echo "Use Ctrl+C to exit this script (Qdrant will continue running in the background)"
echo "To stop Qdrant later, run: docker stop qdrant-server"
echo "To remove the container, run: docker rm qdrant-server" 