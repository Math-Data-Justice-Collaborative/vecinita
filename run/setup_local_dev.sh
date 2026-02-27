#!/bin/bash
# Setup Local Development Environment
# This script configures backend to use local PostgREST instead of production Supabase

set -e

echo "🔧 Setting up local development environment..."

# Backup current .env
if [ -f backend/.env ]; then
    echo "📦 Backing up current .env to .env.backup..."
    cp backend/.env backend/.env.backup
fi

# Create local development .env
cat > backend/.env.local << 'EOF'
# Local Development Configuration
# Using local PostgreSQL + PostgREST (docker-compose)

# ---------------------------------
# Local Supabase (PostgREST)
# ---------------------------------
SUPABASE_URL=http://localhost:3001
SUPABASE_KEY=dev-anon-key

# ---------------------------------
# Local Database
# ---------------------------------
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres

# ---------------------------------
# Cloud LLM Provider API Keys
# ---------------------------------
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-your-deepseek-api-key-here}
GROQ_API_KEY=${GROQ_API_KEY:-your-groq-api-key-here}
OPEN_API_KEY=${OPEN_API_KEY:-your-openai-api-key-here}
TAVILY_API_KEY=${TAVILY_API_KEY:-your-tavily-api-key-here}

# ---------------------------------
# Agent Provider Configuration
# ---------------------------------
DEFAULT_PROVIDER=deepseek

# ---------------------------------
# Embedding Model Config
# ---------------------------------
EMBEDDING_MODEL=text-embedding-3-small
USE_LOCAL_EMBEDDINGS=true

# ---------------------------------
# LangSmith (Optional)
# ---------------------------------
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=${LANGSMITH_API_KEY:-}

# ---------------------------------
# TensorFlow Configuration
# ---------------------------------
TF_ENABLE_ONEDNN_OPTS=0
EOF

# Copy API keys from existing .env if available
if [ -f backend/.env ]; then
    echo "🔑 Copying API keys from existing .env..."
    for key in DEEPSEEK_API_KEY GROQ_API_KEY OPEN_API_KEY TAVILY_API_KEY LANGSMITH_API_KEY; do
        value=$(grep "^${key}=" backend/.env | cut -d'=' -f2- || echo "")
        if [ ! -z "$value" ]; then
            sed -i "s|${key}=.*|${key}=${value}|" backend/.env.local
        fi
    done
fi

# Replace current .env with local version
cp backend/.env.local backend/.env

echo "✅ Local .env configured!"
echo ""
echo "📁 Configuration summary:"
echo "   SUPABASE_URL: http://localhost:3001"
echo "   DATABASE_URL: postgresql://postgres:postgres@localhost:5432/postgres"
echo ""

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres postgrest

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check if schema exists
echo "🔍 Checking database schema..."
SCHEMA_EXISTS=$(docker-compose exec -T postgres psql -U postgres -d postgres -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'document_chunks');" 2>/dev/null || echo "false")

if [ "$SCHEMA_EXISTS" = "f" ] || [ "$SCHEMA_EXISTS" = "false" ]; then
    echo "📊 Installing database schema..."
    docker-compose exec -T postgres psql -U postgres -d postgres < backend/scripts/schema_install.sql
    echo "✅ Schema installed!"
else
    echo "✅ Schema already exists!"
fi

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "✨ Local development environment ready!"
echo ""
echo "🌐 Services available at:"
echo "   - Agent API:     http://localhost:8000"
echo "   - Gateway API:   http://localhost:8002"
echo "   - PostgREST:     http://localhost:3001"
echo "   - pgAdmin:       http://localhost:5050"
echo ""
echo "📝 To restore production config: cp backend/.env.backup backend/.env"
echo "📋 To view logs: docker-compose logs -f vecinita-agent"
echo "🔄 To restart: docker-compose restart"
