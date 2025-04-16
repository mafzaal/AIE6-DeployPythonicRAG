FROM node:18 AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files and install dependencies in one layer
COPY app/frontend/package*.json ./
RUN npm install && \
    npm uninstall tailwindcss @tailwindcss/postcss && \
    npm install tailwindcss@3.3.0 postcss autoprefixer --save-dev

# Copy frontend source files and build in one layer
COPY app/frontend/ ./
RUN npm run build && ls -la build/

# Backend stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UVICORN_WS_PROTOCOL=websockets

# Create a non-root user in one layer
RUN groupadd -r appuser && useradd -r -g appuser -m -u 1000 -d /home/appuser -s /sbin/nologin appuser
USER appuser

WORKDIR /app

COPY uv.lock pyproject.toml /app/
RUN uv sync

# Copy application files in one layer
COPY aimakerspace/ /app/aimakerspace/
COPY api/ /app/api/

# Set up directories and copy frontend build files
RUN mkdir -p /app/logs /app/static/css /app/static/js && \
    chmod -R 777 /app/logs

COPY --from=frontend-builder /app/frontend/build/static/css/* /app/static/css/
COPY --from=frontend-builder /app/frontend/build/static/js/* /app/static/js/
COPY --from=frontend-builder /app/frontend/build/index.html /app/static/
COPY --from=frontend-builder /app/frontend/build/asset-manifest.json /app/static/

# Set ownership in one layer
RUN chown -R appuser:appuser /app/logs

# Set environment variables in one layer
ENV PYTHONPATH=/app \
    PORT=7860 \
    HOST=0.0.0.0 \
    LANGCHAIN_TRACING_V2=true \
    LANGSMITH_TRACING=true \
    LANGSMITH_PROJECT=pythonic-rag \
    LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Expose the Hugging Face required port
EXPOSE 7860

# Switch to non-root user
USER appuser

# Start the application
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]