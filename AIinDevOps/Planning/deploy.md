# Deployment Plan for YouTube Learning Platform

This document outlines the step-by-step process for deploying the YouTube Learning Platform to a production server using Docker and setting up CI/CD on Nebius cloud.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Docker Setup](#docker-setup)
3. [Local CI/CD Pipeline](#local-cicd-pipeline)
4. [(optional) Production Deployment](#optional-production-deployment)

## Prerequisites

Before starting the deployment process, ensure you have the following:

- Access to Nebius Cloud account
- Docker installed on your local development machine (https://docs.docker.com/desktop/)
- Git repository for the project
- Required API keys and credentials:
  - Nebius LLM API credentials
  - Any other service credentials used by the application

## Docker Setup

### 1. Create a Dockerfile

Create a Dockerfile in the root directory of the project:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Offload folder to load a large model in Docker
VOLUME ["/tmp/offload_folder"]

# Copy application code
COPY src .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=main.py \
    FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "999", "--graceful-timeout", "999", "main:app"]
```

### 2. Create a requirements.txt file

Create a requirements.txt file (just copy it from the project root) with all the dependencies of the project:

```
yt-dlp~=2025.1.15
Flask~=3.1.0
openai-whisper==20240930
torch~=2.5.1
transformers~=4.48.1

whisper~=1.1.10
openai~=1.60.2
python-dotenv~=1.0.1
accelerate>=0.26.0
pytest>=8.3.5
gunicorn==23.0.0
```

### 3. Create a .dockerignore file

Create a .dockerignore file to exclude unnecessary files:

```
.git
.gitignore
.pytest_cache
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
*.db
temp_audio.wav
```

### 4. Create a docker-compose.yml file

Create a docker-compose.yml file for local development and testing:

```yaml
services:
  app:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    restart: unless-stopped
```

### 5. Build and Test Docker Image Locally

```shell
  # Build the Docker image
  docker build -t youtube-learning-platform .

  # Run the container
  docker run -p 5000:5000 --env-file .env youtube-learning-platform

```

## Local CI/CD Pipeline

### 1. Create a `docker-compose.ci.yml` file:
```yaml
services:
  app:
    build: .
    image: youtube-learning-platform:${COMMIT_SHA:-latest}
    ports:
      - "5000:5000"
    env_file:
      - .env
    restart: unless-stopped
```

### 2. Create a CI/CD Shell Script

Create a file called `loal-ci-cd.sh` in your project root 
(On Windows use Windows Subsystem for Linux, WSL, for runnig it):

```bash
  #!/bin/bash
  set -e
  
  # Define variables
  export COMMIT_SHA=$(git rev-parse --short HEAD)
  
  echo "=== Starting Local CI/CD Pipeline ==="
  echo "Using commit: $COMMIT_SHA"
  
  # Build stage
  echo -e "\n=== STAGE: Build ==="
  docker-compose -f docker-compose.ci.yml build
  
  # Test stage
  echo -e "\n=== STAGE: Test ==="
  docker-compose -f docker-compose.ci.yml run --rm app python -m unittest discover
  
  # Deploy stage (local deployment)
  echo -e "\n=== STAGE: Deploy ==="
  if [ "$(git rev-parse --abbrev-ref HEAD)" == "main" ]; then
      echo "On main branch, deploying..."
      docker-compose -f docker-compose.ci.yml down || true
      docker-compose -f docker-compose.ci.yml up -d
      echo "Application deployed at http://localhost:5000"
  else
      echo "Not on main branch, skipping deployment"
  fi
  
  echo -e "\n=== CI/CD Pipeline Completed Successfully ==="```
```
Make the Script executable
```bash
  chmod +x local-ci-cd.sh
```

### (optional) 3. Using GitHub Actions Locally
If you prefer to use the same workflow syntax as GitHub Actions, 
you can use the [act](https://github.com/nektos/act) tool to run 
GitHub Actions workflows locally:
1. First, convert your CI/CD YAML to GitHub Actions format:
```yaml
name: Local CI/CD Pipeline

on: [push, workflow_dispatch]

jobs:
  build-test-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build -t youtube-learning-platform:${{ github.sha }} .
          docker tag youtube-learning-platform:${{ github.sha }} youtube-learning-platform:latest
      
      - name: Run tests
        run: |
          docker run --rm youtube-learning-platform:${{ github.sha }} python -m unittest discover
      
      - name: Deploy locally
        if: github.ref == 'refs/heads/main'
        run: |
          docker stop youtube-learning-platform 2>/dev/null || true
          docker rm youtube-learning-platform 2>/dev/null || true
          docker run -d --name youtube-learning-platform -p 5000:5000 --env-file .env youtube-learning-platform:latest
```
2. Save this as `.github/workflows/local-ci-cd.yml`
3. Install and run [act](https://github.com/nektos/act) to execute the workflow locally:
```bash
  # Install act (macOS)
  brew install act
  # Run the workflow
  act
```

## (optional) Production Deployment

### 1. Set Up Nebius Container Registry

1.1. Install `jq` ([how to install](https://jqlang.github.io/jq/download/)) 
which parses JSON outputs from the Nebius AI Cloud CLI and extracts resource IDs for other commands:
```shell
  brew install jq
```
Install the Nebius AI Cloud CLI ([how to install](https://docs.nebius.com/cli/install)) 
which manages all Nebius AI Cloud resources:

```shell
  curl -sSL https://storage.eu-north1.nebius.cloud/cli/install.sh | bash
```
To complete the installation, restart your terminal or run `exec -l $SHELL`.

Make sure that the installation is successful. Run:

```shell
  nebius version
```
In the output, you'll see the version number of your Nebius AI Cloud CLI.

1.2. Configure the Nebius AI Cloud CLI:

```shell
  nebius profile create
```
The last command, `nebius profile create`, will open the sign-in screen of the Nebius AI Cloud 
web console in your browser. Sign in to the web console to complete the initialization. 
After that, save your project ID in the CLI configuration:

Copy your project ID from the web console [Project settings](https://console.eu.nebius.com/settings/).

Add the project ID to the CLI configuration:
```shell
  nebius config set parent-id <project_ID>
```

1.3. Create a container registry in Nebius Cloud. Let's name it `youtube-learning-platform`:
```shell
  export NB_REGISTRY_PATH=$(nebius registry create \
  --name youtube-learning-platform \
  --format json | jq -r ".metadata.id" | cut -d- -f 2)
  echo $NB_REGISTRY_PATH
```
For existing container registry:
```shell
  export NB_REGISTRY_PATH=$(nebius registry list \
  --format json | jq -r '.items[0].metadata.id' | cut -d- -f 2)
  echo $NB_REGISTRY_PATH
```

Create an environment variable for the region in which your project is located:
```shell
  # Extract the region-id from the registry list output
  export NB_REGION_ID=$(nebius registry list | grep registry_fqdn | \
  sed -E 's/.*cr\.([^\.]+)\.nebius\.cloud.*/\1/')
  # Verify the extracted region-id
  echo "Region ID: $NB_REGION_ID"
```

1.4. Configure Docker to work with the created registry

Run the Nebius AI Cloud Docker credential helper. It lets you use Nebius AI Cloud registries 
without running the `docker login`.

```shell
  nebius registry configure-helper
```
Check that the credential helper is configured:
 - Open the file from the previous command output, for example, with the cat command:
```shell
  cat /Users/user/.docker/config.json
```
Check that the credHelpers property contains one of the following lines:
```
"cr.eu-north1.nebius.cloud": "nebius"
"cr.eu-west1.nebius.cloud": "nebius"
```

### 2. Initial Manual Deployment

For the first deployment, you can deploy manually:

```shell
  # Build and tag the Docker image
  docker build -t cr.$NB_REGION_ID.nebius.cloud/$NB_REGISTRY_PATH/youtube-learning-platform:initial .

  # Push the image to Nebius Container Registry
  docker push cr.$NB_REGION_ID.nebius.cloud/$NB_REGISTRY_PATH/youtube-learning-platform:initial
```
Now you are ready to run your app in a docker container anywhere!
The only thing you need is to get the public endpoint URL and configure Domain and HTTPS.
This is beyond the scope of this project but can be done with different cloud providers.
