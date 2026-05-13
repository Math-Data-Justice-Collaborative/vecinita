# RAG Vector Database Backend API Specification

This document describes the backend API endpoints that the RAG Admin interface expects.

## Configuration

Set the environment variable `REACT_APP_RAG_API_URL` to your backend API base URL.

Example: `REACT_APP_RAG_API_URL=https://api.example.com/v1`

If not set, the application runs in **mock mode** with demo data.

## API Endpoints

### Corpus Management

#### `GET /documents`
Retrieve all documents in the corpus with filtering and pagination.

**Query Parameters:**
- `page` (number, optional): Page number for pagination
- `limit` (number, optional): Number of documents per page
- `search` (string, optional): Search query for document titles
- `resource_type` (string, optional): Filter by resource type
- `language` (string, optional): Filter by language
- `tags` (string, optional): Comma-separated list of tags

**Response:**
```json
{
  "documents": [/* array of Document objects */],
  "total": 100,
  "page": 1
}
```

#### `GET /documents/:id`
Retrieve a specific document by ID.

**Response:** Document object

#### `POST /documents`
Create a new document manually.

**Request Body:**
```json
{
  "title": "Document Title",
  "description": "Brief summary",
  "url": "https://example.com",
  "resource_type": "website|document|organization|dataset|service",
  "format": "HTML|PDF|API|video|TXT|DOCX|other",
  "language": "English",
  "organization": "Organization Name",
  "content": "Optional content text",
  "tags": ["tag1", "tag2"]
}
```

**Response:** Created Document object

#### `PUT /documents/:id`
Update an existing document.

**Request Body:** Partial Document object with fields to update

**Response:** Updated Document object

#### `DELETE /documents/:id`
Delete a document from the corpus and vector database.

**Response:**
```json
{
  "success": true
}
```

#### `DELETE /documents/bulk-delete`
Bulk delete multiple documents.

**Request Body:**
```json
{
  "ids": ["id1", "id2", "id3"]
}
```

**Response:**
```json
{
  "success": true,
  "deleted_count": 3
}
```

### URL Scraping

#### `POST /scrape`
Initiate URL scraping job.

**Request Body:**
```json
{
  "url": "https://example.com",
  "depth": 2,
  "auto_tag": true
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued|processing",
  "estimated_pages": 15
}
```

#### `GET /scrape/:job_id`
Get scraping job status.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued|processing|completed|failed",
  "progress": 75,
  "pages_scraped": 12,
  "documents_created": ["doc_id1", "doc_id2"],
  "error": "Optional error message"
}
```

#### `GET /scrape/jobs`
Get all scraping jobs.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "abc123",
      "url": "https://example.com",
      "depth": 2,
      "status": "completed",
      "created_at": "2026-03-12T10:00:00Z",
      "completed_at": "2026-03-12T10:05:00Z"
    }
  ]
}
```

### Document Upload

#### `POST /upload`
Upload a document file (PDF, DOCX, TXT, etc.).

**Request:** multipart/form-data
- `file`: File to upload
- `auto_tag` (optional): "true" or "false"
- `metadata` (optional): JSON string with document metadata

**Response:**
```json
{
  "document_id": "doc123",
  "status": "processing|completed"
}
```

### Auto-Tagging

#### `POST /tags/auto-generate`
Generate tags for a document using AI.

**Request Body:**
```json
{
  "document_id": "doc123"
}
```

**Response:**
```json
{
  "document_id": "doc123",
  "suggestions": [
    { "tag": "machine-learning", "confidence": 0.95 },
    { "tag": "research", "confidence": 0.87 }
  ],
  "metadata": {
    "description": "Auto-generated description",
    "organization": "Detected organization"
  }
}
```

#### `POST /tags/apply`
Apply tags to a document.

**Request Body:**
```json
{
  "document_id": "doc123",
  "tags": ["tag1", "tag2"],
  "metadata": { /* optional metadata updates */ }
}
```

**Response:** Updated Document object

#### `GET /tags`
Get all unique tags in the corpus.

**Response:**
```json
{
  "tags": ["tag1", "tag2", "tag3"],
  "tag_counts": {
    "tag1": 15,
    "tag2": 8,
    "tag3": 3
  }
}
```

### Vector Database Operations

#### `POST /embeddings/generate`
Generate embeddings for a document.

**Request Body:**
```json
{
  "document_id": "doc123"
}
```

**Response:**
```json
{
  "document_id": "doc123",
  "status": "completed|failed",
  "vector_count": 42
}
```

#### `POST /embeddings/search`
Semantic search in the vector database.

**Request Body:**
```json
{
  "query": "search query text",
  "filters": {
    "resource_type": ["website", "document"],
    "language": "English",
    "tags": ["tag1"],
    "limit": 10
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "document": { /* Document object */ },
      "score": 0.95,
      "matched_chunks": ["relevant text chunk 1", "chunk 2"]
    }
  ]
}
```

#### `GET /stats`
Get corpus statistics.

**Response:**
```json
{
  "total_documents": 156,
  "total_embeddings": 3420,
  "documents_by_type": {
    "website": 45,
    "document": 89,
    "dataset": 22
  },
  "documents_by_language": {
    "English": 120,
    "Spanish": 36
  },
  "recent_documents": [/* array of recent Document objects */]
}
```

## Document Object Schema

```typescript
interface Document {
  id: string;
  title: string;
  description: string;
  url: string;
  resource_type: 'website' | 'document' | 'organization' | 'dataset' | 'service';
  format: 'HTML' | 'PDF' | 'API' | 'video' | 'TXT' | 'DOCX' | 'other';
  language: string;
  organization: string;
  content?: string;
  embedding_status?: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string; // ISO 8601 timestamp
  updated_at: string; // ISO 8601 timestamp
  tags?: string[];
  scrape_depth?: number;
}
```

## Metadata Tags

The system supports the following standard metadata tags:

| Tag             | Description          | Type     |
| --------------- | -------------------- | -------- |
| `title`         | Name of the resource | string   |
| `description`   | Short summary        | string   |
| `url`           | Primary link         | string   |
| `resource_type` | Type of resource     | enum     |
| `format`        | File/content format  | enum     |
| `language`      | Content language     | string   |
| `organization`  | Provider or owner    | string   |
| `tags`          | Custom tags          | string[] |

## Error Handling

All endpoints should return appropriate HTTP status codes:
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "message": "Error description",
  "details": "Optional detailed error information"
}
```
