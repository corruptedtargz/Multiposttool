"""Instagram downloads videos from a public URL. This exposes ONLY the uploads
folder (no app, no settings) through an ngrok tunnel, started on demand."""
import os, threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import config

_lock = threading.Lock()
_url: str | None = None


class _Handler(SimpleHTTPRequestHandler):
    def list_directory(self, path):  # no directory listings
        self.send_error(404)

    def log_message(self, *a):
        pass


def public_base_url() -> str:
    global _url
    with _lock:
        if _url:
            return _url
        token = os.getenv("NGROK_AUTHTOKEN")
        if not token:
            raise RuntimeError("Instagram needs a public URL: add a free ngrok authtoken in Settings.")
        srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Handler, directory=str(config.UPLOADS)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        from pyngrok import ngrok
        ngrok.set_auth_token(token)
        tunnel = ngrok.connect(srv.server_address[1], "http")
        _url = tunnel.public_url.replace("http://", "https://")
        return _url
