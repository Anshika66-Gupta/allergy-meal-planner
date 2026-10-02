# Use official slim Python base image
FROM python:3.11-slim

# Install system dependencies & curl for Ollama installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy python dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Copy entrypoint script and set permissions
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Environment defaults
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV OLLAMA_MODEL=gemma3:1b

EXPOSE 8501

ENTRYPOINT ["/start.sh"]
