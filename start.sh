#!/bin/bash

PORT="${PORT:-8501}"
MODEL="${OLLAMA_MODEL:-gemma3:1b}"

echo "🥗 Starting Allergy-Safe Meal Planner..."

if command -v ollama >/dev/null 2>&1; then
    echo "🚀 Starting local Ollama daemon in background..."
    ollama serve >/dev/null 2>&1 &
    
    # Quick non-blocking wait for Ollama ready (max 6 seconds)
    WAIT_COUNT=0
    while [ $WAIT_COUNT -lt 3 ]; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            echo "✅ Ollama daemon is active!"
            break
        fi
        sleep 2
        WAIT_COUNT=$((WAIT_COUNT + 1))
    done

    # Pull model asynchronously in background so web server starts immediately without Render port-check timeouts
    if [ -n "$MODEL" ]; then
        echo "📦 Initiating background model pull for '$MODEL'..."
        (
            ollama pull "$MODEL" >/dev/null 2>&1 && echo "✅ Model '$MODEL' ready!" || echo "ℹ️ Running with existing models."
        ) &
    fi
else
    echo "💡 Local Ollama CLI not detected. Running seamlessly with Cloud Smart Safety Engine."
fi

echo "🌟 Starting Streamlit server on port $PORT..."
exec streamlit run app.py --server.port="$PORT" --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false
