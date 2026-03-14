# Agent: CLI interface to LLM

## Overview
`agent.py` is a command line that takes a user question, sends it to a large language model via an OpenAI-compatible API, and returns a structured response in JSON format.

## Requirements
- Python 3.10+
- `uv` for dependency management
- Access to LLM via API (default: local Qwen Code proxy)

## Configuration

### 1. Running the proxy (if using local Qwen)
```bash
cd ~/qwen-code-oai-proxy
docker compose up -d
