# Vecinita Data Directory Structure

## Organization

```
data/
├── input/              # Input files for scraper
│   └── urls.txt        # List of URLs to scrape (MAIN INPUT)
├── output/             # Scraper output files
│   ├── chunks.txt      # Extracted content chunks
│   ├── extracted_links.txt  # Links found during scraping
│   └── failed.txt      # Failed URL log
├── config/             # Scraper configuration
│   ├── playwright_sites.txt    # Sites requiring JS rendering
│   ├── recursive_sites.txt     # Sites for recursive crawling
│   └── skip_sites.txt          # Sites to skip
├── archive/            # Old/manual content
│   └── manual_scraping/   # Manually collected content
└── test_urls/          # Test datasets
    ├── test_urls.txt
    ├── test_urls_small.txt
    ├── test_urls_clean.txt
    └── test_single.txt
```

## File Purposes

### Input (`input/`)
- **urls.txt** - Main URL list for scraping (31 URLs, organized by category)

### Output (`output/`)
- **chunks.txt** - Processed document chunks ready for vector storage
- **extracted_links.txt** - Outbound links found during scraping
- **failed.txt** - URLs that failed to scrape (for retry with Playwright)

### Config (`config/`)
- **playwright_sites.txt** - Domains requiring JavaScript rendering
- **recursive_sites.txt** - Sites to crawl recursively (format: `url depth`)
- **skip_sites.txt** - Domains to skip (ToS restrictions, paywalls, etc.)

### Archive (`archive/`)
- Previous scraper runs and manually collected content

### Test (`test_urls/`)
- Test datasets for development and testing

## Usage with Scraper

```bash
# Standard scrape with all URLs
uv run python -m src.scraper.main \
  --input data/input/urls.txt \
  --output-file data/output/chunks.txt \
  --failed-log data/output/failed.txt

# With streaming mode (uploads immediately)
uv run python -m src.scraper.main \
  --input data/input/urls.txt \
  --output-file data/output/chunks.txt \
  --failed-log data/output/failed.txt \
  --stream

# Test with small dataset
uv run python -m src.scraper.main \
  --input data/test_urls/test_urls_small.txt \
  --output-file data/output/chunks.txt \
  --failed-log data/output/failed.txt
```

## Data Pipeline

1. **Input** → `input/urls.txt`
2. **Config** → `config/` (controls behavior)
3. **Scrape** → Fetches content from URLs
4. **Process** → Chunks content, generates embeddings
5. **Output** → `output/` files + Supabase upload
6. **Archive** → Old runs moved to `archive/`

## Content Categories (31 URLs)

| Category | Sites | Purpose |
|----------|-------|---------|
| Education | RIDE, Providence Schools, EnrollRI | School info, enrollment |
| Health | NuestraSalud, HealthSourceRI | Medical info (Spanish/English) |
| Government | DHS, DMV | Social services, licensing |
| Immigration | DIIRI, Catholic Charities, USCIS | Immigration resources |
| Community | RICADV, Hispanic Chamber | Community organizations |
| VECINA | WRWC, QubesHub | Project sites |

---

Last Updated: December 31, 2025
