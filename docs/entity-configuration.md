# Entity Type Configuration

This guide explains how to configure entity types for LightRAG knowledge graph construction in the RAG Engine.

## Overview

Entity types guide LightRAG's entity extraction process during document ingestion. By defining specific entity types relevant to your knowledge domain, you can improve the quality and relevance of the extracted knowledge graph.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration File](#configuration-file)
- [API Endpoints](#api-endpoints)
- [Domain-Specific Examples](#domain-specific-examples)
- [Best Practices](#best-practices)
- [LightRAG Integration](#lightrag-integration-epic-3)

---

## Quick Start

### 1. Default Entity Types

The RAG Engine comes pre-configured with 8 general-purpose entity types:

| Entity Type | Description | Examples |
|-------------|-------------|----------|
| `person` | Individual people, including names, roles, and titles | John Doe, Dr. Jane Smith, CEO Bob Johnson |
| `organization` | Companies, institutions, agencies, and groups | Microsoft Corporation, Stanford University, WHO |
| `concept` | Abstract ideas, theories, methodologies, and principles | Machine Learning, Agile Methodology, Six Sigma |
| `product` | Products, services, tools, and offerings | iPhone 15, Microsoft Azure, AWS Lambda |
| `location` | Geographic locations, places, addresses, and regions | San Francisco, CA, Building A Floor 3 |
| `technology` | Technologies, frameworks, programming languages, and tools | Python, React.js, Docker, Neo4j |
| `event` | Events, meetings, conferences, and significant occurrences | AWS re:Invent 2025, Product Launch |
| `document` | Documents, reports, policies, and written materials | Employee Handbook, API Documentation |

### 2. Viewing Current Entity Types

Query the GET endpoint to see all configured entity types:

```bash
curl http://localhost:8000/api/v1/config/entity-types
```

Example response:

```json
{
  "entity_types": [
    {
      "type_name": "person",
      "description": "Individual people, including names, roles, and titles",
      "examples": ["John Doe", "Dr. Jane Smith", "CEO Bob Johnson"]
    },
    ...
  ]
}
```

### 3. Adding Custom Entity Types

Add a new entity type using the POST endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/config/entity-types \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type_name": "patent",
    "description": "Patents, intellectual property, and inventions",
    "examples": ["US Patent 10,123,456", "European Patent EP1234567"]
  }'
```

**Note:** POST endpoint requires authentication via `Authorization: Bearer <API_KEY>` header.

---

## Configuration File

### Location

The entity types configuration file is located at:

```
config/entity-types.yaml
```

You can customize this path using the `ENTITY_TYPES_CONFIG_PATH` environment variable:

```bash
ENTITY_TYPES_CONFIG_PATH=/path/to/custom/entity-types.yaml
```

### File Structure

```yaml
# config/entity-types.yaml
entity_types:
  - type_name: person              # Lowercase, no spaces
    description: "Individual people, including names, roles, and titles"
    examples:
      - "John Doe"
      - "Dr. Jane Smith"
      - "CEO Bob Johnson"

  - type_name: organization
    description: "Companies, institutions, agencies, and groups"
    examples:
      - "Microsoft Corporation"
      - "Stanford University"
```

### Field Requirements

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `type_name` | string | Yes | Must be lowercase, no spaces |
| `description` | string | Yes | Human-readable description |
| `examples` | array | No | List of example entities (3-5 recommended) |

### Editing the File

You can edit `config/entity-types.yaml` directly and restart the API service:

```bash
docker-compose restart api
```

Or use the API endpoint to add entity types dynamically without restart.

---

## API Endpoints

### GET /api/v1/config/entity-types

Retrieve currently configured entity types.

**Authentication:** Not required

**Response:**

```json
{
  "entity_types": [
    {
      "type_name": "person",
      "description": "Individual people",
      "examples": ["John Doe"]
    }
  ]
}
```

### POST /api/v1/config/entity-types

Add a new entity type dynamically.

**Authentication:** Required (`Authorization: Bearer <API_KEY>`)

**Request Body:**

```json
{
  "type_name": "patent",
  "description": "Patents, intellectual property, and inventions",
  "examples": ["US Patent 10,123,456", "European Patent EP1234567"]
}
```

**Success Response (201 Created):**

```json
{
  "message": "Entity type 'patent' added successfully",
  "entity_type": {
    "type_name": "patent",
    "description": "Patents, intellectual property, and inventions",
    "examples": ["US Patent 10,123,456", "European Patent EP1234567"]
  }
}
```

**Error Responses:**

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 401 | - | Missing or invalid API key |
| 409 | `ENTITY_TYPE_EXISTS` | Entity type already exists |
| 422 | `INVALID_ENTITY_TYPE` | Validation error (e.g., uppercase type_name) |
| 500 | `ENTITY_CONFIG_WRITE_FAILED` | File write permission error |

---

## Domain-Specific Examples

### Legal Domain

```yaml
entity_types:
  - type_name: statute
    description: "Laws, statutes, codes, and legal regulations"
    examples:
      - "42 U.S.C. § 1983"
      - "California Civil Code § 1798.100"
      - "GDPR Article 17"

  - type_name: case
    description: "Legal cases, court decisions, and precedents"
    examples:
      - "Brown v. Board of Education"
      - "Roe v. Wade"
      - "Marbury v. Madison"

  - type_name: party
    description: "Parties involved in legal matters"
    examples:
      - "Plaintiff"
      - "Defendant"
      - "Third-party Intervenor"

  - type_name: jurisdiction
    description: "Courts, jurisdictions, and legal authorities"
    examples:
      - "9th Circuit Court of Appeals"
      - "California Supreme Court"
      - "International Court of Justice"
```

### Medical Domain

```yaml
entity_types:
  - type_name: disease
    description: "Diseases, conditions, and medical diagnoses"
    examples:
      - "Type 2 Diabetes"
      - "Hypertension"
      - "COVID-19"
      - "Alzheimer's Disease"

  - type_name: medication
    description: "Medications, drugs, and pharmaceutical treatments"
    examples:
      - "Metformin"
      - "Lisinopril"
      - "Ibuprofen"
      - "Remdesivir"

  - type_name: procedure
    description: "Medical procedures, surgeries, and treatments"
    examples:
      - "MRI Scan"
      - "Appendectomy"
      - "Physical Therapy"
      - "Chemotherapy"

  - type_name: symptom
    description: "Symptoms, signs, and clinical presentations"
    examples:
      - "Fever"
      - "Chest Pain"
      - "Fatigue"
      - "Shortness of Breath"
```

### Technical Documentation Domain

```yaml
entity_types:
  - type_name: api_endpoint
    description: "API endpoints and routes"
    examples:
      - "POST /api/v1/documents"
      - "GET /health"
      - "DELETE /api/v1/documents/{id}"

  - type_name: function
    description: "Functions, methods, and code components"
    examples:
      - "ingest_document()"
      - "validate_metadata()"
      - "parse_pdf()"

  - type_name: error_code
    description: "Error codes and status codes"
    examples:
      - "HTTP 404"
      - "ERR_CONNECTION_TIMEOUT"
      - "ENTITY_TYPE_EXISTS"

  - type_name: configuration
    description: "Configuration parameters and environment variables"
    examples:
      - "MAX_FILE_SIZE"
      - "NEO4J_URI"
      - "API_KEY"
```

---

## Best Practices

### 1. Keep Type Names Simple

✅ **Good:** `person`, `organization`, `patent`

❌ **Bad:** `Person`, `legal case`, `US_Patent`

**Rules:**
- Lowercase only
- No spaces (use underscores if needed)
- Concise and descriptive

### 2. Provide Clear Descriptions

Descriptions help LightRAG understand what entities to extract.

✅ **Good:** "Patents, intellectual property, and inventions, including patent numbers and application IDs"

❌ **Bad:** "Patents"

### 3. Include Representative Examples

Examples guide the LLM during entity extraction.

- **Provide 3-5 examples per entity type**
- Use realistic, domain-specific examples
- Include variations (e.g., "Dr. Jane Smith", "Jane Smith, MD")

### 4. Balance Specificity and Generality

- **Too specific:** `california_statute`, `federal_statute` (better: `statute`)
- **Too general:** `thing`, `item`, `object`
- **Just right:** `statute`, `medication`, `technology`

### 5. Avoid Overlapping Entity Types

Ensure entity types are distinct to avoid confusion:

❌ **Overlapping:** `person` and `doctor` (doctor is a type of person)

✅ **Better:** Use `person` with examples like "Dr. Jane Smith"

### 6. Domain-Specific Customization

Start with default entity types and add domain-specific types as needed:

```yaml
# Keep useful general types
entity_types:
  - type_name: person
    ...
  - type_name: organization
    ...

# Add domain-specific types
  - type_name: statute
    ...
  - type_name: case
    ...
```

---

## LightRAG Integration (Epic 3)

Entity types defined in `config/entity-types.yaml` will be automatically passed to LightRAG during document ingestion in **Epic 3: Knowledge Graph Construction**.

### How It Works

1. **Document Ingestion:** User uploads document via API
2. **Entity Extraction:** LightRAG receives configured entity types
3. **LLM Processing:** LLM extracts entities based on type definitions
4. **Graph Construction:** Entities and relationships stored in Neo4j

### Integration Interface

The `LightRAGConfig` class (in `shared/models/lightrag_config.py`) provides the integration interface:

```python
from shared.models.lightrag_config import LightRAGConfig
from shared.config.entity_loader import load_cached_entity_types

# Load entity types
config = load_cached_entity_types("/app/config/entity-types.yaml")

# Create LightRAG config
lightrag_config = LightRAGConfig(
    entity_types=config.get_type_names()
)

# Generate extraction prompt for LightRAG
prompt = lightrag_config.get_entity_extraction_prompt()
```

**Note:** Full LightRAG integration will be completed in Epic 3. This story (2.5) prepares the configuration infrastructure.

---

## Troubleshooting

### Issue: POST endpoint returns 401 Unauthorized

**Solution:** Ensure you're providing the correct API key in the `Authorization` header:

```bash
curl -X POST http://localhost:8000/api/v1/config/entity-types \
  -H "Authorization: Bearer YOUR_ACTUAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

Check your `.env` file for the `API_KEY` value.

### Issue: POST endpoint returns 409 Conflict

**Solution:** The entity type already exists. Use GET endpoint to view existing types:

```bash
curl http://localhost:8000/api/v1/config/entity-types
```

### Issue: POST endpoint returns 422 Validation Error

**Solution:** Check that:
- `type_name` is lowercase
- `type_name` contains no spaces
- `description` is provided
- Request body is valid JSON

### Issue: Changes to config/entity-types.yaml not reflected

**Solution:**
- If using Docker: `docker-compose restart api`
- If using API endpoint: Changes are applied immediately (no restart needed)
- Clear cache: `get_entity_types_config.cache_clear()` (for developers)

### Issue: File permission errors (HTTP 500)

**Solution:** Ensure the API service has write permissions to `config/entity-types.yaml`:

```bash
chmod 666 config/entity-types.yaml
```

Or configure a writable volume in Docker Compose.

---

## Additional Resources

- [PRD: Functional Requirement FR4](../prd/requirements.md#fr4) - Entity type configuration requirements
- [Architecture: Components](../architecture/components.md) - Entity types configuration component design
- [API Specification](../architecture/api-specification.md) - Complete API documentation
- [LightRAG Documentation](https://github.com/HKUDS/LightRAG) - LightRAG entity extraction details

---

## Summary

- **Default entity types** cover general use cases
- **Domain-specific customization** improves extraction quality
- **API endpoints** allow dynamic configuration without restart
- **YAML file** provides persistent configuration
- **LightRAG integration** (Epic 3) will use configured entity types for graph construction

For questions or issues, see the [Troubleshooting](#troubleshooting) section or open an issue on GitHub.
