For a **non-profit resource hub** (links, documents, services, programs, etc.), good metadata should make resources **easy to search, filter, and recommend**. The trick is combining **structural metadata** (what it is) with **contextual metadata** (who it helps and where).

Below is a practical schema that works well for **databases, vector search, or CMS systems**.

---

# Core Identification Metadata

Basic fields every resource should have.

| Tag             | Description          | Example                                                                                  |
| --------------- | -------------------- | ---------------------------------------------------------------------------------------- |
| `title`         | Name of the resource | "RI Food Bank Community Resources"                                                       |
| `description`   | Short summary        | "Directory of food assistance programs across Rhode Island"                              |
| `url`           | Primary link         | [https://rifoodbank.org/community-resources](https://rifoodbank.org/community-resources) |
| `resource_type` | Type of resource     | `website`, `document`, `organization`, `dataset`, `service`                              |
| `format`        | File/content format  | `HTML`, `PDF`, `API`, `video`                                                            |
| `language`      | Content language     | `English`, `Spanish`, `Portuguese`                                                       |
| `organization`  | Provider or owner    | "Rhode Island Food Bank"                                                                 |

---

# Topic / Category Metadata

What the resource is about.

| Tag            | Description           | Examples                                 |
| -------------- | --------------------- | ---------------------------------------- |
| `category`     | High-level grouping   | housing, healthcare, legal               |
| `tags`         | Search keywords       | rent assistance, eviction, utilities     |
| `subtopic`     | More granular subject | tenant rights                            |
| `program_type` | Nature of program     | emergency aid, education, legal services |

Example categories often used in **community resource hubs**:

* housing
* healthcare
* food assistance
* legal aid
* immigration
* employment
* education
* childcare
* transportation
* financial assistance
* mental health
* domestic violence support

---

# Audience Metadata

Who the resource is for.

| Tag                 | Description         | Example                         |
| ------------------- | ------------------- | ------------------------------- |
| `target_population` | Intended group      | immigrants, seniors, veterans   |
| `age_group`         | Age range           | children, youth, adults         |
| `income_level`      | Eligibility bracket | low-income                      |
| `eligibility`       | Requirements        | RI resident, under 200% poverty |
| `accessibility`     | Accessibility info  | wheelchair accessible           |

---

# Geographic Metadata

Very important for local nonprofit directories.

| Tag                    | Description      | Example           |
| ---------------------- | ---------------- | ----------------- |
| `country`              | Country served   | USA               |
| `state`                | State            | Rhode Island      |
| `city`                 | City             | Providence        |
| `region`               | Service region   | statewide         |
| `service_area`         | Geographic scope | Providence County |
| `location_coordinates` | Lat/long         | optional for maps |

---

# Access & Logistics Metadata

| Tag                    | Description               | Example                             |
| ---------------------- | ------------------------- | ----------------------------------- |
| `cost`                 | Cost of service           | free                                |
| `appointment_required` | Whether scheduling needed | true                                |
| `application_required` | Requires application      | yes                                 |
| `hours`                | Availability              | Mon-Fri 9–5                         |
| `contact_phone`        | Phone                     | (401) 555-1234                      |
| `contact_email`        | Email                     | [help@org.org](mailto:help@org.org) |

---

# Data Quality & Maintenance Metadata

Critical for nonprofit hubs.

| Tag                  | Description                |
| -------------------- | -------------------------- |
| `verified`           | Resource reviewed by staff |
| `last_verified_date` | Last time checked          |
| `source`             | Where data came from       |
| `confidence_score`   | Optional ranking           |
| `status`             | active / archived          |

---

# Document Metadata

If you store PDFs, reports, etc.

| Tag                | Description           |
| ------------------ | --------------------- |
| `document_type`    | report, guide, policy |
| `author`           | Author organization   |
| `publication_date` | Date published        |
| `file_size`        | Size                  |
| `version`          | Version               |

---

# AI / Search Optimization Metadata

Helpful if you plan to use **vector search or RAG**.

| Tag                 | Description                |
| ------------------- | -------------------------- |
| `embedding_text`    | Cleaned searchable text    |
| `keywords`          | extracted search terms     |
| `summary`           | AI-generated summary       |
| `related_resources` | links to similar resources |
| `popularity_score`  | ranking metric             |

---

# Example JSON Resource Record

```json
{
  "title": "Rhode Island Food Bank Community Resources",
  "description": "Directory of food assistance programs across Rhode Island.",
  "url": "https://rifoodbank.org/community-resources",
  "resource_type": "website",
  "organization": "Rhode Island Food Bank",
  "category": "food assistance",
  "tags": ["food pantry", "nutrition support", "community programs"],
  "target_population": ["low-income families", "seniors"],
  "state": "Rhode Island",
  "service_area": "statewide",
  "cost": "free",
  "language": ["English", "Spanish"],
  "verified": true,
  "last_verified_date": "2026-02-01"
}
```

---

# High-Value Tags (If You Only Pick 15)

These provide the **most useful filtering power**:

* title
* description
* url
* resource_type
* category
* tags
* organization
* target_population
* service_area
* language
* cost
* eligibility
* contact_phone
* verified
* last_verified_date

---

💡 **Pro tip:**
For systems like the **Vecinita / StoryPath style resource hubs you're working on**, a good architecture is:

* structured metadata (SQL or JSON)
* vector embeddings of description + tags
* filters on category/location

This gives **fast structured filtering + semantic search**.

---

If you'd like, I can also show you:

* **A complete schema for a nonprofit resource database**
* **A tag taxonomy used by large 211 resource directories**
* **A search-optimized tag list (~150 tags)** that works extremely well with vector databases.
