import json
import os
import re

import httpx

from config import MODEL, OLLAMA_CHAT_URL
from tools import TOOLS

HOME = os.path.expanduser("~")

SYSTEM_PROMPT = f"""You are a local coding assistant running on the user's Ubuntu laptop.
The user's home directory is {HOME}.
Use bash to explore the filesystem when you need to find files or projects.

IMPORTANT: When the user asks you to do something, DO IT using the tools. Do not explain how to do it. Do not give examples. Just use the tool directly and report the result.

You have access to EXACTLY these four tools — use ONLY these names:
- bash: runs any shell command like ls, find, cat, mkdir, python3, cd. Input is the command string.
- read_file: reads a single file. Input is the file path string.
- write_file: writes to a file. Input is JSON: {{"path": "filepath", "content": "file content"}}
- search_files: searches text across files. Input is : "query|~/directory" for example "sankofa|~/sankofa"
- open_in_zed: opens a file in the Zed editor. Input is the file path string. Use this after writing or editing a file.
IMPORTANT RULE — there are ONLY 4 tools: bash, read_file, write_file, search_files.
Commands like ls, find, cat, grep, python3 are NOT tools.
They must go INSIDE the bash tool like this:

WRONG: {{"tool": "ls", "input": "/home/goodness"}}
WRONG: {{"tool": "find", "input": "/home/goodness"}}
RIGHT: {{"tool": "bash", "input": "ls /home/goodness"}}
RIGHT: {{"tool": "bash", "input": "find /home/goodness -type d"}}
CRITICAL: Each bash command runs in its own shell. cd does not persist between commands.
Always use full absolute paths. Never use cd alone.
WRONG: {{"tool": "bash", "input": "cd ~/sankofa"}}
RIGHT: {{"tool": "bash", "input": "ls /home/goodness/sankofa"}}

To use a tool respond with a json code block containing ONLY this and nothing else:
```json
{{"tool": "tool_name", "input": "tool_input"}}
```
The user has the projects on their laptop:
-/home/goodness/sankofa --- Sankofa System, a computational knowledge platform
-/home/goodness/agent --- Agent CLI
When you have a final answer respond with plain text.
Use one tool at a time. Act, do not explain."""


def call_model(messages: list) -> str:
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            OLLAMA_CHAT_URL,
            json={"model": MODEL, "messages": messages, "stream": False},
        )
    return response.json()["message"]["content"]


def parse_tool_call(text: str):
    for match in re.finditer(r"```\w*[ \t]*\n(.*?)\n```", text, re.DOTALL):
        json_str = match.group(1).strip()
        try:
            data = json.loads(json_str)
            if "tool" in data and "input" in data:
                return data
        except (json.JSONDecodeError, ValueError):
            pass
    try:
        data = json.loads(text.strip())
        if "tool" in data and "input" in data:
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def run_agent(user_message: str, history: list | None = None) -> str:
    if history is None:
        history = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    last_tool_call = None

    for iteration in range(10):
        print(f"\n--- Iteration {iteration + 1} ---")
        response_text = call_model(messages)
        print(f"Model said: {repr(response_text)}")
        messages.append({"role": "assistant", "content": response_text})

        tool_call = parse_tool_call(response_text)
        print(f"Tool call detected: {tool_call}")

        if tool_call is None:
            return response_text

        # Break if model is stuck repeating the same call
        if tool_call == last_tool_call:
            return "Agent is stuck repeating the same command. Please rephrase your request."
        last_tool_call = tool_call

        tool_name = tool_call["tool"]
        tool_input = tool_call["input"]

        if tool_name not in TOOLS:
            tool_result = f"Unknown tool: {tool_name}. Available tools: bash, read_file, write_file, search_files"
        else:
            tool_result = TOOLS[tool_name](tool_input)

        print(f"Tool result: {repr(tool_result)}")
        messages.append({"role": "user", "content": f"Tool result:\n{tool_result}"})

    return "Agent stopped: reached maximum iterations."
