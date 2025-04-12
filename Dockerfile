FROM node:18 AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY app/frontend/package*.json ./

# Install dependencies and explicitly install tailwindcss v3
RUN npm install
RUN npm uninstall tailwindcss @tailwindcss/postcss && npm install tailwindcss@3.3.0 postcss autoprefixer --save-dev

# Copy frontend source files
COPY app/frontend/ ./

# Build the frontend
RUN npm run build
RUN ls -la build/

# Backend stage
FROM python:3.13

WORKDIR /app

# Copy the Python codebase
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the aimakerspace directory
COPY aimakerspace/ /app/aimakerspace/

# Copy the API files
COPY api/ /app/

# Create static directory and fix structure (move nested static content up)
RUN mkdir -p /app/static/css /app/static/js
COPY --from=frontend-builder /app/frontend/build/static/css/* /app/static/css/
COPY --from=frontend-builder /app/frontend/build/static/js/* /app/static/js/
COPY --from=frontend-builder /app/frontend/build/index.html /app/static/
COPY --from=frontend-builder /app/frontend/build/asset-manifest.json /app/static/

# Debugging: list static directory contents
RUN ls -la /app/static/ /app/static/css/ /app/static/js/

# Set environment variables
ENV PYTHONPATH=/app

# Expose the application port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]