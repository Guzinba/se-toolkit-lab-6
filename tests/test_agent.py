"""Regression tests for Documentation Agent (Task 2)."""

import json
import subprocess
import sys
from pathlib import Path


def run_agent(question: str) -> tuple[int, str, str]:
    """Run agent.py and return (returncode, stdout, stderr)."""
    project_root = Path(__file__).parent.parent
    cmd = ["uv", "run", str(project_root / "agent.py"), question]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=70)
    return result.returncode, result.stdout.strip(), result.stderr


def test_wiki_question_with_read_file():
    """Test: Question about wiki expects read_file in tool_calls."""
    returncode, stdout, stderr = run_agent("What files are in the wiki directory?")
    assert returncode == 0, f"Agent failed: {stderr}"
    
    output = json.loads(stdout)
    assert "answer" in output
    assert "source" in output
    assert "tool_calls" in output
    assert len(output["tool_calls"]) > 0, "Expected tool calls"
    
    tools_used = [c["tool"] for c in output["tool_calls"]]
    assert "list_files" in tools_used or "read_file" in tools_used, f"Expected list_files or read_file, got: {tools_used}"
    
    print("✓ test_wiki_question_with_read_file passed", file=sys.stderr)


def test_wiki_files_question_with_list_files():
    """Test: Question about files expects list_files in tool_calls."""
    returncode, stdout, stderr = run_agent("List all files in wiki")
    assert returncode == 0, f"Agent failed: {stderr}"
    
    output = json.loads(stdout)
    assert "answer" in output
    assert "tool_calls" in output
    assert len(output["tool_calls"]) > 0, "Expected tool calls"
    
    tools_used = [c["tool"] for c in output["tool_calls"]]
    assert "list_files" in tools_used, f"Expected list_files, got: {tools_used}"
    
    print("✓ test_wiki_files_question_with_list_files passed", file=sys.stderr)


if __name__ == "__main__":
    try:
        test_wiki_question_with_read_file()
        test_wiki_files_question_with_list_files()
        print("All tests passed!", file=sys.stderr)
        sys.exit(0)
    except AssertionError as e:
        print(f"Test failed: {e}", file=sys.stderr)
        sys.exit(1)
