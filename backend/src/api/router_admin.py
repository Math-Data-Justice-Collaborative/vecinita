"""
Unified API Gateway - Admin Router

Endpoints for database management, statistics, and system administration.
"""

import asyncio
import os
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, Query, Depends
from supabase import create_client, Client

from ..services.db.schema_diagnostics import validate_schema, get_validation_summary
from .models import (
    AdminHealthResponse,
    AdminStatsResponse,
    CleanDatabaseRequest,
    CleanDatabaseResponse,
    CleanRequestTokenResponse,
    DatabaseStats,
    DeleteChunkResponse,
    DocumentChunk,
    DocumentsListResponse,
    SourcesListResponse,
    ValidateSourceRequest,
    ValidateSourceResponse,
)

router = APIRouter(prefix="/admin", tags=["Administration"])

# Configuration - will be set by main.py
ADMIN_CONFIG = {
    "require_confirmation": True,
    "delete_chunk_batch_size": 1000,
}

# Service URLs from environment
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")

# Token storage (in-memory for now, use Redis for production)
_cleanup_tokens: Dict[str, datetime] = {}


def get_database_client() -> Client:
    """
    Dependency to get Supabase database client.
    
    Returns:
        Supabase client instance
        
    Raises:
        HTTPException: If database credentials not configured
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Database not configured. Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    
    return create_client(supabase_url, supabase_key)


@router.get("/health")
async def admin_health_check(db: Client = Depends(get_database_client)) -> AdminHealthResponse:
    """
    Check health of all backend services.
    
    Particularly useful for debugging deployment issues.
    
    Returns:
        Health status of agent, embedding service, database
    """
    # Check agent service
    agent_health = {"status": "error"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.time()
            response = await client.get(f"{AGENT_SERVICE_URL}/health")
            elapsed_ms = int((time.time() - start) * 1000)
            if response.status_code == 200:
                agent_health = {
                    "status": "ok",
                    "response_time_ms": elapsed_ms,
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
            else:
                agent_health = {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
    except Exception as e:
        agent_health = {
            "status": "error",
            "message": str(e),
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    # Check embedding service
    embedding_health = {"status": "error"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.time()
            response = await client.get(f"{EMBEDDING_SERVICE_URL}/health")
            elapsed_ms = int((time.time() - start) * 1000)
            if response.status_code == 200:
                embedding_health = {
                    "status": "ok",
                    "response_time_ms": elapsed_ms,
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
            else:
                embedding_health = {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
    except Exception as e:
        embedding_health = {
            "status": "error",
            "message": str(e),
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    # Check database
    db_health = {"status": "error"}
    try:
        # Simple query to test connection
        result = db.table("document_chunks").select("id", count="exact").limit(1).execute()
        db_health = {
            "status": "ok",
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        db_health = {
            "status": "error",
            "message": str(e),
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    # Determine overall status
    all_healthy = (
        agent_health["status"] == "ok" and
        embedding_health["status"] == "ok" and
        db_health["status"] == "ok"
    )
    overall_status = "healthy" if all_healthy else "degraded"
    
    return AdminHealthResponse(
        status=overall_status,
        agent_service=agent_health,
        embedding_service=embedding_health,
        database=db_health,
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/stats")
async def get_database_stats(db: Client = Depends(get_database_client)) -> AdminStatsResponse:
    """
    Get comprehensive database and system statistics.
    
    Returns:
        - Database: chunk count, unique sources, embeddings status
        - Services: availability, configuration
    """
    try:
        # Get total chunks
        total_result = db.table("document_chunks").select("*", count="exact").limit(1).execute()
        total_chunks = total_result.count if total_result.count is not None else 0
        
        # Get unique sources
        sources_result = db.rpc("get_unique_sources_count").execute()
        unique_sources = sources_result.data if sources_result.data else 0
        
        # Get chunks with embeddings (non-null embedding column)
        # Note: If processed=true, assume embedding exists
        embeddings_result = db.table("document_chunks").select("*", count="exact").eq("processed", True).limit(1).execute()
        total_embeddings = embeddings_result.count if embeddings_result.count is not None else 0
        
        # Get average chunk size
        avg_size_result = db.rpc("get_average_chunk_size").execute()
        avg_chunk_size = float(avg_size_result.data) if avg_size_result.data else 0.0
        
        # Get database size (if RPC function exists)
        try:
            db_size_result = db.rpc("get_database_size").execute()
            db_size_bytes = db_size_result.data if db_size_result.data else None
        except:
            db_size_bytes = None
        
        db_stats = DatabaseStats(
            total_chunks=total_chunks,
            unique_sources=unique_sources,
            total_embeddings=total_embeddings,
            average_chunk_size=avg_chunk_size,
            db_size_bytes=db_size_bytes,
            last_updated=datetime.now(timezone.utc)
        )
        
        # Service metrics (basic, can be enhanced)
        services = {
            "agent_service": {
                "url": AGENT_SERVICE_URL,
                "status": "configured"
            },
            "embedding_service": {
                "url": EMBEDDING_SERVICE_URL,
                "status": "configured"
            }
        }
        
        return AdminStatsResponse(
            database=db_stats,
            services=services
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@router.get("/documents")
async def list_documents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source_filter: Optional[str] = Query(None, description="Filter by source URL"),
    db: Client = Depends(get_database_client)
) -> DocumentsListResponse:
    """
    List indexed document chunks.
    
    Paginated, sortable by creation date or source.
    
    Args:
        limit: Results per page
        offset: Results to skip
        source_filter: Optional source URL filter
        
    Returns:
        Paginated list of document chunks
    """
    try:
        # Build query
        query = db.table("document_chunks").select(
            "id, source, content, embedding, created_at, updated_at",
            count="exact"
        )
        
        # Apply source filter if provided
        if source_filter:
            query = query.ilike("source", f"%{source_filter}%")
        
        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        # Build document chunks
        documents = []
        for row in result.data:
            # Get content preview (first 200 chars)
            content = row.get("content", "")
            content_preview = content[:200] if content else ""
            
            # Determine embedding dimension (384 for sentence-transformers/all-MiniLM-L6-v2)
            embedding_dim = 384  # Default, could parse from embedding if needed
            
            documents.append(
                DocumentChunk(
                    chunk_id=row["id"],
                    source_url=row.get("source", ""),
                    content_preview=content_preview,
                    embedding_dimension=embedding_dim,
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else datetime.now(timezone.utc),
                    updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None
                )
            )
        
        total = result.count if result.count is not None else len(documents)
        page = (offset // limit) + 1
        
        return DocumentsListResponse(
            documents=documents,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/documents/{chunk_id}")
async def delete_document(chunk_id: str, db: Client = Depends(get_database_client)) -> DeleteChunkResponse:
    """
    Delete a specific document chunk.
    
    Removes from database and vector store.
    
    Args:
        chunk_id: Chunk identifier to delete
        
    Returns:
        Deletion confirmation
    """
    try:
        # Check if chunk exists
        existing = db.table("document_chunks").select("id").eq("id", chunk_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=404,
                detail=f"Chunk {chunk_id} not found"
            )
        
        # Delete the chunk
        result = db.table("document_chunks").delete().eq("id", chunk_id).execute()
        
        return DeleteChunkResponse(
            success=True,
            deleted_chunk_id=chunk_id,
            message=f"Successfully deleted chunk {chunk_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chunk: {str(e)}"
        )


@router.post("/database/clean")
async def clean_database(request: CleanDatabaseRequest, db: Client = Depends(get_database_client)) -> CleanDatabaseResponse:
    """
    Truncate all document chunks and embeddings.
    
    DESTRUCTIVE OPERATION. Requires confirmation token to prevent accidents.
    
    Args:
        request: CleanDatabaseRequest with confirmation token
        
    Returns:
        Confirmation of deletion with count
        
    Raises:
        HTTPException: If confirmation token is invalid
    """
    # Validate token
    token = request.confirmation_token
    
    if token not in _cleanup_tokens:
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired confirmation token. Request a new token from GET /api/admin/database/clean-request"
        )
    
    # Check token expiry
    expires_at = _cleanup_tokens[token]
    if datetime.now(timezone.utc) > expires_at:
        del _cleanup_tokens[token]
        raise HTTPException(
            status_code=403,
            detail="Confirmation token has expired. Request a new token."
        )
    
    # Consume token (one-time use)
    del _cleanup_tokens[token]
    
    try:
        # Check if require_confirmation is enabled
        if ADMIN_CONFIG.get("require_confirmation", True):
            # Already validated token above
            pass
        
        # Get count before deletion
        count_result = db.table("document_chunks").select("*", count="exact").limit(1).execute()
        deleted_count = count_result.count if count_result.count is not None else 0
        
        # Delete all chunks (in batches to avoid timeout)
        batch_size = ADMIN_CONFIG.get("delete_chunk_batch_size", 1000)
        deleted_total = 0
        
        while True:
            result = db.table("document_chunks").delete().limit(batch_size).execute()
            if not result.data:
                break
            deleted_total += len(result.data)
            if len(result.data) < batch_size:
                break
        
        # Also delete orphaned sources if they exist in a separate table
        # (Optional, depends on schema)
        try:
            db.table("search_queries").delete().execute()
        except:
            pass  # Table might not exist or be empty
        
        return CleanDatabaseResponse(
            success=True,
            deleted_chunks=deleted_total,
            message=f"Database cleaned: {deleted_total} chunks deleted"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clean database: {str(e)}"
        )


@router.get("/database/clean-request")
async def request_database_clean() -> CleanRequestTokenResponse:
    """
    Request confirmation token for database cleanup.
    
    Returns token that must be used in /database/clean POST.
    This is the first step of the cleanup process.
    
    Returns:
        Confirmation token (valid for 5 minutes)
    """
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Store with 5-minute expiry
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    _cleanup_tokens[token] = expires_at
    
    # Clean expired tokens
    now = datetime.now(timezone.utc)
    expired = [t for t, exp in _cleanup_tokens.items() if exp < now]
    for t in expired:
        del _cleanup_tokens[t]
    
    return CleanRequestTokenResponse(
        token=token,
        expires_at=expires_at,
        endpoint="POST /api/admin/database/clean"
    )


@router.get("/sources")
async def list_all_sources(db: Client = Depends(get_database_client)) -> SourcesListResponse:
    """
    List all unique source URLs in the database.
    
    Returns:
        List of sources with chunk counts
    """
    try:
        # Query for unique sources with chunk counts
        # Using a raw SQL approach through RPC or direct aggregation
        result = db.rpc("get_sources_with_counts").execute()
        
        if result.data:
            sources = result.data
        else:
            # Fallback: manual aggregation if RPC doesn't exist
            # Get all chunks and aggregate in Python
            all_chunks = db.table("document_chunks").select("source, created_at, updated_at").execute()
            
            # Aggregate by source
            source_map = {}
            for chunk in all_chunks.data:
                source = chunk.get("source", "")
                if source not in source_map:
                    source_map[source] = {
                        "url": source,
                        "chunk_count": 0,
                        "created_at": chunk.get("created_at"),
                        "last_updated": chunk.get("updated_at")
                    }
                source_map[source]["chunk_count"] += 1
                
                # Update last_updated to most recent
                if chunk.get("updated_at"):
                    current_last = source_map[source].get("last_updated")
                    if not current_last or chunk["updated_at"] > current_last:
                        source_map[source]["last_updated"] = chunk["updated_at"]
            
            sources = list(source_map.values())
            sources.sort(key=lambda x: x["chunk_count"], reverse=True)
        
        return SourcesListResponse(
            sources=sources,
            total=len(sources)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sources: {str(e)}"
        )


@router.post("/sources/validate")
async def validate_sources(request: ValidateSourceRequest) -> ValidateSourceResponse:
    """
    Validate a source URL.
    
    Tests HTTP connectivity for the source.
    Admin endpoint for debugging scraping issues.
    
    Returns:
        Validation results
    """
    url = request.url
    
    try:
        # Test HTTP HEAD request first (lightweight)
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                response = await client.head(url)
                http_status = response.status_code
                
                # If HEAD not allowed, try GET
                if http_status == 405:
                    response = await client.get(url, timeout=10.0)
                    http_status = response.status_code
                
                is_accessible = 200 <= http_status < 400
                
                # Basic scrapability check
                is_scrapeable = is_accessible
                if is_accessible:
                    # Check content type if available
                    content_type = response.headers.get("content-type", "")
                    # Scrapeable if HTML, XML, or plain text
                    is_scrapeable = any(
                        ct in content_type.lower()
                        for ct in ["html", "xml", "text/plain", "application/pdf"]
                    )
                
                message = "URL is accessible"
                if is_accessible and is_scrapeable:
                    message = "URL is accessible and scrapeable"
                elif is_accessible and not is_scrapeable:
                    message = f"URL is accessible but content type ({content_type}) may not be scrapeable"
                elif not is_accessible:
                    message = f"URL returned HTTP {http_status}"
                
                return ValidateSourceResponse(
                    url=url,
                    is_accessible=is_accessible,
                    is_scrapeable=is_scrapeable,
                    http_status=http_status,
                    message=message
                )
                
            except httpx.TimeoutException:
                return ValidateSourceResponse(
                    url=url,
                    is_accessible=False,
                    is_scrapeable=False,
                    http_status=None,
                    message="Request timed out after 10 seconds"
                )
            except httpx.HTTPError as e:
                return ValidateSourceResponse(
                    url=url,
                    is_accessible=False,
                    is_scrapeable=False,
                    http_status=None,
                    message=f"HTTP error: {str(e)}"
                )
                
    except Exception as e:
        return ValidateSourceResponse(
            url=url,
            is_accessible=False,
            is_scrapeable=False,
            http_status=None,
            message=f"Validation failed: {str(e)}"
        )


@router.get("/config")
async def get_admin_config():
    """
    Get gateway admin configuration.
    
    Returns:
        Current admin settings
    """
    return {"config": ADMIN_CONFIG}


@router.post("/config")
async def update_admin_config(require_confirmation: Optional[bool] = None):
    """
    Update gateway admin configuration.
    
    Args:
        require_confirmation: Whether to require confirmation tokens for destructive ops
        
    Returns:
        Updated configuration
    """
    if require_confirmation is not None:
        ADMIN_CONFIG["require_confirmation"] = require_confirmation

    return {"config": ADMIN_CONFIG}


@router.get("/diagnostics/schema")
async def schema_diagnostics(db: Client = Depends(get_database_client)) -> Dict[str, Any]:
    """
    Diagnose database schema prerequisites for Vecinita.
    
    Validates:
    - RPC function: search_similar_documents exists
    - Table: document_chunks exists
    - Column: embedding column exists with pgvector(384) type
    - Indexes: Required indexes exist on document_chunks
    - Supporting tables: conversations, documents exist
    
    Returns:
        {
            'status': 'ok' | 'warning' | 'error',
            'summary': String summary of issues,
            'errors': List of blocking errors,
            'warnings': List of non-blocking warnings,
            'checks': Detailed results for each check
        }
    
    Use this endpoint to verify your Supabase schema is correctly configured
    before deploying Vecinita to production.
    """
    try:
        result = await validate_schema(db)
        result['summary'] = get_validation_summary(result)
        return result
    except Exception as e:
        logger.error(f"Schema diagnostics error: {e}")
        return {
            'status': 'error',
            'summary': f'Schema diagnostics failed: {str(e)}',
            'errors': [str(e)],
            'warnings': [],
            'checks': {}
        }
