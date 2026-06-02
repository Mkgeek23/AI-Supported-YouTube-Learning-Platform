#!/bin/bash
  set -e

  # Define variables
  export COMMIT_SHA=$(git rev-parse --short HEAD)

  echo "=== Starting Local CI/CD Pipeline ==="
  echo "Using commit: $COMMIT_SHA"

  # Build stage
  echo -e "\n=== STAGE: Build ==="
  docker-compose -f docker-compose.ci.yml # TODO: call build command here

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

  echo -e "\n=== CI/CD Pipeline Completed Successfully ==="