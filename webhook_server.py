#!/usr/bin/env python3
"""Lightweight webhook receiver for autoresearch-crystal results.
Receives POST /result, appends to results log, optionally notifies via Telegram.

Run on VPS: python3 webhook_server.py
Port: 3011
"""

import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

RESULTS_FILE = "/home/clawd/clawd/projects/autoresearch-crystal/remote_results.jsonl"
PORT = 3011

# Telegram notification (optional)
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "1431739444")


def notify_telegram(text):
    if not TG_BOT_TOKEN:
        return
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Telegram notify failed: {e}")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/result":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"invalid json")
            return

        # Add server timestamp
        data["received_at"] = datetime.now(timezone.utc).isoformat()

        # Append to results file
        with open(RESULTS_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")

        # Log
        val = data.get("val_bpb", "?")
        crystal = data.get("crystal_pct", "?")
        ordering = data.get("crystal_ordering", "?")
        status = data.get("status", "?")
        desc = data.get("description", "")
        run_num = sum(1 for _ in open(RESULTS_FILE)) if os.path.exists(RESULTS_FILE) else 1

        print(f"[Run #{run_num}] val_bpb={val} crystal={crystal}% ordering={ordering} status={status} — {desc}")

        # Notify
        msg = (
            f"🔬 <b>Autoresearch Run #{run_num}</b>\n"
            f"val_bpb: <code>{val}</code>\n"
            f"crystal: <code>{crystal}%</code>\n"
            f"ordering: <code>{ordering}</code>\n"
            f"status: {status}\n"
            f"{desc}"
        )
        notify_telegram(msg)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Quiet logging
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Crystal webhook listening on port {PORT}")
    server.serve_forever()
