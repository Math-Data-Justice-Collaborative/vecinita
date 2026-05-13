# User Journeys Diagram: Indexing Worker
> Auto-generated: 2026-05-12

## Journey 1: Single-Document Indexing

```mermaid
journey
    title Single-Document Indexing
    section Trigger
      Gateway receives index request: 5: Gateway
      Invoke index_document via Modal SDK: 4: Gateway
    section Processing
      Read document from PostgreSQL: 5: Indexing Worker
      Chunk document (SentenceSplitter): 5: Indexing Worker
      Generate embeddings on GPU: 4: Indexing Worker
      Delete old vectors: 5: Indexing Worker
      Insert new vectors: 5: Indexing Worker
      Update content hash: 5: Indexing Worker
    section Result
      Return IndexingResult: 5: Indexing Worker
      Gateway receives confirmation: 5: Gateway
```

## Journey 2: Batch Indexing

```mermaid
journey
    title Batch Indexing (Multiple Documents)
    section Trigger
      Gateway submits batch request: 5: Gateway
      Invoke index_batch via Modal SDK: 4: Gateway
    section Validation
      Validate batch size <= 100: 5: Indexing Worker
    section Processing
      Create indexing_jobs record: 5: Indexing Worker
      Fan out via spawn_map: 4: Indexing Worker
      Parallel GPU containers process: 3: Modal Platform
      Aggregate results: 4: Indexing Worker
    section Result
      Return aggregated IndexingResult: 5: Indexing Worker
      Gateway receives summary: 5: Gateway
```

## Journey 3: Selective Re-Indexing

```mermaid
journey
    title Selective Re-Indexing (Changed Content Only)
    section Trigger
      Gateway requests re-index for source: 5: Gateway
      Invoke reindex_changed via Modal SDK: 4: Gateway
    section Detection
      Load all documents for source: 5: Indexing Worker
      Load stored content hashes: 5: Indexing Worker
      Compute current SHA-256 hashes: 5: Indexing Worker
      Compare current vs stored hashes: 5: Indexing Worker
    section Processing
      Skip unchanged documents: 5: Indexing Worker
      Index changed documents via spawn_map: 4: Indexing Worker
      Update content hashes: 5: Indexing Worker
    section Result
      Return result with skip count: 5: Indexing Worker
      Gateway sees efficiency metrics: 5: Gateway
```

## Journey 4: Full Vector Rebuild

```mermaid
journey
    title Full Vector Rebuild (Model Change)
    section Trigger
      Operator initiates rebuild: 5: Operator
      Gateway spawns rebuild_all: 4: Gateway
    section Safety Checks
      Verify confirm flag: 5: Indexing Worker
      Check no concurrent rebuild: 5: Indexing Worker
    section Cleanup
      Delete all existing vectors: 3: Indexing Worker
      Clear all content hashes: 3: Indexing Worker
    section Processing
      Load all documents: 4: Indexing Worker
      Process in batches via spawn_map: 3: Indexing Worker
      Write new vectors and hashes: 3: Indexing Worker
    section Result
      Return complete IndexingResult: 5: Indexing Worker
      Operator receives confirmation: 5: Operator
```

## Journey 5: Post-Scrape Auto-Indexing

```mermaid
journey
    title Post-Scrape Automatic Indexing
    section Scrape Completes
      Scraper finishes processing URL: 5: Scraper Worker
      Document written to data_mgmt.documents: 5: Scraper Worker
    section Trigger Indexing
      Invoke index_document cross-app: 4: Scraper Worker
    section Processing
      Read newly scraped document: 5: Indexing Worker
      Chunk and embed on GPU: 4: Indexing Worker
      Write vectors to agent.vectors: 5: Indexing Worker
    section Result
      Return success to scraper: 5: Indexing Worker
      Scraper logs indexed_at timestamp: 5: Scraper Worker
      Document is now searchable via RAG: 5: Agent Service
```
