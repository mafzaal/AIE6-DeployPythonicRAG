# Running the RAG Chat Application in Docker

This document provides instructions for building and running the RAG Chat Application using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Building and Running the Application

1. Make sure you have a valid OpenAI API key in your `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
```

2. Build and run the application using Docker Compose:

```bash
docker-compose up --build
```

This command will:
- Build the frontend with the shadcn/ui components and Tailwind CSS
- Build the Python backend
- Start the application on port 8000

3. Access the application in your browser:

```
http://localhost:8000
```

## Stopping the Application

To stop the application, press `Ctrl+C` in the terminal where Docker Compose is running, or run:

```bash
docker-compose down
```

## Troubleshooting

If you encounter any issues:

1. Check the Docker logs for errors:
```bash
docker-compose logs
```

2. Make sure your `.env` file contains a valid OpenAI API key.

3. Ensure ports 8000 is available on your system.

4. If you make changes to the frontend code, you may need to rebuild the Docker image:
```bash
docker-compose up --build
``` 