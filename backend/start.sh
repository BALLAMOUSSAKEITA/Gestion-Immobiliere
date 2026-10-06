#!/bin/sh
set -e

PORT="${PORT:-8000}"

echo "Serving temporary health endpoint on port ${PORT}..."
python - <<'PY' &
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"status":"ok","phase":"migrating"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return

HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
PY
HEALTH_PID=$!

cleanup() {
  kill "$HEALTH_PID" 2>/dev/null || true
  wait "$HEALTH_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Running database migrations..."
attempt=1
while [ "$attempt" -le 5 ]; do
  if alembic upgrade head; then
    break
  fi
  echo "Migration attempt ${attempt} failed, retrying..."
  attempt=$((attempt + 1))
  sleep 3
done

if [ "$attempt" -gt 5 ]; then
  echo "Migrations failed after retries"
  exit 1
fi

echo "Starting API on port ${PORT}..."
cleanup
trap - EXIT INT TERM
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
