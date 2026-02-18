#!/bin/bash
# Quick Test - Verify Local Supabase Setup

set -e

echo "🧪 Testing local Supabase setup..."
echo ""

# Check if services are running
if docker ps | grep -q "vecinita-postgres-test"; then
    echo "✅ PostgreSQL test instance is running"
else
    echo "❌ PostgreSQL test instance is not running"
    echo "   Run: cd supabase && ./start-local.sh"
    exit 1
fi

if docker ps | grep -q "vecinita-postgrest-test"; then
    echo "✅ PostgREST test instance is running"
else
    echo "❌ PostgREST test instance is not running"
    echo "   Run: cd supabase && ./start-local.sh"
    exit 1
fi

# Test PostgREST connection
echo ""
echo "🔗 Testing PostgREST connection..."
RESPONSE=$(curl -s http://localhost:3001/ || echo "FAILED")
if [ "$RESPONSE" != "FAILED" ]; then
    echo "✅ PostgREST is responding"
else
    echo "❌ PostgREST is not responding"
    exit 1
fi

# Test database connection
echo ""
echo "🔗 Testing PostgreSQL connection..."
TABLE_EXISTS=$(docker exec vecinita-postgres-test psql -U postgres -d postgres -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'document_chunks');" 2>/dev/null || echo "false")

if [ "$TABLE_EXISTS" = "t" ] || [ "$TABLE_EXISTS" = "true" ]; then
    echo "✅ Database schema exists"
    
    # Count rows
    ROW_COUNT=$(docker exec vecinita-postgres-test psql -U postgres -d postgres -tAc "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null || echo "0")
    echo "   📊 document_chunks has $ROW_COUNT rows"
else
    echo "⚠️  Database schema not initialized"
    echo "   Run: cd supabase && ./init-local-db.sh"
fi

# Test RPC function
RPC_EXISTS=$(docker exec vecinita-postgres-test psql -U postgres -d postgres -tAc "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'search_similar_documents');" 2>/dev/null || echo "false")
if [ "$RPC_EXISTS" = "t" ] || [ "$RPC_EXISTS" = "true" ]; then
    echo "✅ RPC function 'search_similar_documents' exists"
else
    echo "⚠️  RPC function 'search_similar_documents' not found"
fi

echo ""
echo "✨ Local test environment status: READY"
echo ""
echo "📋 Connection details:"
echo "   PostgreSQL: postgresql://postgres:postgres@localhost:54321/postgres"
echo "   PostgREST:  http://localhost:3001"
echo "   pgAdmin:    http://localhost:5051 (test@example.com / test123)"
echo ""
echo "🔧 To use in your backend:"
echo "   export SUPABASE_URL=http://localhost:3001"
echo "   export DATABASE_URL=postgresql://postgres:postgres@localhost:54321/postgres"
echo ""
echo "   Or copy backend/.env.test to backend/.env"
