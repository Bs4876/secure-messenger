FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Install system dependencies for cryptography and bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source
COPY . /app

# Expose port and provide a convenient default command for development
EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
