FROM python:3.13

WORKDIR /app

# Copy the Python codebase
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the aimakerspace directory
COPY aimakerspace/ /app/aimakerspace/

# Copy the API files and static files
COPY api/ /app/

# Make sure static directory exists
RUN mkdir -p /app/static

# Set environment variables
ENV PYTHONPATH=/app

# Expose the application port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]