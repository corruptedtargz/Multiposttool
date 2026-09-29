"""Desktop entry point: runs the local server and shows it in a native window."""
import socket, threading, time
import uvicorn, webview
import config
from app import app


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    config.load()
    port = free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    webview.create_window("Clip Poster", f"http://127.0.0.1:{port}",
                          width=560, height=880, min_size=(460, 600))
    webview.start()
    server.should_exit = True


if __name__ == "__main__":
    main()
