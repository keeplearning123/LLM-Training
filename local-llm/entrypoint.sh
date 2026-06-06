#!/bin/sh

# Start Ollama server in the background
ollama serve &

# Wait for the Ollama server to boot up safely
echo "Waiting for Ollama server to start..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 2
done

echo "Ollama server is active! Seeding models..."

# Automatically download models
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:8b

echo "🟢 All models loaded successfully! Container is ready."

# Keep the container alive by binding to the background process
wait