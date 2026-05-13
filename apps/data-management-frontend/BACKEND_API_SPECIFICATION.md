# RAG Vector Database API Specification

This document outlines the complete backend API required for the RAG Admin Dashboard.

## Table of Contents

1. [Base Configuration](#base-configuration)
2. [Data Models](#data-models)
3. [API Endpoints](#api-endpoints)
   - [Corpus Management](#corpus-management)
   - [URL Scraping](#url-scraping)
   - [Document Upload](#document-upload)
   - [Auto-Tagging](#auto-tagging)
   - [Vector Database Operations](#vector-database-operations)
   - [Statistics](#statistics)

---

## Base Configuration

**Base URL**: Set via environment variable `REACT_APP_RAG_API_URL`

**Example**: `https://api.example.com/v1/rag`

**Headers**: All requests should include:
```
Content-Type: application/json
Authorization: Bearer <token> (if authentication is required)
```

---

## Data Models

### Document

The core data model representing a document in the corpus.

```typescript
interface Document {
  // Core identification
  id: string;                    // Unique identifier
  title: string;                 // Name of the resource
  description: string;           // Short summary
  url: string;                   // Primary link or file path
  
  // Resource metadata
  resource_type: 'website' | 'document' | 'organization' | 'dataset' | 'service';
  format: 'HTML' | 'PDF' | 'API' | 'video' | 'TXT' | 'DOCX' | 'other';
  language: string;              // e.g., "English", "Spanish", "Portuguese"
  organization: string;          // Provider or owner
  
  // Content
  content?: string;              // Full text content (optional, can be large)
  
  // System metadata
  embedding_status?: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;            // ISO 8601 timestamp
  updated_at: string;            // ISO 8601 timestamp
  
  // Categorization
  tags?: string[];               // Array of tags
  scrape_depth?: number;         // Crawl depth for scraped URLs
  
  // Extended metadata (based on nonprofit resource hub schema)
  // Topic/Category
  category?: string;             // e.g., "housing", "healthcare", "food-assistance"
  subtopic?: string;
  program_type?: string;
  
  // Audience
  target_population?: string[];  // e.g., ["immigrants", "seniors", "veterans"]
  age_group?: string;            // e.g., "children", "youth", "adults"
  income_level?: string;         // e.g., "low-income"
  eligibility?: string;
  accessibility?: string;
  
  // Geographic
  country?: string;
  state?: string;
  city?: string;
  region?: string;
  service_area?: string;
  location_coordinates?: { lat: number; lng: number };
  
  // Access & Logistics
  cost?: string;                 // e.g., "free", "$10"
  appointment_required?: boolean;
  application_required?: boolean;
  hours?: string;
  contact_phone?: string;
  contact_email?: string;
  
  // Data Quality
  verified?: boolean;
  last_verified_date?: string;
  source?: string;
  confidence_score?: number;
  status?: 'active' | 'archived';
  
  // Document-specific
  document_type?: string;        // e.g., "report", "guide", "policy"
  author?: string;
  publication_date?: string;
  file_size?: number;
  version?: string;
  
  // AI/Search
  embedding_text?: string;       // Cleaned text for embeddings
  keywords?: string[];
  summary?: string;              // AI-generated summary
  related_resources?: string[];  // IDs of related documents
  popularity_score?: number;
}
```

### Tag Suggestion

Used for AI-generated tag suggestions.

```typescript
interface TagSuggestion {
  tag: string;                   // Suggested tag
  confidence: number;            // Confidence score (0-1)
}
```

### Scrape Request

Request payload for URL scraping.

```typescript
interface ScrapeRequest {
  url: string;                   // URL to scrape
  depth: number;                 // Crawl depth (0 = single page, 1+ = follow links)
  auto_tag?: boolean;            // Whether to auto-generate tags (default: false)
  config?: {
    content_selector?: string;   // CSS selectors for main content
    strip_boilerplate?: boolean; // Remove navigation, ads, footer
    normalize_whitespace?: boolean; // Clean formatting
    allowed_domains?: string[];  // Restrict crawl to specific domains
    max_pages?: number;          // Maximum pages to crawl
    request_timeout?: number;    // Request timeout in seconds
    rate_limit?: number;         // Requests per second
    user_agent?: string;         // User agent string
    deduplicate_content?: boolean; // Remove duplicate pages
  };
  processing?: {
    chunk_size?: number;         // Tokens per chunk
    chunk_overlap?: number;      // Overlap between chunks
    min_chunk_length?: number;   // Skip fragments smaller than this
    max_chunk_length?: number;   // Maximum chunk size
    split_method?: string;       // How to split text
    preserve_headers?: boolean;  // Keep section headers for context
  };
}
```

---

## API Endpoints

### Corpus Management

#### 1. List Documents

Get a paginated list of documents with optional filters.

**Endpoint**: `GET /documents`

**Query Parameters**:
```typescript
{
  page?: number;              // Page number (default: 1)
  limit?: number;             // Items per page (default: 20)
  search?: string;            // Search query (searches title, description, content)
  resource_type?: string;     // Filter by resource type
  language?: string;          // Filter by language
  tags?: string;              // Comma-separated tags (e.g., "housing,food-assistance")
  category?: string;          // Filter by category
  organization?: string;      // Filter by organization
  verified?: boolean;         // Filter by verification status
  status?: string;            // Filter by status (active/archived)
}
```

**Response**: `200 OK`
```json
{
  "documents": [
    {
      "id": "doc-123",
      "title": "RI Food Bank Community Resources",
      "description": "Directory of food assistance programs across Rhode Island",
      "url": "https://rifoodbank.org/community-resources",
      "resource_type": "website",
      "format": "HTML",
      "language": "English",
      "organization": "Rhode Island Food Bank",
      "embedding_status": "completed",
      "created_at": "2026-03-11T10:00:00Z",
      "updated_at": "2026-03-12T10:00:00Z",
      "tags": ["food-assistance", "community", "resources"],
      "category": "food-assistance",
      "target_population": ["low-income families", "seniors"],
      "state": "Rhode Island",
      "service_area": "statewide",
      "cost": "free",
      "verified": true,
      "last_verified_date": "2026-02-01T00:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20,
  "pages": 3
}
```

**Error Responses**:
- `400 Bad Request`: Invalid query parameters
- `500 Internal Server Error`: Server error

---

#### 2. Get Document by ID

Retrieve a specific document with full details.

**Endpoint**: `GET /documents/:id`

**Path Parameters**:
- `id` (string, required): Document ID

**Response**: `200 OK`
```json
{
  "id": "doc-123",
  "title": "RI Food Bank Community Resources",
  "description": "Directory of food assistance programs across Rhode Island",
  "url": "https://rifoodbank.org/community-resources",
  "resource_type": "website",
  "format": "HTML",
  "language": "English",
  "organization": "Rhode Island Food Bank",
  "content": "Full text content of the document...",
  "embedding_status": "completed",
  "created_at": "2026-03-11T10:00:00Z",
  "updated_at": "2026-03-12T10:00:00Z",
  "tags": ["food-assistance", "community", "resources"],
  "category": "food-assistance",
  "target_population": ["low-income families", "seniors"],
  "state": "Rhode Island",
  "service_area": "statewide",
  "cost": "free",
  "contact_phone": "(401) 555-1234",
  "contact_email": "help@rifoodbank.org",
  "verified": true,
  "last_verified_date": "2026-02-01T00:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Document not found
- `500 Internal Server Error`: Server error

---

#### 3. Create Document

Manually create a new document in the corpus.

**Endpoint**: `POST /documents`

**Request Body**:
```json
{
  "title": "New Resource",
  "description": "Description of the resource",
  "url": "https://example.com/resource",
  "resource_type": "website",
  "format": "HTML",
  "language": "English",
  "organization": "Example Organization",
  "content": "Optional full text content",
  "tags": ["tag1", "tag2"],
  "category": "healthcare",
  "target_population": ["seniors"],
  "state": "Rhode Island",
  "cost": "free",
  "verified": true
}
```

**Response**: `201 Created`
```json
{
  "id": "doc-456",
  "title": "New Resource",
  "description": "Description of the resource",
  "url": "https://example.com/resource",
  "resource_type": "website",
  "format": "HTML",
  "language": "English",
  "organization": "Example Organization",
  "embedding_status": "pending",
  "created_at": "2026-03-12T10:00:00Z",
  "updated_at": "2026-03-12T10:00:00Z",
  "tags": ["tag1", "tag2"],
  "category": "healthcare",
  "target_population": ["seniors"],
  "state": "Rhode Island",
  "cost": "free",
  "verified": true
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request body or missing required fields
- `409 Conflict`: Document with same URL already exists
- `500 Internal Server Error`: Server error

---

#### 4. Update Document

Update an existing document's metadata.

**Endpoint**: `PUT /documents/:id`

**Path Parameters**:
- `id` (string, required): Document ID

**Request Body**: (All fields optional - only send what needs to be updated)
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "tags": ["new-tag", "another-tag"],
  "category": "housing",
  "verified": true,
  "last_verified_date": "2026-03-12T00:00:00Z"
}
```

**Response**: `200 OK`
```json
{
  "id": "doc-123",
  "title": "Updated Title",
  "description": "Updated description",
  "url": "https://rifoodbank.org/community-resources",
  "resource_type": "website",
  "format": "HTML",
  "language": "English",
  "organization": "Rhode Island Food Bank",
  "embedding_status": "completed",
  "created_at": "2026-03-11T10:00:00Z",
  "updated_at": "2026-03-12T15:30:00Z",
  "tags": ["new-tag", "another-tag"],
  "category": "housing",
  "verified": true,
  "last_verified_date": "2026-03-12T00:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request body
- `404 Not Found`: Document not found
- `500 Internal Server Error`: Server error

---

#### 5. Delete Document

Delete a document from the corpus and its embeddings from the vector database.

**Endpoint**: `DELETE /documents/:id`

**Path Parameters**:
- `id` (string, required): Document ID

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Document and embeddings deleted successfully"
}
```

**Error Responses**:
- `404 Not Found`: Document not found
- `500 Internal Server Error`: Server error

---

#### 6. Bulk Delete Documents

Delete multiple documents at once.

**Endpoint**: `DELETE /documents/bulk-delete`

**Request Body**:
```json
{
  "ids": ["doc-123", "doc-456", "doc-789"]
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "deleted_count": 3,
  "message": "3 documents deleted successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request body or empty IDs array
- `500 Internal Server Error`: Server error

---

### URL Scraping

#### 7. Start URL Scrape

Initiate a URL scraping job with optional depth crawling.

**Endpoint**: `POST /scrape`

**Request Body**:
```json
{
  "url": "https://example.com/page",
  "depth": 2,
  "auto_tag": true,
  "config": {
    "content_selector": "article, .main-content",
    "strip_boilerplate": true,
    "normalize_whitespace": true,
    "allowed_domains": ["example.org"],
    "max_pages": 50,
    "request_timeout": 30,
    "rate_limit": 2,
    "user_agent": "RAG-ResourceHub-Bot/1.0",
    "deduplicate_content": true
  },
  "processing": {
    "chunk_size": 512,
    "chunk_overlap": 100,
    "min_chunk_length": 50,
    "max_chunk_length": 1000,
    "split_method": "recursive",
    "preserve_headers": true
  }
}
```

**Field Descriptions**:
- `url` (string, required): The URL to scrape
- `depth` (number, required): Crawl depth
  - `0`: Single page only
  - `1`: Page + immediate links
  - `2+`: Follow links up to N levels deep
- `auto_tag` (boolean, optional): Whether to automatically generate tags using AI (default: false)
- `config` (object, optional): Scraping configuration overrides
  - `content_selector` (string): CSS selectors for main content (e.g., "article, .content, #main")
  - `strip_boilerplate` (boolean): Remove navigation, ads, footer (default: true)
  - `normalize_whitespace` (boolean): Clean formatting (default: true)
  - `allowed_domains` (array): Restrict crawl to specific domains (e.g., ["example.org"])
  - `max_pages` (number): Maximum pages to crawl (default: 100, range: 1-10000)
  - `request_timeout` (number): Request timeout in seconds (default: 30, range: 5-120)
  - `rate_limit` (number): Requests per second (default: 2, range: 0.1-10)
  - `user_agent` (string): User agent string (default: "RAG-ResourceHub-Bot/1.0")
  - `deduplicate_content` (boolean): Remove duplicate pages (default: true)
- `processing` (object, optional): Document processing configuration overrides
  - `chunk_size` (number): Tokens per chunk (default: 512, range: 100-2000)
  - `chunk_overlap` (number): Overlap between chunks (default: 100, range: 0-500)
  - `min_chunk_length` (number): Skip fragments smaller than this (default: 50, range: 10-500)
  - `max_chunk_length` (number): Maximum chunk size (default: 1000, range: 500-5000)
  - `split_method` (string): How to split text - "recursive", "semantic", "paragraph", "sentence" (default: "recursive")
  - `preserve_headers` (boolean): Keep section headers for context (default: true)

**Response**: `202 Accepted`
```json
{
  "job_id": "scrape-abc123",
  "status": "queued",
  "estimated_pages": 15,
  "message": "Scraping job started successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid URL or depth parameter
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

#### 8. Get Scrape Job Status

Check the status of a scraping job.

**Endpoint**: `GET /scrape/:job_id`

**Path Parameters**:
- `job_id` (string, required): Job ID returned from scrape initiation

**Response**: `200 OK`
```json
{
  "job_id": "scrape-abc123",
  "status": "processing",
  "progress": 67,
  "pages_scraped": 10,
  "total_pages": 15,
  "documents_created": ["doc-111", "doc-222", "doc-333"],
  "started_at": "2026-03-12T10:00:00Z",
  "updated_at": "2026-03-12T10:05:00Z",
  "error": null
}
```

**Status Values**:
- `queued`: Job is waiting to start
- `processing`: Currently scraping
- `completed`: Job finished successfully
- `failed`: Job failed with error

**Error Responses**:
- `404 Not Found`: Job ID not found
- `500 Internal Server Error`: Server error

---

#### 9. List Scrape Jobs

Get all scraping jobs (with pagination).

**Endpoint**: `GET /scrape/jobs`

**Query Parameters**:
```typescript
{
  page?: number;              // Page number (default: 1)
  limit?: number;             // Items per page (default: 20)
  status?: string;            // Filter by status
}
```

**Response**: `200 OK`
```json
{
  "jobs": [
    {
      "job_id": "scrape-abc123",
      "url": "https://example.com/page",
      "depth": 2,
      "status": "completed",
      "progress": 100,
      "pages_scraped": 15,
      "documents_created": ["doc-111", "doc-222"],
      "created_at": "2026-03-12T10:00:00Z",
      "completed_at": "2026-03-12T10:10:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 20
}
```

**Error Responses**:
- `500 Internal Server Error`: Server error

---

### Document Upload

#### 10. Upload Document File

Upload a document file (PDF, DOCX, TXT, etc.) for processing.

**Endpoint**: `POST /upload`

**Content-Type**: `multipart/form-data`

**Form Fields**:
- `file` (file, required): The document file
- `auto_tag` (boolean, optional): Whether to auto-generate tags (default: false)
- `metadata` (JSON string, optional): Additional metadata as JSON

**Example Request** (using FormData):
```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('auto_tag', 'true');
formData.append('metadata', JSON.stringify({
  organization: "Example Organization",
  language: "English",
  category: "healthcare"
}));
```

**Response**: `201 Created`
```json
{
  "document_id": "doc-789",
  "status": "processing",
  "filename": "document.pdf",
  "file_size": 1048576,
  "message": "Document uploaded and processing started"
}
```

**Error Responses**:
- `400 Bad Request`: No file provided or invalid file type
- `413 Payload Too Large`: File size exceeds limit
- `415 Unsupported Media Type`: File type not supported
- `500 Internal Server Error`: Server error

**Supported File Types**:
- `application/pdf` (.pdf)
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (.docx)
- `application/msword` (.doc)
- `text/plain` (.txt)
- `text/markdown` (.md)
- `text/html` (.html)

---

### Auto-Tagging

#### 11. Auto-Generate Tags

Generate AI-powered tag suggestions and metadata for a document.

**Endpoint**: `POST /tags/auto-generate`

**Request Body**:
```json
{
  "document_id": "doc-123"
}
```

**Response**: `200 OK`
```json
{
  "document_id": "doc-123",
  "suggestions": [
    {
      "tag": "food-assistance",
      "confidence": 0.95
    },
    {
      "tag": "community-resources",
      "confidence": 0.89
    },
    {
      "tag": "statewide",
      "confidence": 0.78
    }
  ],
  "metadata": {
    "category": "food-assistance",
    "target_population": ["low-income families", "seniors"],
    "service_area": "statewide",
    "summary": "AI-generated summary of the document content..."
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid document ID
- `404 Not Found`: Document not found
- `422 Unprocessable Entity`: Document has no content to analyze
- `500 Internal Server Error`: Server error

---

#### 12. Apply Tags

Apply suggested tags and metadata to a document.

**Endpoint**: `POST /tags/apply`

**Request Body**:
```json
{
  "document_id": "doc-123",
  "tags": ["food-assistance", "community-resources", "statewide"],
  "metadata": {
    "category": "food-assistance",
    "target_population": ["low-income families", "seniors"],
    "service_area": "statewide"
  }
}
```

**Response**: `200 OK`
```json
{
  "id": "doc-123",
  "title": "RI Food Bank Community Resources",
  "tags": ["food-assistance", "community-resources", "statewide"],
  "category": "food-assistance",
  "target_population": ["low-income families", "seniors"],
  "service_area": "statewide",
  "updated_at": "2026-03-12T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request body
- `404 Not Found`: Document not found
- `500 Internal Server Error`: Server error

---

#### 13. Get All Tags

Retrieve all unique tags in the corpus with usage counts.

**Endpoint**: `GET /tags`

**Query Parameters**:
```typescript
{
  min_count?: number;         // Minimum usage count (default: 1)
  category?: string;          // Filter by category type
}
```

**Response**: `200 OK`
```json
{
  "tags": [
    "food-assistance",
    "healthcare",
    "housing",
    "low-income",
    "seniors",
    "statewide"
  ],
  "tag_counts": {
    "food-assistance": 15,
    "healthcare": 23,
    "housing": 18,
    "low-income": 31,
    "seniors": 12,
    "statewide": 27
  },
  "total_tags": 6,
  "total_usage": 126
}
```

**Error Responses**:
- `500 Internal Server Error`: Server error

---

### Vector Database Operations

#### 14. Generate Embeddings

Generate vector embeddings for a document.

**Endpoint**: `POST /embeddings/generate`

**Request Body**:
```json
{
  "document_id": "doc-123"
}
```

**Response**: `200 OK`
```json
{
  "document_id": "doc-123",
  "status": "completed",
  "vector_count": 42,
  "embedding_model": "text-embedding-ada-002",
  "chunk_size": 512,
  "message": "Embeddings generated successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid document ID
- `404 Not Found`: Document not found
- `422 Unprocessable Entity`: Document has no content to embed
- `500 Internal Server Error`: Server error

---

#### 15. Semantic Search

Perform semantic search across the vector database.

**Endpoint**: `POST /embeddings/search`

**Request Body**:
```json
{
  "query": "food assistance programs for seniors in Providence",
  "filters": {
    "resource_type": ["website", "document"],
    "language": "English",
    "tags": ["food-assistance", "seniors"],
    "category": "food-assistance",
    "state": "Rhode Island",
    "verified": true
  },
  "limit": 10
}
```

**Field Descriptions**:
- `query` (string, required): The search query
- `filters` (object, optional): Metadata filters to apply
  - `resource_type` (array): Filter by resource types
  - `language` (string): Filter by language
  - `tags` (array): Documents must have all these tags
  - `category` (string): Filter by category
  - `state` (string): Filter by state
  - `verified` (boolean): Filter by verification status
- `limit` (number, optional): Maximum results to return (default: 10, max: 100)

**Response**: `200 OK`
```json
{
  "results": [
    {
      "document": {
        "id": "doc-123",
        "title": "RI Food Bank Community Resources",
        "description": "Directory of food assistance programs",
        "url": "https://rifoodbank.org/community-resources",
        "resource_type": "website",
        "tags": ["food-assistance", "seniors", "statewide"]
      },
      "score": 0.89,
      "matched_chunks": [
        "The Rhode Island Food Bank provides food assistance programs for seniors throughout Providence...",
        "Senior-specific programs include home delivery and nutrition education..."
      ]
    }
  ],
  "total_results": 1,
  "query": "food assistance programs for seniors in Providence"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid query or filters
- `500 Internal Server Error`: Server error

---

### Statistics

#### 16. Get Corpus Statistics

Retrieve overall statistics about the corpus.

**Endpoint**: `GET /stats`

**Response**: `200 OK`
```json
{
  "total_documents": 156,
  "total_embeddings": 3420,
  "total_tags": 47,
  "documents_by_type": {
    "website": 89,
    "document": 45,
    "organization": 12,
    "dataset": 7,
    "service": 3
  },
  "documents_by_language": {
    "English": 132,
    "Spanish": 18,
    "Portuguese": 6
  },
  "documents_by_status": {
    "completed": 142,
    "processing": 8,
    "failed": 3,
    "pending": 3
  },
  "documents_by_category": {
    "food-assistance": 34,
    "housing": 28,
    "healthcare": 41,
    "legal-aid": 19,
    "education": 15,
    "other": 19
  },
  "recent_documents": [
    {
      "id": "doc-456",
      "title": "Recently Added Resource",
      "created_at": "2026-03-12T10:00:00Z"
    }
  ],
  "updated_at": "2026-03-12T10:35:00Z"
}
```

**Error Responses**:
- `500 Internal Server Error`: Server error

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context about the error"
    }
  }
}
```

**Common Error Codes**:
- `INVALID_REQUEST`: Request validation failed
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

---

## Rate Limiting

**Rate Limits**:
- Standard endpoints: 100 requests/minute
- Scraping endpoint: 10 requests/minute
- Upload endpoint: 20 requests/minute

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1678634400
```

---

## Authentication (Optional)

If your backend requires authentication, include the token in the Authorization header:

```
Authorization: Bearer <your-api-token>
```

---

## Webhook Events (Optional)

If your backend supports webhooks, you can configure them to receive real-time updates:

**Webhook Events**:
- `document.created`: New document added
- `document.updated`: Document metadata updated
- `document.deleted`: Document removed
- `scrape.completed`: Scraping job finished
- `scrape.failed`: Scraping job failed
- `embeddings.completed`: Embeddings generated

**Webhook Payload Example**:
```json
{
  "event": "document.created",
  "timestamp": "2026-03-12T10:00:00Z",
  "data": {
    "document_id": "doc-123",
    "title": "New Resource"
  }
}
```

---

## Testing the API

### Using cURL

**Get all documents**:
```bash
curl -X GET "https://api.example.com/v1/rag/documents?page=1&limit=20" \
  -H "Content-Type: application/json"
```

**Create a document**:
```bash
curl -X POST "https://api.example.com/v1/rag/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Resource",
    "description": "A test resource",
    "url": "https://example.com",
    "resource_type": "website",
    "format": "HTML",
    "language": "English",
    "organization": "Test Org"
  }'
```

**Start a scrape job**:
```bash
curl -X POST "https://api.example.com/v1/rag/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "depth": 1,
    "auto_tag": true
  }'
```

**Upload a file**:
```bash
curl -X POST "https://api.example.com/v1/rag/upload" \
  -F "file=@document.pdf" \
  -F "auto_tag=true" \
  -F 'metadata={"organization":"Test Org","language":"English"}'
```

---

## Implementation Notes

1. **Vector Database**: The backend should use PostgreSQL with pgvector or another production-grade vector store for storing embeddings.

2. **Embedding Model**: Recommended models:
   - OpenAI: `text-embedding-ada-002` or `text-embedding-3-small`
   - Open source: `sentence-transformers/all-MiniLM-L6-v2`

3. **Document Processing**:
   - PDF: Use libraries like `pypdf` or `pdfplumber`
   - DOCX: Use `python-docx`
   - HTML: Use `BeautifulSoup4` or `playwright` for JavaScript-heavy sites

4. **Auto-Tagging**: Use LLMs (GPT-4, Claude, Llama) to analyze content and suggest tags based on the metadata schema.

5. **Web Scraping**:
   - Respect `robots.txt`
   - Implement rate limiting
   - Use `playwright` or `selenium` for JavaScript-rendered content
   - Consider using `scrapy` for large-scale crawling

6. **Background Jobs**: Use a task queue (Celery, Bull, etc.) for long-running operations like scraping and embedding generation.

7. **Storage**: Store uploaded files in object storage (S3, GCS, Azure Blob) and reference by URL.

---

## Environment Variables

Your backend should support these configuration options:

```bash
# API Configuration
PORT=8000
API_PREFIX=/v1/rag

# Database
DATABASE_URL=postgresql://user:pass@localhost/rag_db
VECTOR_DB_URL=http://localhost:6333  # Qdrant, Weaviate, etc.

# Embeddings
EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_API_KEY=sk-...

# File Upload
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=/tmp/uploads

# Scraping
MAX_SCRAPE_DEPTH=3
SCRAPE_TIMEOUT=30000
USER_AGENT=RAG-Scraper/1.0

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_WINDOW=60000  # 1 minute
RATE_LIMIT_MAX=100
```

---

## Change Log

| Version | Date       | Changes                                    |
|---------|------------|--------------------------------------------|
| 1.0     | 2026-03-12 | Initial API specification                  |

---

## Recommended Tools & Libraries

### Scraping Tools

**For Text Extraction:**

| Tool | Use Case | Installation |
|------|----------|-------------|
| **trafilatura** | Best for extracting main content from HTML | `pip install trafilatura` |
| **newspaper3k** | News articles and blog posts | `pip install newspaper3k` |
| **readability-lxml** | Mozilla Readability algorithm for content extraction | `pip install readability-lxml` |
| **playwright** | JavaScript-heavy sites (React, Vue, Angular) | `pip install playwright` |
| **scrapy** | Large-scale crawling with built-in rate limiting | `pip install scrapy` |

**trafilatura Example:**
```python
import trafilatura

downloaded = trafilatura.fetch_url('https://example.com')
content = trafilatura.extract(
    downloaded,
    include_comments=False,
    include_tables=False,
    no_fallback=False
)
```

**playwright Example (for JS sites):**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://example.com')
    content = page.content()
    browser.close()
```

### Document Processing Tools

**Text Chunking:**

| Tool | Description |
|------|-------------|
| **LangChain** | `RecursiveCharacterTextSplitter` for smart chunking |
| **llama-index** | Document processing and indexing framework |
| **tiktoken** | OpenAI's tokenizer for accurate token counting |

**LangChain Chunking Example:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=100,
    length_function=len,
    separators=["\n\n", "\n", " ", ""]
)

chunks = text_splitter.split_text(document_text)
```

**Semantic Chunking Example:**
```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings

text_splitter = SemanticChunker(
    OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile"
)
docs = text_splitter.create_documents([text])
```

### Vector Database Options

| Database | Best For | Cloud/Self-Hosted |
|----------|----------|-------------------|
| **Pinecone** | Production, managed service | Cloud |
| **Weaviate** | Open source, GraphQL API | Both |
| **Qdrant** | High performance, Rust-based | Both |
| **PostgreSQL + pgvector** | Existing project standard, relational + vector search | Both |
| **Milvus** | Large scale, enterprise | Both |

### Embedding Models

**OpenAI (Recommended for Production):**
- `text-embedding-ada-002` - 1536 dimensions, $0.0001/1K tokens
- `text-embedding-3-small` - 1536 dimensions, $0.00002/1K tokens (5x cheaper)
- `text-embedding-3-large` - 3072 dimensions, best quality

**Open Source (Self-Hosted):**
- `sentence-transformers/all-MiniLM-L6-v2` - 384 dimensions, fast
- `sentence-transformers/all-mpnet-base-v2` - 768 dimensions, better quality
- `BAAI/bge-large-en-v1.5` - 1024 dimensions, state-of-the-art

**Usage Example:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode([
    "First chunk of text",
    "Second chunk of text"
])
```

### Configuration Best Practices

**Scraping Configuration by Content Type:**

| Content Type | Recommended Settings |
|--------------|---------------------|
| **Blog/News** | `content_selector`: "article, .post-content"<br>`strip_boilerplate`: true<br>`rate_limit`: 2 req/sec |
| **Documentation** | `depth`: 2-3<br>`preserve_headers`: true<br>`chunk_size`: 512 |
| **Community Resources** | `auto_tag`: true<br>`extract_metadata`: all fields<br>`rate_limit`: 1-2 req/sec |
| **Government Sites** | `request_timeout`: 60s<br>`rate_limit`: 1 req/sec<br>Respect robots.txt strictly |

**Processing Configuration by Use Case:**

| Use Case | chunk_size | chunk_overlap | split_method |
|----------|-----------|---------------|--------------|
| **Q&A/FAQ** | 300-500 | 50-100 | semantic |
| **Long Documents** | 512-800 | 100-150 | recursive |
| **Technical Docs** | 400-600 | 100 | recursive |
| **Short Content** | 200-400 | 50 | paragraph |

**Metadata Priority for Retrieval:**

Essential metadata fields ranked by impact on retrieval quality:

1. **title** (highest impact) - Direct matching and ranking
2. **category** - Filters 60-80% of irrelevant results
3. **tags** - Semantic grouping and discovery
4. **organization** - Entity-based filtering
5. **location/state** - Geographic relevance (for local resources)
6. **language** - Multilingual support
7. **verified** - Trust/quality signal
8. **date_published** - Freshness ranking
9. **document_type** - Format-based filtering
10. **target_population** - Audience matching

---

For questions or issues, please contact your backend development team.