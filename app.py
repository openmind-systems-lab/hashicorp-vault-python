#!/usr/bin/env python3
"""Tiny HTTP app used to validate HashiCorp Vault Agent injection on Kubernetes.

The only goal is to prove that the Vault
sidecar writes the expected secret file into /vault/secrets and that the main
container can read it.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import os
import socket
import time

SECRET_PATH = Path(os.getenv("VAULT_SECRET_FILE", "/vault/secrets/realm.xml"))
PORT = int(os.getenv("PORT", "8080"))

STARTED_AT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def secret_status() -> dict:
    exists = SECRET_PATH.exists()
    content = SECRET_PATH.read_text(encoding="utf-8") if exists else ""
    return {
        "path": str(SECRET_PATH),
        "exists": exists,
        "size_bytes": len(content.encode("utf-8")),
        "first_80_chars": content[:80] if exists else "",
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/_ping", "/healthz"):
            status = secret_status()
            self._send_json(
                200,
                {
                    "status": "ok",
                    "app": "python-vault-validation",
                    "hostname": socket.gethostname(),
                    "started_at": STARTED_AT,
                    "vault_secret": status,
                },
            )
            return

        if self.path == "/secret-required":
            status = secret_status()
            self._send_json(200 if status["exists"] else 503, status)
            return

        self._send_json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"Starting server on port {PORT}; checking secret at {SECRET_PATH}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
