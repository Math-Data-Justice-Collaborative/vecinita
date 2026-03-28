#!/bin/bash
# Start Local Test Supabase Environment

set -e

echo "🚀 Starting local test Supabase environment..."
echo ""
echo "⚠️  NOTE: This is a TEST environment"
echo "   - Uses local PostgreSQL on port 54321"
echo "   - Uses local PostgREST on port 3001"
echo "   - Does NOT connect to production"
echo ""

cd "$(dirname "$0")"

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait a moment
sleep 3

# Initialize database
echo ""
./init-local-db.sh

echo ""
echo "✨ Local test environment is ready!"
echo ""
echo "📝 Next steps:"
echo "   1. Update your backend/.env to use local settings:"
echo "      SUPABASE_URL=http://localhost:3001"
echo "      DATABASE_URL=postgresql://postgres:postgres@localhost:54321/postgres"
echo ""
echo "   2. Or copy test env vars:"
echo "      cp supabase/.env.test backend/.env.test"
echo ""
echo "   3. Run your backend:"
echo "      cd backend && uv run uvicorn src.agent.main:app --reload"
echo ""
echo "🛑 To stop: cd supabase && docker-compose down"
