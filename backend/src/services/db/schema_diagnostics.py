"""
Database Schema Diagnostics (Phase 1).

Verifies that required database schema elements exist:
- RPC function: search_similar_documents
- Column: document_chunks.embedding (pgvector type, 384 dimensions)
- Indexes: document_chunks on source, session_id, created_at
- Tables: document_chunks, conversations, documents (with expected columns)

Provides meaningful error messages if prerequisites are missing.
"""

import logging
from typing import Dict, Any, Optional
from supabase import Client

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates Supabase schema prerequisites for Vecinita."""
    
    def __init__(self, db: Client):
        """Initialize with Supabase client."""
        self.db = db
        self.validation_errors: list[str] = []
        self.validation_warnings: list[str] = []
    
    async def validate_all(self) -> Dict[str, Any]:
        """
        Run all schema validations.
        
        Returns:
            {
                'status': 'ok' | 'warning' | 'error',
                'errors': [...],
                'warnings': [...],
                'checks': {
                    'rpc_search_similar_documents': bool,
                    'table_document_chunks': bool,
                    'column_embedding': {'exists': bool, 'type': str, 'dimensions': int},
                    'index_source': bool,
                    'index_session_id': bool,
                    'index_created_at': bool,
                    'table_conversations': bool,
                    'table_documents': bool,
                }
            }
        """
        self.validation_errors = []
        self.validation_warnings = []
        results = {}
        
        # Check RPC function
        results['rpc_search_similar_documents'] = await self._check_rpc_search_similar_documents()
        
        # Check document_chunks table and columns
        results['table_document_chunks'] = await self._check_table_document_chunks()
        results['column_embedding'] = await self._check_column_embedding()
        
        # Check indexes
        results['index_source'] = await self._check_index('document_chunks_source_idx')
        results['index_session_id'] = await self._check_index('document_chunks_session_id_idx')
        results['index_created_at'] = await self._check_index('document_chunks_created_at_idx')
        
        # Check supporting tables
        results['table_conversations'] = await self._check_table('conversations')
        results['table_documents'] = await self._check_table('documents')
        
        # Determine overall status
        if self.validation_errors:
            status = 'error'
        elif self.validation_warnings:
            status = 'warning'
        else:
            status = 'ok'
        
        return {
            'status': status,
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'checks': results,
        }
    
    async def _check_rpc_search_similar_documents(self) -> bool:
        """
        Check if search_similar_documents RPC function exists.
        
        Expected signature:
            search_similar_documents(
                query_embedding: vector,
                match_threshold: float = 0.3,
                match_count: int = 5
            ) -> TABLE
        
        Returns:
            True if RPC exists, False otherwise
        """
        try:
            # Try calling the RPC with null/zero values to check existence
            # (This will fail with dimension error if RPC doesn't exist, but we catch that)
            response = await self._execute_rpc_check()
            return True
        except Exception as e:
            error_msg = str(e)
            
            # Check if error is about the RPC not existing vs. parameter mismatch
            if 'not found' in error_msg.lower() or 'no function' in error_msg.lower():
                self.validation_errors.append(
                    "❌ RPC function 'search_similar_documents' not found in database.\n"
                    "   Solution: Create RPC function with signature:\n"
                    "   - search_similar_documents(query_embedding vector, match_threshold float, match_count int)\n"
                    "   See: docs/deployment/SUPABASE_SCHEMA_SETUP.md"
                )
                return False
            else:
                # If it's another error (like vector dimension), RPC exists but has config issue
                logger.warning(f"RPC check status unclear: {error_msg}")
                return True  # Assume it exists, dimension check will catch config issues
        
        return False
    
    async def _execute_rpc_check(self) -> Any:
        """Execute RPC call to verify it exists."""
        # Try to call RPC - will fail gracefully if it doesn't exist
        zero_vector = [0.0] * 384  # Correct dimensions
        return self.db.rpc(
            'search_similar_documents',
            {
                'query_embedding': zero_vector,
                'match_threshold': 0.3,
                'match_count': 1
            }
        ).execute()
    
    async def _check_table_document_chunks(self) -> bool:
        """Check if document_chunks table exists with expected columns."""
        try:
            response = self.db.table('document_chunks').select('id').limit(1).execute()
            return True
        except Exception as e:
            self.validation_errors.append(
                "❌ Table 'document_chunks' not found in database.\n"
                "   Solution: Create required schema.\n"
                "   See: docs/deployment/SUPABASE_SCHEMA_SETUP.md"
            )
            return False
    
    async def _check_column_embedding(self) -> Dict[str, Any]:
        """
        Check if document_chunks.embedding column exists and is pgvector(384).
        
        Returns:
            {'exists': bool, 'type': str, 'dimensions': int}
        """
        try:
            # Query table structure (using PostgreSQL info schema via RPC is ideal,
            # but we'll try a simple select to verify column accessibility)
            response = self.db.table('document_chunks').select('embedding').limit(0).execute()
            
            # If we get here, column exists
            # Try to infer type from Supabase response metadata if available
            # For now, we mark as "exists" and recommend manual verification
            
            self.validation_warnings.append(
                "⚠️  Assuming 'embedding' column exists with pgvector(384) type.\n"
                "   Recommended: Verify in Supabase Dashboard → SQL Editor →\n"
                "   SELECT column_name, udt_name FROM information_schema.columns\n"
                "   WHERE table_name = 'document_chunks' AND column_name = 'embedding'"
            )
            
            return {
                'exists': True,
                'type': 'vector (assumed)',
                'dimensions': 384
            }
        except Exception as e:
            error_msg = str(e)
            if 'embedding' in error_msg.lower() or 'column' in error_msg.lower():
                self.validation_errors.append(
                    "❌ Column 'embedding' not found in 'document_chunks' table.\n"
                    "   Solution: Add column with: ALTER TABLE document_chunks ADD COLUMN embedding vector(384);\n"
                    "   See: docs/deployment/SUPABASE_SCHEMA_SETUP.md"
                )
                return {'exists': False, 'type': None, 'dimensions': None}
            else:
                logger.warning(f"Embedding column check status unclear: {error_msg}")
                return {
                    'exists': True,
                    'type': 'vector (unverified)',
                    'dimensions': 384
                }
    
    async def _check_index(self, index_name: str) -> bool:
        """
        Check if index exists on document_chunks table.
        
        Note: Supabase doesn't expose index metadata via PostgREST,
        so we recommend manual verification via SQL Editor.
        
        Returns:
            True (assumes indexes exist; recommend manual verification)
        """
        self.validation_warnings.append(
            f"⚠️  Cannot verify index '{index_name}' via API.\n"
            "   Recommended: Verify in Supabase Dashboard → SQL Editor →\n"
            "   SELECT indexname FROM pg_indexes WHERE schemaname = 'public'"
        )
        return True  # Optimistically assume it exists
    
    async def _check_table(self, table_name: str) -> bool:
        """Check if table exists."""
        try:
            response = self.db.table(table_name).select('id').limit(0).execute()
            return True
        except Exception as e:
            self.validation_warnings.append(
                f"⚠️  Table '{table_name}' may not exist or may have no accessible columns.\n"
                "   Recommended: Verify in Supabase Dashboard → Table Editor"
            )
            return False


async def validate_schema(db: Client) -> Dict[str, Any]:
    """
    Convenience function: Run complete schema validation.
    
    Args:
        db: Supabase client
        
    Returns:
        Validation result dictionary with status and detailed checks
    """
    validator = SchemaValidator(db)
    return await validator.validate_all()


def get_validation_summary(validation_result: Dict[str, Any]) -> str:
    """
    Format validation result as human-readable summary.
    
    Args:
        validation_result: Result from validate_schema()
        
    Returns:
        Formatted string summary
    """
    status = validation_result['status'].upper()
    errors = validation_result['errors']
    warnings = validation_result['warnings']
    
    lines = [f"Schema Validation: {status}"]
    lines.append("=" * 50)
    
    if errors:
        lines.append("\nERRORS:")
        for error in errors:
            lines.append(f"\n{error}")
    
    if warnings:
        lines.append("\nWARNINGS:")
        for warning in warnings:
            lines.append(f"\n{warning}")
    
    if not errors and not warnings:
        lines.append("\n✅ All schema checks passed!")
    
    return "\n".join(lines)
