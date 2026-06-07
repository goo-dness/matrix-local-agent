#!/usr/bin/env python3
import sys
import threading
import time

import httpx

API_URL = "http://localhost:8080/chat"


def thinking_spinner(stop_event):
    print("Thinking", end="", flush=True)
    while not stop_event.is_set():
        print(".", end="", flush=True)
        time.sleep(0.5)
    print()


def chat(message: str, session_id: str) -> tuple[str, str]:
    try:
        stop_event = threading.Event()
        thread = threading.Thread(target=thinking_spinner, args=(stop_event,))
        thread.start()

        response = httpx.post(
            API_URL, json={"message": message, "session_id": session_id}, timeout=120.0
        )

        stop_event.set()
        thread.join()

        data = response.json()
        return data["response"], data["session_id"]

    except httpx.ConnectError:
        print("\nError: Matrix server is not running.")
        print(
            "Start it with: cd ~/agent && source venv/bin/activate && uvicorn main:app --port 8080"
        )
        sys.exit(1)


def main():
    session_id = ""

    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        response, _ = chat(message, session_id)
        print(response)
        return

    print("\nMatrix ready. Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "bye"):
                print("Goodbye.")
                break

            response, session_id = chat(user_input, session_id)
            print(f"\nMatrix: {response}\n")

        except KeyboardInterrupt:
            print("\nGoodbye.")
            break


if __name__ == "__main__":
    main()
