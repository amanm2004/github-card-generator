FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy the rest of the source code
COPY . .

# Cloud Run expects port 8080
EXPOSE 8080

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
