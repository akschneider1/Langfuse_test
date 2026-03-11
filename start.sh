#!/usr/bin/env bash
set -euo pipefail

echo "=== Langfuse v3 Self-Hosted Setup ==="
echo ""

# Install Python dependencies
if [ -f requirements.txt ]; then
  echo "[1/3] Installing Python dependencies..."
  pip install -q -r requirements.txt
fi

# Start Langfuse via Docker Compose
echo "[2/3] Starting Langfuse v3 services (Postgres, ClickHouse, Redis, MinIO, Web, Worker)..."
docker-compose up -d

echo "[3/3] Waiting for Langfuse to be healthy (this may take a minute on first run)..."
for i in $(seq 1 60); do
  if wget -q --spider http://localhost:3000/api/public/health 2>/dev/null; then
    echo ""
    echo "=== Langfuse v3 is running! ==="
    echo ""
    echo "  UI:            http://localhost:3000"
    echo "  API:           http://localhost:3000/api/public"
    echo "  MinIO Console: http://localhost:9091  (minioadmin / minioadmin)"
    echo ""
    echo "Next steps:"
    echo "  1. Open the UI and create an account"
    echo "  2. Create a project and grab your API keys"
    echo "  3. cp .env.example .env  — then paste your keys"
    echo "  4. python scripts/seed_test_data.py"
    echo "  5. python scripts/stream_test_data.py"
    echo ""
    exit 0
  fi
  printf "."
  sleep 3
done

echo ""
echo "WARNING: Langfuse did not become healthy within 3 minutes."
echo "Check logs with: docker-compose logs langfuse-web"
exit 1
