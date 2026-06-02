In this final task, you'll complete the implementation of a local CI/CD pipeline. 
It builds on the Docker setup from the previous task and extends it to automate the build, test, and deployment process.

## **Implementation details**

### **The CI/CD script `local-ci-cd.sh`**

The script performs the following steps:

1. Gets the current Git commit SHA for image tagging  
2. Builds the Docker image using Docker Compose  
3. Runs unit tests inside the Docker container  
4. Deploys the application locally if on the main branch

### **The Docker Compose configuration `docker-compose.ci.yml`**

This file defines the service configuration for the CI/CD pipeline, including:

* Building the Docker image  
* Tagging the image with the commit SHA  
* Setting up port mapping and environment variables

### **The Python wrapper `task.py`**

The `CICDBuilder` class provides a Python interface for executing the CI/CD pipeline:

* Makes the CI/CD script executable  
* Executes the script and captures the output  
* Returns a success flag and the output

## **Task**

1. Review the CI/CD implementation files: `local-ci-cd.sh`, `docker-compose.ci.yml`, and `task.py`.  
2. Understand the stages defined in [./local-ci-cd.sh](file://AIinDevOps/CICD/local-ci-cd.sh) (Build, Test, Deploy).  
3. Run the pipeline using the `CICDBuilder` class in [task.py](file://AIinDevOps/CICD/task.py).  
4. Fix the `local-ci-cd.sh` script to pass the test check.  
<div class="hint">
  Do not forget to copy file `.env` to the folder CICD.
</div>
<div class="hint">
Make sure you have Docker and Git installed on your machine before running the CI/CD pipeline.
</div>
