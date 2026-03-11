#!/usr/bin/env bash
set -euo pipefail

echo "=== Langfuse Self-Hosted Setup ==="
echo ""

# Install Python dependencies
if [ -f requirements.txt ]; then
  echo "[1/3] Installing Python dependencies..."
  pip install -q -r requirements.txt
fi

# Start Langfuse via Docker Compose
echo "[2/3] Starting Langfuse services (Postgres + Langfuse Server)..."
docker-compose up -d

echo "[3/3] Waiting for Langfuse to be healthy..."
for i in $(seq 1 30); do
  if wget -q --spider http://localhost:3000/api/public/health 2>/dev/null; then
    echo ""
    echo "=== Langfuse is running! ==="
    echo "  UI:  http://localhost:3000"
    echo "  API: http://localhost:3000/api/public"
    echo ""
    echo "Next steps:"
    echo "  1. Open the UI and create an account"
    echo "  2. Create a project and grab your API keys"
    echo "  3. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env"
    echo "  4. Run: python scripts/seed_test_data.py"
    echo "  5. Run: python scripts/stream_test_data.py"
    echo ""
    exit 0
  fi
  printf "."
  sleep 2
done

echo ""
echo "WARNING: Langfuse did not become healthy within 60s."
echo "Check logs with: docker-compose logs langfuse-server"
exit 1
