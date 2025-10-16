# Metadata Configuration

This guide explains how to define custom metadata fields for document organization and filtering in the RAG Engine.

## Overview

The RAG Engine supports custom metadata schemas that allow you to define domain-specific attributes for your documents. This enables you to:

- Filter documents by custom attributes (e.g., department, project, author)
- Organize documents with tags and categories
- Track document versions and creation dates
- Control document visibility and access

## Metadata Schema File

The metadata schema is defined in a YAML configuration file located at `config/metadata-schema.yaml`. This file specifies the fields that can be attached to documents during ingestion.

### Configuration Location

The schema file path is configurable via the `METADATA_SCHEMA_PATH` environment variable:

```bash
# Default path (Docker container)
METADATA_SCHEMA_PATH=/app/config/metadata-schema.yaml
```

## Supported Field Types

The schema supports five field types:

| Type | Description | Example Values |
|------|-------------|----------------|
| `string` | Text values | `"John Doe"`, `"Engineering"` |
| `integer` | Whole numbers | `1`, `42`, `2024` |
| `date` | ISO 8601 dates (YYYY-MM-DD) | `"2024-10-16"` |
| `boolean` | True/false values | `true`, `false` |
| `tags` | List of strings | `["important", "reviewed"]` |

## Schema Structure

Each field definition in the schema includes:

- **field_name**: Unique identifier for the field
- **type**: Data type (string, integer, date, boolean, tags)
- **required**: Whether the field must be provided (true/false)
- **default**: Default value if not provided (optional)
- **description**: Human-readable explanation of the field

### Example Schema

```yaml
metadata_fields:
  - field_name: author
    type: string
    required: false
    default: "Unknown"
    description: "Document author name"

  - field_name: department
    type: string
    required: false
    description: "Department or organizational unit"

  - field_name: date_created
    type: date
    required: false
    description: "Document creation date (ISO 8601 format: YYYY-MM-DD)"

  - field_name: tags
    type: tags
    required: false
    default: []
    description: "List of tags for categorization"

  - field_name: version
    type: integer
    required: false
    default: 1
    description: "Document version number"

  - field_name: is_public
    type: boolean
    required: false
    default: false
    description: "Whether document is publicly accessible"
```

## Domain-Specific Examples

### Legal Documents

```yaml
metadata_fields:
  - field_name: case_number
    type: string
    required: true
    description: "Legal case identifier"

  - field_name: practice_area
    type: string
    required: true
    description: "Practice area (e.g., corporate, litigation, IP)"

  - field_name: filing_date
    type: date
    required: false
    description: "Date document was filed"

  - field_name: confidentiality_level
    type: string
    required: false
    default: "internal"
    description: "Confidentiality level (public, internal, confidential)"

  - field_name: tags
    type: tags
    required: false
    default: []
    description: "Document tags (e.g., contract, motion, brief)"
```

### Medical Documents

```yaml
metadata_fields:
  - field_name: patient_id
    type: string
    required: true
    description: "Patient identifier (anonymized)"

  - field_name: document_type
    type: string
    required: true
    description: "Type of medical document (lab_report, imaging, consultation)"

  - field_name: date_of_service
    type: date
    required: true
    description: "Date of medical service"

  - field_name: provider
    type: string
    required: false
    description: "Healthcare provider name"

  - field_name: is_sensitive
    type: boolean
    required: false
    default: true
    description: "Whether document contains sensitive information"
```

### Technical Documentation

```yaml
metadata_fields:
  - field_name: project_name
    type: string
    required: true
    description: "Project identifier"

  - field_name: document_type
    type: string
    required: true
    description: "Type (spec, design, api_doc, readme)"

  - field_name: version
    type: integer
    required: false
    default: 1
    description: "Document version number"

  - field_name: authors
    type: tags
    required: false
    default: []
    description: "List of document authors"

  - field_name: last_updated
    type: date
    required: false
    description: "Last update date"

  - field_name: is_deprecated
    type: boolean
    required: false
    default: false
    description: "Whether document is deprecated"
```

## Using Metadata in API Requests

When ingesting documents via the API, provide metadata as a JSON object:

### Example: Document Ingestion with Metadata

```bash
curl -X POST http://localhost:8000/api/v1/documents/ingest \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.pdf",
    "metadata": {
      "author": "Jane Smith",
      "department": "Engineering",
      "date_created": "2024-10-16",
      "tags": ["specification", "reviewed"],
      "version": 2,
      "is_public": false
    }
  }'
```

### Example: Minimal Metadata (Defaults Applied)

```bash
curl -X POST http://localhost:8000/api/v1/documents/ingest \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.pdf",
    "metadata": {
      "author": "John Doe"
    }
  }'
```

In this case, the API will automatically apply default values:
- `version` → `1`
- `tags` → `[]`
- `is_public` → `false`

## Validation Rules

### Required Fields

If a field is marked as `required: true`, documents must provide a value for that field during ingestion. Missing required fields result in a `422 Unprocessable Entity` error.

### Type Validation

The API validates that field values match their declared types:

- **String fields** must be text values
- **Integer fields** must be whole numbers (not floats or strings)
- **Date fields** must be ISO 8601 format (`YYYY-MM-DD`)
- **Boolean fields** must be `true` or `false`
- **Tags fields** must be arrays of strings

### Extra Fields

The schema is **permissive** by default. You can include additional metadata fields not defined in the schema, and they will be stored alongside the defined fields.

## Error Handling

### Missing Required Field

```json
{
  "error": {
    "code": "INVALID_METADATA",
    "message": "Metadata validation failed",
    "validation_errors": "Required field 'author' is missing"
  }
}
```

**HTTP Status**: `422 Unprocessable Entity`

### Wrong Field Type

```json
{
  "error": {
    "code": "INVALID_METADATA",
    "message": "Metadata validation failed",
    "validation_errors": "Field 'version' must be integer, got str"
  }
}
```

**HTTP Status**: `422 Unprocessable Entity`

### Invalid Date Format

```json
{
  "error": {
    "code": "INVALID_METADATA",
    "message": "Metadata validation failed",
    "validation_errors": "Field 'date_created' must be valid ISO 8601 date string, got '01/15/2024'"
  }
}
```

**HTTP Status**: `422 Unprocessable Entity`

### Multiple Errors

When multiple validation errors occur, they are combined:

```json
{
  "error": {
    "code": "INVALID_METADATA",
    "message": "Metadata validation failed",
    "validation_errors": "Required field 'author' is missing; Field 'version' must be integer, got str"
  }
}
```

## Troubleshooting

### Schema File Not Found

**Error**: `SCHEMA_NOT_FOUND`

**Solution**:
1. Verify the `METADATA_SCHEMA_PATH` environment variable points to the correct file
2. Ensure the schema file exists at the specified path
3. Check file permissions (readable by the API service)

### Invalid YAML Syntax

**Error**: `INVALID_SCHEMA: Invalid YAML in schema file`

**Solution**:
1. Validate YAML syntax using a linter or online validator
2. Check for proper indentation (use spaces, not tabs)
3. Ensure all strings with special characters are quoted

### Schema Validation Error

**Error**: `INVALID_SCHEMA: Invalid schema structure`

**Solution**:
1. Verify all required fields are present (`field_name`, `type`, `description`)
2. Check that field types are valid (`string`, `integer`, `date`, `boolean`, `tags`)
3. Ensure `required` is a boolean (`true` or `false`)
4. Verify default values match their field type

### Cache Issues

The metadata schema is cached for performance. If you update the schema file, restart the API service to reload:

```bash
docker-compose restart api
```

## Best Practices

### 1. Keep Schemas Simple

Start with essential fields and expand as needed. Too many fields can make ingestion complex.

### 2. Use Descriptive Field Names

Choose clear, self-documenting field names:
- ✅ Good: `date_created`, `author_name`, `project_id`
- ❌ Bad: `dc`, `auth`, `pid`

### 3. Provide Sensible Defaults

Set default values for optional fields to simplify ingestion:

```yaml
- field_name: version
  type: integer
  required: false
  default: 1
  description: "Document version"
```

### 4. Use Tags for Flexible Categorization

Tags provide flexible categorization without requiring schema changes:

```yaml
- field_name: tags
  type: tags
  required: false
  default: []
  description: "Document tags"
```

### 5. Document Your Schema

Include clear descriptions for each field to help API users understand the schema.

### 6. Validate Before Deployment

Test schema changes in a development environment before deploying to production.

## Schema Migration

When updating an existing schema:

1. **Add new fields** with `required: false` to avoid breaking existing ingestion workflows
2. **Set sensible defaults** for new fields
3. **Test validation** with existing and new documents
4. **Update documentation** to reflect schema changes
5. **Restart API service** to load the new schema

### Example: Adding a New Field

```yaml
# Before
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Author"

# After (safe addition)
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Author"

  - field_name: review_status
    type: string
    required: false        # Not required - won't break existing workflows
    default: "pending"     # Sensible default
    description: "Document review status (pending, approved, rejected)"
```

## Related Documentation

- [API Documentation](api-reference.md) - Full API reference including document ingestion endpoints
- [Architecture Guide](architecture/components.md) - System architecture and component overview
- [Configuration Guide](configuration.md) - Complete environment variable reference
