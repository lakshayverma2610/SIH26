# 🛡️ Geo-CashWatch (SIH 26184)
> **Predictive Analytics & Geospatial Framework for Cybercrime Mule Network Detection & ATM Cash-Out Interception**

Developed for **Smart India Hackathon (SIH 26184)** — Ministry of Home Affairs (I4C).

---

## 📖 Complete Documentation
For the full end-to-end architecture, data flow pipeline, and testing instructions, read the comprehensive guide:
👉 **[WORKFLOW_END_TO_END.md](WORKFLOW_END_TO_END.md)**

---

## 🚀 Quick Start (Kubernetes & Docker Only)

> **Note:** This application requires a Kubernetes cluster (e.g., Minikube, Docker Desktop K8s, or a cloud provider) and does not support local terminal execution.

### 1. Build the Docker Images
```bash
# Build Backend Image
docker build -t geo-cashwatch-backend:latest ./backend

# Build Frontend Image
docker build -t geo-cashwatch-frontend:latest ./frontend
```

### 2. Deploy Enterprise Infrastructure (Postgres, Redis, Kafka)
```bash
# 1. Deploy Persistent Relational Database (PostgreSQL)
kubectl apply -f k8s/postgres-deployment.yaml

# 2. Deploy In-Memory Datastore & Geospatial Cache (Redis)
kubectl apply -f k8s/redis-deployment.yaml

# 3. Deploy Event Streaming Broker (Apache Kafka)
kubectl apply -f k8s/kafka-cluster.yaml
```

### 3. Deploy Application Gateway & Async Huey Workers
```bash
# Deploy Huey Background Task Workers (ERSS 112 & CFCFRMS 1930)
kubectl apply -f k8s/huey-worker-deployment.yaml

# Deploy Core FastAPI Gateway
kubectl apply -f k8s/backend-deployment.yaml

# Deploy React Command Center Dashboard
kubectl apply -f k8s/frontend-deployment.yaml
```

### 4. (Optional) Seed Redis Database
To seed 5,000 enterprise account profiles and 1,500 ATM geospatial coordinates into Redis:
```bash
kubectl run -i --tty redis-seeder --image=geo-cashwatch-backend:latest --restart=Never --env="REDIS_URL=redis://redis:6379/0" -- python data_simulation/seed_redis.py
```

### 5. Access the Dashboard
Wait for the pods to initialize, then forward the ports:
```bash
kubectl port-forward svc/frontend-service 5173:80
```
Access the dashboard at `http://localhost:5173`.

### 6. Launch Live Real-Time Simulator
To inject attacks, run the simulator inside a Kubernetes Job or a temporary debug pod that has access to the internal Kafka network:
```bash
kubectl run -i --tty simulator-pod --image=geo-cashwatch-backend:latest --restart=Never -- python data_simulation/kafka_producer.py
```
