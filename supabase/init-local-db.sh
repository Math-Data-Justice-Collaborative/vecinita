#!/bin/bash
# Initialize Local Test Database
# Run this after starting docker-compose to set up the schema

set -e

echo "🔧 Initializing local test database..."

# Check if PostgreSQL is ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec vecinita-postgres-test pg_isready -U postgres > /dev/null 2>&1; do
  echo "   Waiting..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Check if schema is already installed
SCHEMA_EXISTS=$(docker exec vecinita-postgres-test psql -U postgres -d postgres -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'document_chunks');" 2>/dev/null || echo "false")

if [ "$SCHEMA_EXISTS" = "f" ] || [ "$SCHEMA_EXISTS" = "false" ]; then
    echo "📊 Installing database schema..."
    docker exec -i vecinita-postgres-test psql -U postgres -d postgres < init-local-db.sql
    echo "✅ Schema installed successfully!"
else
    echo "✅ Schema already exists"
fi

# Verify installation
echo "🔍 Verifying installation..."
TABLES=$(docker exec vecinita-postgres-test psql -U postgres -d postgres -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")
echo "   Found $TABLES tables in database"

RPC_EXISTS=$(docker exec vecinita-postgres-test psql -U postgres -d postgres -tAc "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'search_similar_documents');" 2>/dev/null || echo "false")
if [ "$RPC_EXISTS" = "t" ] || [ "$RPC_EXISTS" = "true" ]; then
    echo "   ✅ RPC function 'search_similar_documents' exists"
else
    echo "   ⚠️  RPC function 'search_similar_documents' not found"
fi

echo ""
echo "✨ Local test database ready!"
echo ""
echo "📋 Connection details:"
echo "   PostgreSQL: postgresql://postgres:postgres@localhost:54321/postgres"
echo "   PostgREST:  http://localhost:3001"
echo "   pgAdmin:    http://localhost:5051 (test@example.com / test123)"
echo ""
echo "🔗 Test the connection:"
echo "   curl http://localhost:3001/document_chunks?limit=1"
