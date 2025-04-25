Smart Campus Assistant
Description
Smart Campus Assistant is a web application designed to assist students and campus staff in navigating the campus easily and managing lost and found items. The project leverages AI and natural language processing (NLP) technologies to answer navigation questions (e.g., "Where is the Computer Science Department located on campus?") and incorporates an image recognition system to identify reported lost or found items.
The project consists of four main services:

frontend: User interface built with Angular, served via Nginx, which also acts as a reverse proxy for backend services.
navigation-bot: NLP processing service to answer navigation queries.
lost-and-found: Service to manage lost and found items, with image recognition via YOLOv5.
mongodb: MongoDB database to store lost and found data.

Tech Stack
AI/NLP (Offline & Self-hosted)

Language Model (LLM):

Uses transformers (Hugging Face) via HuggingFacePipeline from langchain.
Suggested models: LLaMA 2 or Mistral (local execution).
Dependencies:
transformers==4.41.2
langchain==0.2.5
langchain_community==0.2.5
torch==2.6.0




RAG (Retrieval-Augmented Generation):

Vector database: faiss-cpu==1.8.0 for storing and searching embeddings.
Embedding generation: sentence-transformers==3.0.1 with the all-MiniLM-L6-v2 model.



Image Recognition (Lost-and-Found)

Uses YOLOv5 for image recognition.
Dependencies:
torch==2.6.0



Backend

Framework: FastAPI (fastapi==0.111.0) with Uvicorn (uvicorn==0.30.1).
Database: MongoDB (mongo:latest from Docker Hub, copied to ghcr.io/<your-username>/mongo:latest during CI/CD).
Language: Python 3.10 (base image python:3.10-bullseye for navigation-bot, python:3.11-slim for lost-and-found).

Frontend

Framework: Angular (compiled via Node.js node:20).
Web Server: Nginx (nginx:1.25) to serve the Angular app and proxy requests to backend services.

Prerequisites

Docker and Docker Compose installed on your machine.
Available ports: 8080 (frontend), 8001 (navigation-bot), 8002 (lost-and-found), 27017 (mongodb).
Internet access for initial dependency and image downloads (the project runs offline after setup).
A GitHub account with a personal access token (for GHCR) and an Azure account (for ACI deployment).

Installation and Setup
1. Clone the Project
git clone <project-URL>
cd smart-campus-assistant

2. Configure Files
backend/navigation-bot/Dockerfile
FROM python:3.10-bullseye

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy the entire project
COPY . .

# Generate embeddings and FAISS index inside the container
RUN python embeddings.py

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

backend/navigation-bot/requirements.txt
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.4
faiss-cpu==1.8.0
numpy==1.26.4
sentence-transformers==3.0.1
langchain==0.2.5
langchain_community==0.2.5
transformers==4.41.2
huggingface-hub==0.23.4
torch==2.6.0
pytest==8.3.3

backend/lost-and-found/requirements.txt
fastapi==0.111.0
uvicorn==0.30.1
pymongo==4.6.1
torch==2.6.0
pytest==8.3.3

frontend/Dockerfile
Ensure the Dockerfile for the frontend handles both local and Azure environments:
# Stage 1: Build the Angular application
FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build --prod

# Stage 2: Set up NGINX to serve the application
FROM nginx:1.25
COPY --from=build /app/dist/smart-campus-frontend /usr/share/nginx/html

# Set default environment variable
ARG ENV=prod
COPY nginx.conf /etc/nginx/nginx.conf.prod
COPY nginx.conf.local /etc/nginx/nginx.conf.local

# Copy the appropriate NGINX config based on the environment
RUN if [ "$ENV" = "local" ]; then \
    cp /etc/nginx/nginx.conf.local /etc/nginx/nginx.conf; \
    else \
    cp /etc/nginx/nginx.conf.prod /etc/nginx/nginx.conf; \
    fi

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

frontend/nginx.conf (for Azure)
NGINX configuration for deployment on Azure, using static FQDNs:
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name localhost;
        client_max_body_size 100M;
        root /usr/share/nginx/html;
        index index.html index.htm;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /ask {
            proxy_pass http://navigationbot-static.francecentral.azurecontainer.io:8001/ask;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/lost-and-found/ {
            proxy_pass http://lostfound-static.francecentral.azurecontainer.io:8002/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /lost-and-found/data/ {
            proxy_pass http://lostfound-static.francecentral.azurecontainer.io:8002/data/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}

frontend/nginx.conf.local (for local execution)
NGINX configuration for local execution with Docker Compose, using service names:
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    resolver 127.0.0.11 valid=30s;

    server {
        listen 80;
        server_name localhost;
        client_max_body_size 100M;
        root /usr/share/nginx/html;
        index index.html index.htm;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /ask {
            set $upstream_navigation_bot http://navigation-bot:8001;
            proxy_pass $upstream_navigation_bot/ask;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/lost-and-found/ {
            set $upstream_lost_and_found http://lost-and-found:8002;
            proxy_pass $upstream_lost_and_found/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /lost-and-found/data/ {
            set $upstream_lost_and_found_data http://lost-and-found:8002;
            proxy_pass $upstream_lost_and_found_data/data/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}

docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      args:
        - ENV=local
    ports:
      - "8080:80"
    depends_on:
      - navigation-bot
      - lost-and-found
    networks:
      - app-network

  navigation-bot:
    build:
      context: ./backend/navigation-bot
    ports:
      - "8001:8001"
    networks:
      - app-network

  lost-and-found:
    build:
      context: ./backend/lost-and-found
    ports:
      - "8002:8002"
    volumes:
      - lost_and_found_data:/app/data
    depends_on:
      mongodb:
        condition: service_healthy
    environment:
      - MONGO_URI=mongodb://mongodb:27017
    networks:
      - app-network

  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test: ["CMD", "mongo", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

volumes:
  mongodb_data:
  lost_and_found_data:

networks:
  app-network:
    driver: bridge

3. Build and Start Services Locally
docker-compose up -d --build

4. Verify Services
docker ps

Expected output:
CONTAINER ID   IMAGE                             COMMAND                  STATUS                   PORTS                      NAMES
<container_id> smart-campus-assistant-frontend   "/docker-entrypoint.…"   Up                       0.0.0.0:8080->80/tcp       smart-campus-assistant-frontend-1
<container_id> smart-campus-assistant-navigation-bot  "uvicorn main:app --…"   Up                       0.0.0.0:8001->8001/tcp     smart-campus-assistant-navigation-bot-1
<container_id> smart-campus-assistant-lost-and-found  "uvicorn main:app --…"   Up                       0.0.0.0:8002->8002/tcp     smart-campus-assistant-lost-and-found-1
<container_id> mongo:latest                      "docker-entrypoint.s…"   Up (healthy)             0.0.0.0:27017->27017/tcp   smart-campus-assistant-mongodb-1

5. Access the Application Locally
Open your browser and go to:http://localhost:8080
Test the Application
1. User Interface (Frontend)

Navigation:
Click on "Home" (/).
Click on "Services" (/services).
Click on "About" (/about).



2. Navigation Bot

Go to the homepage (/).
Type a question (e.g., "Where is the Computer Science Department located on campus?").
Verify the response (e.g., "The location 'Computer Science Department' can be found here:").

Direct API Test
curl -X POST http://localhost:8001/ask \
-H "Content-Type: application/json" \
-d '{"query": "Where is the Computer Science Department located on campus?"}'

Note: For Azure deployment, update the CORS settings in backend/navigation-bot/main.py to allow requests from the Azure frontend URL:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:8080",
        "http://frontend-static.francecentral.azurecontainer.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

3. Lost-and-Found

Go to the /lost-and-found page.
Submit a lost item (e.g., description: "Black backpack").
Submit a found item (e.g., description: "Black backpack").
Check for matches.

Direct API Test

Report a lost item (e.g., water bottle):
curl -X POST http://localhost:8002/api/lost-and-found/ \
-H "Content-Type: application/json" \
-d '{
  "item_type": "water bottle",
  "description": "Blue reusable water bottle, 500ml, with a black cap",
  "location": "Gymnasium near the weight room",
  "date_lost": "2025-04-23",
  "status": "lost",
  "contact_info": "sarah.connor@example.com"
}'


Verify entries in MongoDB:
docker exec -it smart-campus-assistant-mongodb-1 mongosh

Then:
use lost_and_found_db
db.items.find()



CI/CD with GitHub Actions
1. CI/CD Workflow

File: .github/workflows/ci-cd.yml
Trigger: On push or pull request to the main branch.
Steps:
Build and Push Images:
Builds Docker images for frontend, navigation-bot, and lost-and-found.
Pulls the mongo:latest image from Docker Hub and pushes it to GitHub Container Registry (GHCR) as ghcr.io/<your-username>/mongo:latest.
Pushes all images to GHCR.


Deploy to Azure Container Instances (ACI):
Deploys services to ACI with static FQDNs:
Frontend: http://frontend-static.francecentral.azurecontainer.io
Navigation-bot: http://navigationbot-static.francecentral.azurecontainer.io:8001
Lost-and-found: http://lostfound-static.francecentral.azurecontainer.io:8002
MongoDB: mongodb://mongodb-static.francecentral.azurecontainer.io:27017



Suggested Improvement: Add Unit Tests
To ensure the services are functional before deployment, add a testing step in the docker-build-push job:
- name: 🧪 Run unit tests for navigation-bot
  run: |
    docker build -t navigation-bot-test ./backend/navigation-bot
    docker run --rm navigation-bot-test pytest tests/
- name: 🧪 Run unit tests for lost-and-found
  run: |
    docker build -t lost-and-found-test ./backend/lost-and-found
    docker run --rm lost-and-found-test pytest tests/

Add these steps before the "Build and push" steps to catch issues early.
2. Configuration of Secrets
In GitHub, add the following secrets under Settings > Secrets and variables > Actions:

GHCR_TOKEN: GitHub token with read:packages and write:packages permissions.
AZURE_CREDENTIALS: Azure credentials for ACI deployment (JSON format).
DOCKERHUB_USERNAME: Your Docker Hub username.
DOCKERHUB_TOKEN: Your Docker Hub access token (to avoid rate limits when pulling mongo:latest).

3. Access the Application on Azure
After deployment via the CI/CD pipeline, access the application at:http://frontend-static.francecentral.azurecontainer.io
Test APIs on Azure

Navigation-bot:curl -X POST http://frontend-static.francecentral.azurecontainer.io/ask \
-H "Content-Type: application/json" \
-d '{"query": "Where is the Computer Science Department located on campus?"}'


Lost-and-Found:curl -X POST http://frontend-static.francecentral.azurecontainer.io/api/lost-and-found/ \
-H "Content-Type: application/json" \
-d '{
  "description": "Blue reusable water bottle, 500ml, with a black cap",
  "location": "Gymnasium near the weight room",
  "date_lost": "2025-04-23",
  "status": "lost",
  "contact_info": "exemple@example.com"
}'



DevOps
1. Containerization with Docker

Each service is containerized to ensure consistent execution.
Dockerfiles automate dependency installation:
frontend/Dockerfile: Builds the Angular app and configures Nginx with two config files (nginx.conf and nginx.conf.local).
navigation-bot/Dockerfile: Installs Python dependencies, pre-downloads the all-MiniLM-L6-v2 model, and generates FAISS embeddings using embeddings.py.
lost-and-found/Dockerfile: Configures permissions for the data volume and installs dependencies.



2. Orchestration with Docker Compose

docker-compose.yml orchestrates the services:
Network: Custom app-network for inter-service communication.
Dependencies: Uses depends_on with condition: service_healthy for MongoDB.
Volumes: Persists data with mongodb_data and lost_and_found_data.



3. Reverse Proxy with Nginx

Nginx in the frontend service:
Serves the Angular app.
Proxies requests to navigation-bot (/ask) and lost-and-found (/api/lost-and-found/).


Two NGINX configurations:
nginx.conf: Uses static FQDNs for Azure.
nginx.conf.local: Uses Docker service names for local execution.



4. Monitoring and Service Health

Healthcheck for MongoDB:healthcheck:
  test: ["CMD", "mongo", "--eval", "db.adminCommand('ping')"]
  interval: 10s
  timeout: 5s
  retries: 5



5. Error Handling

Logs:
docker-compose logs <service> for local errors.
az container logs --resource-group smart-campus-rg --name <container> for ACI.


Container Status:
Local: docker ps -a.
ACI: az container show --resource-group smart-campus-rg --name <container> --query provisioningState --output tsv.

Future Improvements

Event Calendar: Stay updated with all campus events, activities, and important dates by integrating an event management system with real-time updates and notifications.
Campus Map: Add an interactive map with real-time navigation to help users find their way around campus, potentially integrating with the navigation-bot service for enhanced location-based queries.
Integrate Ollama to simplify LLM deployment.
Optimize FAISS for larger vector databases.
Add an admin interface for lost-and-found.
Add integration tests for APIs.
Integrate CI/CD monitoring with notifications (e.g., Slack).

Contributing

Fork the project.
Create a branch (git checkout -b feature/new-feature).
Commit your changes (git commit -m "Add new feature").
Push to your branch (git push origin feature/new-feature).
Create a Pull Request.


