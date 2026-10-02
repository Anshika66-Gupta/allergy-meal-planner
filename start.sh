#!/bin/bash
set -e

echo "🚀 Starting local Ollama server in background..."
ollama serve &

echo "⏳ Waiting for Ollama server to become ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 2
done

echo "✅ Ollama server is active!"

MODEL=${OLLAMA_MODEL:-"gemma3:1b"}
echo "📦 Pulling Ollama model '$MODEL'..."
ollama pull "$MODEL" || echo "⚠️ Model pull notice: Continuing with available models."

echo "🌟 Starting Streamlit web server on port ${PORT:-8501}..."
exec streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0
