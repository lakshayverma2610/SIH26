FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for ML packages (libgomp for Treelite/LightGBM)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire workspace necessary for the backend
COPY backend /app/backend
COPY ml_inference /app/ml_inference
COPY geospatial_engine /app/geospatial_engine
COPY data_simulation /app/data_simulation

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.api_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
