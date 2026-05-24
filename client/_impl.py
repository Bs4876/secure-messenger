"""Implementation for the client package.

This file contains the actual CLI logic (moved from top-level cli.py).
"""

import threading
import json
from getpass import getpass

import httpx

API = "http://127.0.0.1:8000"


def sse_listener(token: str, stop_event: threading.Event):
    url = f"{API}/stream?token={token}"
    try:
        with httpx.Client(timeout=None) as client:
            try:
                with client.stream('GET', url) as resp:
                    for raw in resp.iter_lines():
                        if stop_event.is_set():
                            break
                        if not raw:
                            continue
                        line = raw.decode() if isinstance(raw, bytes) else raw
                        if line.startswith('data:'):
                            payload = line.split('data:', 1)[1].strip()
                            try:
                                obj = json.loads(payload)
                            except json.JSONDecodeError:
                                print(f"\n[RAW] {payload}\n> ", end='', flush=True)
                                continue
                            if not isinstance(obj, dict):
                                print(f"\n[EVENT] {obj}\n> ", end='', flush=True)
                                continue
                            sender = obj.get('sender', 'unknown')
                            recip = obj.get('recipient', '')
                            content = obj.get('content', '')
                            print(f"\n[{sender} -> {recip}] {content}\n> ", end='', flush=True)
            except Exception:
                if not stop_event.is_set():
                    print(f"\n[SSE] connection to {url} failed or closed.\n> ", end='', flush=True)
    except Exception:
        return


def login_prompt():
    username = input('Name: ').strip()
    password = getpass('Password: ')
    try:
        r = httpx.post(f"{API}/login", json={"username": username, "password": password}, timeout=10.0)
    except httpx.ConnectError:
        print(f"Cannot connect to server at {API}. Make sure the server is running: uvicorn server.main:app --reload")
        return None, None
    except httpx.ReadTimeout:
        print(f"Request to server timed out. Is the server running and responsive at {API}?")
        return None, None
    except httpx.RequestError as e:
        print(f"Network error: {e}")
        return None, None

    if r.status_code == 200:
        token = r.json()['access_token']
        print(f'Logged in as {username}')
        return username, token
    else:
        print('Login failed:', r.status_code, r.text)
        return None, None


def fetch_inbox(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{API}/messages", headers=headers)
    if r.status_code == 200:
        messages = r.json()
        if not messages:
            print('Inbox empty')
        for m in messages:
            print(f"[{m['created_at']}] {m['sender']} -> {m['recipient']}: {m['content']}")
    else:
        print('Error fetching inbox:', r.status_code, r.text)


def send_message(token: str, recipient: str, content: str):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.post(f"{API}/messages", json={"recipient": recipient, "content": content}, headers=headers)
    if r.status_code == 201:
        print('Sent')
    else:
        print('Send failed:', r.status_code, r.text)


def main():
    username, token = login_prompt()
    if not token:
        return

    stop_event = threading.Event()
    t = threading.Thread(target=sse_listener, args=(token, stop_event), daemon=True)
    t.start()

    try:
        print("Type 'recipient: message' to send, '/inbox' to list messages, '/quit' to exit")
        while True:
            line = input('> ').strip()
            if not line:
                continue
            if line == '/quit':
                break
            if line == '/help':
                print("Commands: /inbox /help /quit")
                continue
            if line == '/inbox':
                fetch_inbox(token)
                continue
            if ':' in line:
                recipient, content = line.split(':', 1)
                recipient = recipient.strip()
                content = content.strip()
                if recipient and content:
                    send_message(token, recipient, content)
                else:
                    print("Invalid format. Use: recipient: message")
            else:
                print("Unknown input. Use 'recipient: message' or /help")
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()


if __name__ == '__main__':
    main()
