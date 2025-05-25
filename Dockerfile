# Dockerfile

# 1. Use an official Python runtime as a parent image
FROM python:3.9-slim

# 2. Set environment variables
# Prevents Python from writing pyc files to disc (equivalent to python -B)
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory in the container
WORKDIR /app

# 4. Install system dependencies (if any are needed in the future, e.g., for specific libraries)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements.txt and install Python dependencies
# Copy requirements first to leverage Docker cache if requirements haven't changed
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code into the working directory
# This includes 'api', 'cacm_adk_core', 'static', 'config', 'cacm_library', 
# 'cacm_standard', 'ontology', 'examples', 'scripts' directories.
COPY . .

# 7. Expose the port the app runs on
EXPOSE 8000

# 8. Define the command to run the application
# This command assumes uvicorn is listed in requirements.txt
# It runs the FastAPI application defined in api/main.py, accessible from outside the container.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
