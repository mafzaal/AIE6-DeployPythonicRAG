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

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser -s /sbin/nologin appuser

# Copy the Python codebase
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the aimakerspace directory
COPY aimakerspace/ /app/aimakerspace/

# Copy the API files
COPY api/ /app/api/

# Create logs directory
RUN mkdir -p /app/logs

# Create static directory and fix structure (move nested static content up)
RUN mkdir -p /app/static/css /app/static/js
COPY --from=frontend-builder /app/frontend/build/static/css/* /app/static/css/
COPY --from=frontend-builder /app/frontend/build/static/js/* /app/static/js/
COPY --from=frontend-builder /app/frontend/build/index.html /app/static/
COPY --from=frontend-builder /app/frontend/build/asset-manifest.json /app/static/

# Debugging: list static directory contents
RUN ls -la /app/static/ /app/static/css/ /app/static/js/

# Set ownership and permissions
RUN chown -R appuser:appuser /app/logs && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=7860
ENV HOST=0.0.0.0

# Expose the Hugging Face required port
EXPOSE 7860

# Switch to non-root user
USER appuser

# Start the application with the correct path
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]