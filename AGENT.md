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
# Documentation Agent CLI

## Overview
`agent.py` answers questions using LLM with tool calling (`read_file`, `list_files`).

## Setup
```bash
cp .env.agent.example .env.agent.secret
uv sync
