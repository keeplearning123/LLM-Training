# Shared Local LLM Environment (Ollama & Continue)

This repository provides a standardized, automated local AI assistant setup for IntelliJ using **Docker Compose** and the **Continue** plugin. It automatically provisions Ollama and pulls all required models (`llama3.2:1b`, `qwen2.5-coder:7b`, and `deepseek-r1:8b`) without manual terminal intervention.

---

## 💻 System Prerequisites

Because LLMs run entirely on your local machine, your hardware must meet these minimums:
*   **Docker Desktop**: Installed and running.
*   **System RAM**: Minimum **16 GB RAM** recommended to support the 7B and 8B models concurrently.
*   **Python**: Version 3.8 or higher installed locally to run evaluation scripts.

---

## 🚀 Quick Start (Team Onboarding)

### 1. Start the Local AI Stack
Clone this repository, navigate to the directory, and run the following command in your terminal:
```bash
docker compose up -d
```
*Note: The initial launch will take several minutes because Docker will automatically pull the Ollama image and download all three models in the background.*

---

## 🏃‍♂️ Step 2: Run the Optimization & Evaluation Demo

Once your containers are fully up and running, you can execute a test validation script to evaluate how different hyper-parameters impact model outputs.

### A. Install Python Dependencies
Before running the script, ensure you have the required packages installed locally:
```bash
pip install ollama requests
```

### B. Execute the Demo Script
Run the evaluation matrix directly from your terminal:
```bash
python /Users/gs/IdeaProjects/LLM-Training/local-llm/demo1.py \
  --temperatures 0.0,0.2 \
  --top-p 0.8,1.0 \
  --top-k 1,5
```

### 🎛️ Parameters Explained
*   **`--temperatures`**: Controls creativity. Lower values (like `0.0`) yield strict, deterministic answers, while higher values allow variation.
*   **`--top-p`**: Controls nucleus sampling diversity.
*   **`--top-k`**: Restricts the model's vocabulary choices to the top *K* highest-probability tokens.
*   **Need More Options?** Additional configurations, flags, and benchmarking logic can be found and altered directly within the codebase of `demo1.py`.

### 📊 Viewing Benchmarking Output
After execution, the script evaluates model performance across your specified parameter combinations. Output metrics and comparative CSV logs are generated inside the workspace directory of your `LLM-Training` project for analysis.

---

## 🧩 Step 3: Install Continue in IntelliJ

1. Open **IntelliJ IDEA**.
2. Go to **Settings** (or **Preferences** on macOS) > **Plugins**.
3. Search the Marketplace for **Continue** and click **Install**.

---

## ⚙️ Step 4: Apply the Team Configuration

1. Open your local Continue configuration file located at `~/.continue/config.yaml`.
2. Replace its contents with the entire contents of the `config.yaml` file provided in the root of this repository.
3. If the models do not appear in the bottom-left dropdown of your Continue sidebar, click the **Reload Config** button inside the plugin interface.

---

## 🛠️ Repository Configuration Files

### `docker-compose.yml`
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-local-ai
    ports:
      - "11434:11434"
    volumes:
      - ollama_storage:/root/.ollama
      - ./entrypoint.sh:/entrypoint.sh
    entrypoint: ["/bin/sh", "/entrypoint.sh"]
    restart: unless-stopped

volumes:
  ollama_storage:
```

### `entrypoint.sh`
```bash
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
```

### `config.yaml` (For `~/.continue/config.yaml`)
```yaml
version: 1.0.0
schema: v1
models:
  - name: Llama 3.2 1B
    provider: ollama
    model: llama3.2:1b
    roles:
      - chat
      - edit
      - apply

  - name: Qwen2.5-Coder 7B
    provider: ollama
    model: qwen2.5-coder:7b
    roles:
      - chat
      - autocomplete

  - name: DeepSeek R1 8B
    provider: ollama
    model: deepseek-r1:8b
    roles:
      - chat
      - embed
```
