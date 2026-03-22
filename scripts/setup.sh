#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🚀 Iterra Development Setup"
echo "============================="

# 1. Environment variables
if [ ! -f .env ]; then
  echo "📋 Copying .env.example → .env"
  cp .env.example .env
  echo "   ⚠️  Edit .env and add your OPENAI_API_KEY before running the AI features."
else
  echo "✅ .env already exists — skipping copy"
fi

# 2. Start infrastructure services
echo ""
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose up -d db redis
echo "   Waiting for services to be healthy..."
sleep 5

# 3. Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install -r apps/api/requirements-dev.txt
pip install -e packages/ai-engine/
echo "   ✅ Python dependencies installed"

# 4. Install Node dependencies
echo ""
echo "📦 Installing Node dependencies..."
cd packages/shared-types && npm install && cd "$REPO_ROOT"
cd apps/web && npm install --legacy-peer-deps && cd "$REPO_ROOT"
echo "   ✅ Node dependencies installed"

# 5. Run database migrations
echo ""
echo "🗄️  Running database migrations..."
docker-compose run --rm api alembic upgrade head
echo "   ✅ Migrations complete"

# 6. Seed database
echo ""
echo "🌱 Seeding database..."
docker-compose run --rm api python /app/../scripts/seed_db.py || true
echo "   ✅ Database seeded"

# 7. Start all services
echo ""
echo "🎉 Starting all services..."
docker-compose up -d

echo ""
echo "============================="
echo "✅ Iterra is running!"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Run 'make stop' to stop all services."
