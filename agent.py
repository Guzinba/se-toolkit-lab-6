"""
Documentation Agent CLI - Task 2
Answers questions using LLM with tool calling (read_file, list_files).
"""

import json
import os
import sys
import argparse
import re
from pathlib import Path
from typing import Optional

try:
    import httpx
except ImportError:
    print("Error: httpx required. Install: uv add httpx", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.resolve()
MAX_TOOL_CALLS = 10
DEFAULT_TIMEOUT = 60


# =============================================================================
# Tool Definitions
# =============================================================================

def get_tool_schemas() -> list[dict]:
    """Return OpenAI-compatible function schemas."""
    return [
        {
            "name": "read_file",
            "description": "Read content of a file from the project",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root"
                    }
                },
                "required": ["path"],
                "additionalProperties": False
            }
        },
        {
            "name": "list_files",
            "description": "List files and directories at a path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root"
                    }
                },
                "required": ["path"],
                "additionalProperties": False
            }
        }
    ]


def _validate_path(path_str: str) -> Path:
    """Validate path stays within PROJECT_ROOT."""
    clean_path = path_str.strip().lstrip('/')
    resolved = (PROJECT_ROOT / clean_path).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError:
        raise ValueError(f"Path traversal detected: '{path_str}'")
    return resolved


def read_file(path: str) -> str:
    """Read file content."""
    try:
        file_path = _validate_path(path)
        if not file_path.is_file():
            return f"Error: File not found: {path}"
        return file_path.read_text(encoding="utf-8")
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def list_files(path: str) -> str:
    """List directory contents."""
    try:
        dir_path = _validate_path(path)
        if not dir_path.is_dir():
            return f"Error: Not a directory: {path}"
        entries = []
        for entry in sorted(dir_path.iterdir()):
            suffix = "/" if entry.is_dir() else ""
            entries.append(f"{entry.name}{suffix}")
        return "\n".join(entries)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


TOOLS = {"read_file": read_file, "list_files": list_files}


# =============================================================================
# LLM Communication
# =============================================================================

def load_env_file(filepath: str) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    path = Path(filepath)
    if not path.exists():
        return env_vars
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars


def call_llm(messages: list[dict], config: dict, tools: Optional[list[dict]] = None) -> dict:
    """Send request to LLM API."""
    api_base = config.get("LLM_API_BASE", "http://localhost:42005/v1")
    api_key = config.get("LLM_API_KEY", "")
    model = config.get("LLM_MODEL", "qwen3-coder-plus")
    timeout = int(config.get("LLM_TIMEOUT", str(DEFAULT_TIMEOUT)))
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "messages": messages, "temperature": 0.1, "max_tokens": 1000}
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    url = f"{api_base}/chat/completions"
    
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


# =============================================================================
# Agent Loop
# =============================================================================

def run_agent_loop(question: str, config: dict) -> dict:
    """Run agent loop with tool calling."""
    system_prompt = (
        "You are a documentation assistant. Answer questions using the project wiki. "
        "Use these tools:\n"
        "- list_files(path): List directory contents\n"
        "- read_file(path): Read file content\n\n"
        "Rules:\n"
        "1. Explore wiki/ directory with list_files if needed\n"
        "2. Use read_file to get content from specific files\n"
        "3. Cite source as: wiki/filename.md#section-anchor\n"
        "4. Return answer in JSON format"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    tool_schemas = get_tool_schemas()
    tool_calls_log = []
    
    for iteration in range(MAX_TOOL_CALLS):
        try:
            response = call_llm(messages, config, tools=tool_schemas)
        except Exception as e:
            return {"answer": f"Error: LLM call failed: {e}", "source": "", "tool_calls": tool_calls_log}
        
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call.get("function", {}).get("name")
                tool_args_str = tool_call.get("function", {}).get("arguments", "{}")
                
                try:
                    tool_args = json.loads(tool_args_str) if isinstance(tool_args_str, str) else tool_args_str
                except json.JSONDecodeError:
                    tool_args = {}
                
                if tool_name in TOOLS:
                    try:
                        result = TOOLS[tool_name](**tool_args)
                    except Exception as e:
                        result = f"Error: {type(e).__name__}: {e}"
                else:
                    result = f"Error: Unknown tool '{tool_name}'"
                
                tool_calls_log.append({"tool": tool_name, "args": tool_args, "result": result})
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "content": result,
                    "name": tool_name
                })
            continue
        else:
            answer = message.get("content", "")
            source = ""
            match = re.search(r'(wiki/[\w\-/]+\.md(?:#[\w\-]+)?)', answer)
            if match:
                source = match.group(1)
            
            return {"answer": answer.strip(), "source": source, "tool_calls": tool_calls_log}
    
    return {"answer": "Error: Max tool calls reached", "source": "", "tool_calls": tool_calls_log}


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Documentation Agent CLI")
    parser.add_argument("question", type=str, help="Question to ask")
    args = parser.parse_args()
    
    config = load_env_file(".env.agent.secret")
    result = run_agent_loop(args.question, config)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
