import json
import os
import subprocess


def bash(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    output = result.stdout + result.stderr
    return output if output else "Command ran with no output"


def read_file(path: str) -> str:
    try:
        with open(os.path.expanduser(path), "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(raw_input) -> str:
    try:
        data = raw_input if isinstance(raw_input, dict) else json.loads(raw_input)
        path = os.path.expanduser(data["path"])
        content = data["content"]
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def open_in_zed(path: str) -> str:
    try:
        subprocess.Popen(["zed", os.path.expanduser(path)])
        # return f"Opened {path} in Zed"
    except Exception as e:
        return f"Error opening in Zed: {str(e)}"


def search_files(raw_input) -> str:
    try:
        if isinstance(raw_input, dict):
            query = raw_input["query"]
            directory = raw_input.get("directory", "~")
        else:
            raw_input = str(raw_input).strip()
            try:
                data = json.loads(raw_input)
                query = data["query"]
                directory = data.get("directory", "~")
            except (json.JSONDecodeError, ValueError):
                parts = raw_input.split("|", 1)
                query = parts[0].strip()
                directory = parts[1].strip() if len(parts) > 1 else "~"
        directory = os.path.expanduser(directory)

        # Search filenames
        name_result = subprocess.run(
            ["find", directory, "-name", f"*{query}*"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Search text inside files
        text_result = subprocess.run(
            ["grep", "-r", "-l", "--include=*.py", query, directory],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = ""
        if name_result.stdout:
            output += f"Files marching name '{query}':\n{name_result.stdout}\n"
        if text_result.stdout:
            output += f"Files containing text '{query}':\n{text_result.stdout}\n"

        return output if output else "No matches found"
    except Exception as e:
        return f"Error searching: {str(e)}"


TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "search_files": search_files,
    "open_in_zed": open_in_zed,
}
