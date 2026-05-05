-- Fix for unprocessed document_chunks
-- This marks all rows with embeddings as processed so they can be searched

UPDATE document_chunks 
SET 
    is_processed = TRUE,
    processing_status = 'completed'
WHERE 
    embedding IS NOT NULL
    AND is_processed = FALSE;

-- Verify the update
SELECT 
    COUNT(*) as total_rows,
    SUM(CASE WHEN is_processed = TRUE THEN 1 ELSE 0 END) as processed_rows,
    SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as rows_with_embeddings
FROM document_chunks;
