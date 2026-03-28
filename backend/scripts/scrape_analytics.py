"""
Analytics queries for scraping and embedding tracking.
"""
import os
from typing import List, Dict, Any, Optional
import psycopg2
from datetime import datetime


class ScrapeAnalytics:
    def __init__(self, database_url: str):
        self.conn = psycopg2.connect(database_url)

    def get_last_scrape_by_model(self) -> List[Dict[str, Any]]:
        """Get last scrape time for each embedding model."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    provider,
                    model,
                    table_name,
                    last_used_at,
                    chunks_count
                FROM embedding_metadata
                ORDER BY last_used_at DESC NULLS LAST;
            """)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_scrape_timeline(self, source_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get timeline of when sources were last scraped per model."""
        with self.conn.cursor() as cur:
            query = """
                SELECT 
                    source_url,
                    last_scraped_at,
                    (last_scrape_by_model)::jsonb as models_used,
                    scrape_count
                FROM document_sources
            """
            if source_url:
                query += " WHERE source_url = %s"
                cur.execute(query, (source_url,))
            else:
                cur.execute(query)

            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_chunks_by_model(self, model: str = None) -> Dict[str, int]:
        """Count chunks per embedding model."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    provider,
                    model,
                    chunks_count
                FROM embedding_metadata;
            """)
            return {f"{row[0]}_{row[1]}": row[2] for row in cur.fetchall()}

    def get_scrape_stats(self) -> Dict[str, Any]:
        """Get overall scraping statistics."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT source_url) as total_sources,
                    COUNT(*) as total_chunks,
                    SUM(COALESCE(chunk_size, 0)) as total_characters,
                    MAX(last_scraped_at) as last_scrape_time,
                    AVG(scrape_count) as avg_scrapes_per_source
                FROM document_sources;
            """)
            row = cur.fetchone()
            return {
                "total_sources": row[0],
                "total_chunks": row[1],
                "total_characters": row[2],
                "last_scrape_time": row[3],
                "avg_scrapes_per_source": row[4]
            }

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    analytics = ScrapeAnalytics(db_url)

    print("=== Last Scrape by Model ===")
    for record in analytics.get_last_scrape_by_model():
        print(record)

    print("\n=== Chunks by Model ===")
    for model, count in analytics.get_chunks_by_model().items():
        print(f"{model}: {count} chunks")

    print("\n=== Overall Stats ===")
    print(analytics.get_scrape_stats())

    analytics.close()
