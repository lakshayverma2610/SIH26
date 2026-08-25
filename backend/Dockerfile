FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for ML packages (libgomp for Treelite/LightGBM)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire workspace necessary for the backend (backend, ai_engine, graph_db)
COPY backend /app/backend
COPY ai_engine /app/ai_engine
COPY graph_db /app/graph_db
COPY data_engine /app/data_engine

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
