"""
Link tracking for the VECINA scraper.
Extracts and saves URLs and metadata from scraped content.
"""

import logging
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .uploader import DatabaseUploader

log = logging.getLogger(__name__)


class LinkTracker:
    """Tracks and saves extracted links and metadata."""

    def __init__(self, output_file: Optional[str] = None, uploader: Optional['DatabaseUploader'] = None):
        """Initialize with optional output file and database uploader.

        Args:
            output_file: Optional file path to save links summary
            uploader: Optional DatabaseUploader instance to upload links to database
        """
        self.output_file = output_file
        self.uploader = uploader
        self.links: Dict[str, List[str]] = {}
        self.loaders: Dict[str, str] = {}  # Track loader type per source

    def add_links(self, source_url: str, links: List[str], loader_type: str = "Unknown") -> None:
        """
        Add links from a source.

        Args:
            source_url: The URL that was scraped
            links: List of links found
            loader_type: The type of loader used
        """
        if source_url not in self.links:
            self.links[source_url] = links
            self.loaders[source_url] = loader_type
        else:
            self.links[source_url].extend(links)

        log.info(f"--> Tracked {len(links)} links from {source_url}")

    def save_links(self) -> None:
        """Save all tracked links to file and database."""
        # Upload to database if uploader is available
        if self.uploader:
            self._upload_links_to_database()

        # Also save to file for reference
        if self.output_file and self.links:
            self._save_links_to_file()

    def _upload_links_to_database(self) -> None:
        """Upload all tracked links to Supabase database."""
        if not self.uploader or not self.links:
            return

        total_successful = 0
        total_failed = 0

        for source_url, links in self.links.items():
            loader_type = self.loaders.get(source_url, "Unknown")

            # Deduplicate links before uploading
            unique_links = list(set(links))

            successful, failed = self.uploader.upload_links(
                links=unique_links,
                source_url=source_url,
                loader_type=loader_type
            )
            total_successful += successful
            total_failed += failed

        log.info(
            f"--> ✅ Database upload complete: {total_successful} links uploaded, {total_failed} failed"
        )

    def _save_links_to_file(self) -> None:
        """Save links summary to file."""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"LINK EXTRACTION SUMMARY\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"{'='*70}\n\n")

                for source, links in self.links.items():
                    f.write(f"Source: {source}\n")
                    f.write(f"Links found: {len(set(links))}\n")
                    f.write("-" * 70 + "\n")

                    for link in sorted(set(links)):  # Deduplicate and sort
                        f.write(f"  • {link}\n")

                    f.write("\n")

            log.info(
                f"--> ✅ Saved {sum(len(v) for v in self.links.values())} links to {self.output_file}")
        except Exception as e:
            log.error(f"--> ❌ Failed to save links: {e}")

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        return {
            "total_sources": len(self.links),
            "total_links": sum(len(v) for v in self.links.values()),
            "unique_links": sum(len(set(v)) for v in self.links.values())
        }
