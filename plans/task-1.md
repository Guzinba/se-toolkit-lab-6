# Task Plan 1: Basic CLI Agent

## Selecting a provider and model
- **Provider**: Qwen Code via a local proxy (`qwen-code-oai-proxy`)
- **Endpoint**: `http://localhost:42005/v1`
- **Model**: `qwen3-coder-plus`
- **Authentication**: Bearer token from `.env.agent.secret`

## Agent Architecture
## agent.py structure
1. Parsing command line arguments (question)
2. Loading configuration from `.env.agent.secret`
3. Forming a request to OpenAI-compatible API
4. Sending a POST request with a timeout of 60 seconds
5. Parsing the response, extracting `content`
6. Forming JSON: `{"response": "...", "tool_calls": []}`
7. Output to stdout, logs to stderr

## Error handling
- Network errors → output to stderr, exit code 1
- Timeout → output to stderr, exit code 1
- Invalid response from LLM → output to stderr, exit code 1

## Testing
- One regression test: running agent.py, checking JSON in stdout
