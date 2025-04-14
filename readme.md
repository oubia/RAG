# Project Setup and Execution Guide

---

## **Introduction**
This guide provides instructions to set up and run the project using Ollama stored large language models, a Python backend, and a frontend. Follow the steps to configure and execute the project successfully.

---

## **Prerequisites**

Ensure the following tools are installed:

1. **Python 3.8+**: Download from [Python.org](https://www.python.org/downloads/).
2. **pip**: Python package manager (included with Python installations).
3. **AWS CLI**: [Install and configure AWS CLI](https://aws.amazon.com/cli/).
4. **Node.js and npm**: Download and install from [Node.js official website](https://nodejs.org/).

---

## **Setup Instructions**

### **1. Clone the Repository**
Use the following commands to clone the project repository and navigate into the project directory:

```bash
git clone repo_link
cd RAG
git checkout your-branch-or-main
```
---
# Setting Up a Python Virtual Environment

This guide provides step-by-step instructions on how to create and activate a Python virtual environment. Virtual environments are essential for managing package versions and ensuring that different projects can run in isolated settings without interfering with each other.

## Prerequisites

- Python 3.x installed on your machine. You can download Python from [python.org](https://www.python.org/downloads/).

## Creating a Virtual Environment

1. **Open your terminal or command prompt**.
2. **Navigate to your project directory** where you want the virtual environment to be set up.

    ```bash
    cd path/to/your/RAG
    ```

3. **Create the virtual environment**:
    - For **Windows**:
    
    ```bash
    python -m venv env
    ```

    - For **macOS and Linux**:
    
    ```bash
    python3 -m venv env
    ```

    This command will create a new directory called `env` within your project directory, where the virtual environment files will be stored.
---

## Activating the Virtual Environment

Once you have created a virtual environment, you need to activate it to use it.

- **On Windows**:

    ```bash
    .\env\Scripts\activate
    ```

- **On macOS and Linux**:

    ```bash
    source env/bin/activate
    ```

---

## Running The project
In order to run the project, it is obligatory to create an AWS Endpoint for the LLM to work on the `sagemaker` platform.

After that, it is necessary to log into the `AWS` Profile.

``` bash

pip install -r requirements.txt
```
---

## Run The platform
To run the platform it is necessary to run the following command:

### Run the Backend

```bash
uvicorn main:app --reload
```
### Prepare the Frontend
```bash
cd frontend
npm install
npm start
```

## Deactivating the Virtual Environment

To stop using the virtual environment and return to your global Python environment, you can deactivate it by running:

```bash
deactivate
```
# Test APIs

```bash
curl -X POST http://host.docker.internal:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "prompt": "Your prompt here",
    "temperature": 0.5,
    "max_tokens": 100
}'

```

```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "prompt": "Your prompt here",
    "temperature": 0.5,
    "max_tokens": 100
}'

```

# Test embedding:

```bash
curl -X POST http://host.docker.internal:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text:latest",
    "text": "Test input for embeddings"
}'

```
```bash
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text:latest",

}'

```