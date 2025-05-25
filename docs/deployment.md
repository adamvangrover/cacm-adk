# CACM-ADK Deployment Guide

This guide provides instructions for deploying and running the CACM Authoring & Development Kit (ADK) application.

## Using Docker (Recommended)

Docker provides a containerized environment for running the application with all its dependencies.

### 1. Building the Docker Image

From the project root directory (where the `Dockerfile` is located), run the following command to build the Docker image:

```bash
docker build -t cacm-adk-app:latest .
```
This will create an image named `cacm-adk-app` with the tag `latest`.

### 2. Running the Docker Container

Once the image is built, you can run it as a container:

```bash
docker run -d -p 8000:8000 --name cacm-adk-instance cacm-adk-app:latest
```
Breakdown of the command:
*   `-d`: Runs the container in detached mode (in the background).
*   `-p 8000:8000`: Maps port 8000 of the host machine to port 8000 of the container (where the FastAPI application runs).
*   `--name cacm-adk-instance`: Assigns a name to the running container for easier management.
*   `cacm-adk-app:latest`: Specifies the image to run.

### 3. Accessing the Application

Once the container is running, the application can be accessed via the following URLs:

*   **API Base URL:** `http://localhost:8000`
*   **Interactive API Docs (Swagger UI):** `http://localhost:8000/docs`
*   **ReDoc API Docs:** `http://localhost:8000/redoc`
*   **Landing Page:** `http://localhost:8000/`

### 4. Stopping and Removing the Container

To stop the running container:
```bash
docker stop cacm-adk-instance
```

To remove the stopped container (if you want to free up the name or clean up):
```bash
docker rm cacm-adk-instance
```

## Running without Docker (for Development)

For development purposes, you can run the FastAPI application directly using Uvicorn.

### Prerequisites:

1.  Ensure you have Python installed (e.g., Python 3.9+).
2.  It's highly recommended to use a virtual environment.
3.  All dependencies must be installed from `requirements.txt`.

### Steps:

1.  **Navigate to the project root directory.**
2.  **Create and activate a virtual environment (if not already done):**
    ```bash
    python -m venv .venv
    # On Windows: .venv\Scripts\activate
    # On macOS/Linux: source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the Uvicorn server:**
    ```bash
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
    ```
    Breakdown of the command:
    *   `uvicorn`: The ASGI server.
    *   `api.main:app`: Path to the FastAPI application instance (`app`) within the `api/main.py` file.
    *   `--reload`: Enables auto-reload when code changes are detected (useful for development).
    *   `--host 0.0.0.0`: Makes the server accessible from your local network (not just `localhost`).
    *   `--port 8000`: Specifies the port to run on.

The application will then be accessible at the same URLs listed in the Docker section (e.g., `http://localhost:8000/`).
