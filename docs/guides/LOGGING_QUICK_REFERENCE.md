# Quick Reference - Enhanced Logging

## The Change You Asked For

**Old way (subprocess):**
```
Running command: C:\...\python.exe -m src.services.scraper.server --input ...
(and that's all you see until it finishes)
```

**New way (direct execution):**
```
✓ Real-time detailed logging as scraping happens
✓ See what's being loaded, how many chunks, any errors
✓ No subprocess overhead, faster execution
✓ Everything flows through the same logger
```

## Commands

### Normal scraping (INFO level only)
```bash
python -m src.cli --stream
```

### With all debug details
```bash
python -m src.cli --stream --verbose
```

### Debug mode + verbose
```bash
python -m src.cli --stream --verbose --debug
```

## What You'll See Now

### INFO level (default)
```
INFO  | Initializing scraper...
INFO  | Scraper initialized successfully
INFO  | Starting scraping process...
INFO  | SUCCESS: https://example.com (42 chunks, 8 links)
INFO  | Initial scrape completed
```

### DEBUG level (with --verbose)
```
DEBUG | Initializing VecinaScraper with output_file=...
DEBUG | ScraperConfig loaded: rate_limit=2.0s
DEBUG | SmartLoader initialized
DEBUG | DocumentProcessor initialized: chunk_size=1000, overlap=200
DEBUG | [Loading] Attempting to load: https://example.com
DEBUG | [Load Result] Loader type: unstructured, Success: True, Docs: 1
DEBUG | [Processing] Processing 1 document(s)
DEBUG | [Processing Result] Chunks written: 42, Links extracted: 8
```

## Key Improvements

| Before | After |
|--------|-------|
| Single command line shown | Full real-time logging |
| Wait until done to see results | See progress as it happens |
| Subprocess overhead | Direct execution (faster) |
| Limited error info | Full exception tracebacks |
| Can't see initialization | See all config and module setup |

## Implementation

- Scraper now imported directly (no subprocess)
- Logger hierarchy: `vecinita_pipeline.scraper`, `.loaders`, `.processors`
- All logging flows through CLI logger in real-time
- DEBUG messages controlled by `--verbose` flag
- Both scraping stages (initial + Playwright) enhanced

## Files Changed

- `src/cli/data_scrape_load.py` - Direct scraper execution
- `src/utils/scraper/scraper.py` - Detailed logging added
- `src/utils/scraper/loaders.py` - Logger hierarchy updated
- `src/utils/scraper/processors.py` - Logger hierarchy updated

## No Breaking Changes

Everything still works exactly the same way, just with much better visibility into what's happening.
