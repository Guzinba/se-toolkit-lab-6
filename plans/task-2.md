# Task 2 Plan: Documentation Agent

## Tool Schemas

### read_file
- **Parameters:** `path` (string) — relative path from project root
- **Returns:** File content or error message
- **Security:** Reject paths outside project root (no ../ traversal)

### list_files
- **Parameters:** `path` (string) — relative directory path
- **Returns:** Newline-separated list of files/directories
- **Security:** Same path validation as read_file

## Agent Loop
1. Send question + tool schemas to LLM
2. If `tool_calls` in response → execute tools, add results, repeat (max 10 iterations)
3. If text response → extract answer + source, return JSON

## Output Format
```json
{
  "answer": "string",
  "source": "wiki/file.md#anchor",
  "tool_calls": [{"tool": "...", "args": {}, "result": "..."}]
}
