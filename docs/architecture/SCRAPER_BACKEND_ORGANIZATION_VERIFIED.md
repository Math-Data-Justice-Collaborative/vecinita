# Scraper Backend Code - Confirmed Organized ✓

## Status: ✅ VERIFIED

All scraper backend code (non-CLI) is confirmed to be in the `src/utils/scraper/` folder.

## Folder Structure

```
src/utils/scraper/
├── __init__.py           (10 lines)   - Package initialization & exports
├── config.py             (90 lines)   - ScraperConfig class
├── loaders.py           (197 lines)   - SmartLoader class
├── processors.py        (171 lines)   - DocumentProcessor class
├── scraper.py           (207 lines)   - VecinaScraper class (main)
├── utils.py             (110 lines)   - Utility functions
├── link_tracker.py       (70 lines)   - LinkTracker class
└── main.py              (144 lines)   - CLI entry point
```

**Total: 999 lines of scraper backend code**

## Module Dependencies

```
VecinaScraper (scraper.py)
├── ScraperConfig (config.py)
├── SmartLoader (loaders.py)
│   └── utils (URL handling, validation)
├── DocumentProcessor (processors.py)
│   └── utils (text cleaning)
├── LinkTracker (link_tracker.py)
└── utils (file I/O, logging)
```

## What Each Module Does

### `config.py` - Configuration Management
- Loads site categorization files
- Manages scraper settings (rate limits, chunk sizes)
- Handles environment configuration

### `loaders.py` - Document Loading
- Routes URLs to appropriate loaders (Playwright, Recursive, Unstructured)
- Handles special cases (GitHub, CSV, PDFs)
- Manages rate limiting and error recovery

### `processors.py` - Document Processing
- Cleans HTML content using BeautifulSoupTransformer
- Chunks documents into manageable pieces
- Extracts metadata and links

### `scraper.py` - Main Orchestrator
- Coordinates all components
- Processes URLs sequentially
- Collects statistics and results
- Writes output files

### `link_tracker.py` - Link Extraction
- Tracks extracted links from documents
- Associates links with source URLs
- Saves link metadata

### `utils.py` - Utility Functions
- Text cleaning and normalization
- URL validation and conversion
- File I/O operations
- Logging helpers

### `server.py` - CLI entry (URL file mode)
- Argument parsing
- Can be run directly: `python -m src.services.scraper.server`
- Initializes scraper and processes URLs

### `__init__.py` - Package
- Marks folder as Python package
- Exports public classes and functions

## How the CLI Uses It

```python
# In src/cli/__main__.py (delegates to pipeline CLI)
from src.services.scraper.scraper import VecinaScraper

# Create scraper instance
scraper = VecinaScraper(
    output_file="data/chunks.txt",      # Where to save chunks
    failed_log="data/failed.txt",       # Where to log failures
    links_file="data/links.txt",        # Where to save links
    stream_mode=True                    # Whether to upload to DB immediately
)

# Process URLs
total, successful, failed = scraper.scrape_urls(urls)

# Get summary and finalize
scraper.print_summary()
scraper.finalize()
```

## Self-Contained Module

All imports within the scraper folder are **internal** (use relative imports):

```python
from .config import ScraperConfig           # Internal
from .loaders import SmartLoader            # Internal
from .processors import DocumentProcessor   # Internal
from .link_tracker import LinkTracker       # Internal
from .utils import write_to_failed_log      # Internal
```

External imports are only standard library and LangChain packages:
- `logging`, `time`, `os`, `sys`
- `langchain-community` (document loaders)
- `langchain-text-splitters`
- `beautifulsoup4`, `requests`

## What's NOT in the Scraper Folder

These are separate, non-scraper modules (correctly placed in `src/utils/`):

1. **db_cli.py** - Database operations
2. **vector_loader.py** - Vector embedding operations
3. **faq_loader.py** - FAQ data loading
4. **html_cleaner.py** - Legacy HTML cleaner (unused by new scraper)
5. **scraper_to_text.py** - OLD legacy scraper (deprecated)

## Verification Commands

```bash
# Import all scraper components
python -c "from src.services.scraper.scraper import VecinaScraper; print('✓ OK')"

# Check module structure
python -c "
from src.services.scraper import config, loaders, processors, scraper, utils
print('✓ All modules present')
"

# Run scraper directly
python -m src.services.scraper.server --help

# Use from CLI
python -m src.cli --stream --verbose
```

## Conclusion

✅ **CONFIRMED**: In-process scraper backend code lives under `src/services/scraper/`

The modular structure provides:
- Clear separation of concerns
- Easy maintenance and testing
- Simple extension mechanism
- Clean import path for CLI: `from src.services.scraper.scraper import VecinaScraper`

No changes needed - the structure is optimal.
