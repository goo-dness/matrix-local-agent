# Matrix Agent

An autonomous, tool-augmented local AI assistant built using FastAPI, HTTPX, and SQLite. This system was designed to execute system commands and manage local files completely through an iteration loop driven by an LLM backend.

## Project Architecture

* **`main.py`**: The backend server gateway built with FastAPI. It handles the request lifecycle, session creation, and trims conversational history to keep context clean.
* **`agent.py`**: The core execution brain. It coordinates an iterative loop (up to 10 passes) that calls the language model, parses tool invocations from text, and routes execution results back to the context window.
* **`tools.py`**: The low-level operational layers mapping the agent to the host system. It contains deterministic functions for `bash`, `read_file`, `write_file`, and `search_files`.
* **`memory.py`**: An SQLite database layer managing persistence. It saves conversational histories sequentially matching unique 8-character session IDs.
* **`cli.py`**: A clean, terminal-based interactive command-line interface with a background spinner thread for live interaction.

## Core Mechanics

The engine works by processing user strings through an execution loop:
1. The user inputs a command via the CLI.
2. The server pulls conversational history from SQLite.
3. The model reviews instructions and decides whether to output a final string or call a system tool (e.g., executing a bash command).
4. If a tool is called, `tools.py` runs it locally, captures stdout/stderr, and injects the output back into the model's message array for the next iteration step.
