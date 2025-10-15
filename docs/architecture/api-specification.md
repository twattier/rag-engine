# API Specification

## REST API Specification

```yaml
openapi: 3.0.0
info:
  title: RAG Engine API
  version: 1.0.0
  description: |
    Production-ready RAG API with graph-based retrieval, multi-format document processing,
    and multiple integration interfaces (Open-WebUI, MCP, n8n, REST).
  contact:
    name: RAG Engine Project
    url: https://github.com/your-org/rag-engine

servers:
  - url: http://localhost:8000
    description: Local development server
  - url: http://your-domain.com/api
    description: Production server (user-deployed)

tags:
  - name: documents
    description: Document ingestion and management
  - name: queries
    description: RAG query operations
  - name: knowledge-graph
    description: Knowledge graph exploration
  - name: health
    description: System health and status

paths:
  /health:
    get:
      summary: Health check endpoint
      tags: [health]
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  services:
                    type: object
                    properties:
                      neo4j:
                        type: string
                        example: "connected"
                      lightrag:
                        type: string
                        example: "ready"
                      rag_anything:
                        type: string
                        example: "ready"

  /documents/ingest:
    post:
      summary: Ingest a new document
      tags: [documents]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
                  description: Document file to ingest
                metadata:
                  type: object
                  additionalProperties: true
                  description: Custom metadata fields (JSON)
                doc_id:
                  type: string
                  description: Optional custom document ID
                parse_method:
                  type: string
                  enum: [auto, ocr, txt]
                  default: auto
                  description: Document parsing method
      responses:
        '202':
          description: Document accepted for processing
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Document'
        '400':
          $ref: '#/components/responses/BadRequest'
        '500':
          $ref: '#/components/responses/InternalError'

  /documents/{doc_id}:
    get:
      summary: Get document status and metadata
      tags: [documents]
      parameters:
        - name: doc_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Document details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Document'
        '404':
          $ref: '#/components/responses/NotFound'

    delete:
      summary: Delete a document and related knowledge
      tags: [documents]
      parameters:
        - name: doc_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Document deleted successfully
        '404':
          $ref: '#/components/responses/NotFound'

  /query:
    post:
      summary: Perform RAG query
      tags: [queries]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - query
              properties:
                query:
                  type: string
                  description: User query text
                  example: "What are the main findings in the research papers?"
                mode:
                  type: string
                  enum: [local, global, hybrid, naive, mix]
                  default: hybrid
                  description: Retrieval mode
                top_k:
                  type: integer
                  default: 60
                  description: Number of entities/relationships to retrieve
                metadata_filters:
                  type: object
                  additionalProperties: true
                  description: Filter by document metadata
                only_context:
                  type: boolean
                  default: false
                  description: Return only context without LLM generation
                stream:
                  type: boolean
                  default: false
                  description: Enable streaming responses
      responses:
        '200':
          description: Query results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QueryResult'
        '400':
          $ref: '#/components/responses/BadRequest'
        '500':
          $ref: '#/components/responses/InternalError'

  /graph/entities:
    get:
      summary: List entities in knowledge graph
      tags: [knowledge-graph]
      parameters:
        - name: entity_type
          in: query
          schema:
            type: string
          description: Filter by entity type
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: List of entities
          content:
            application/json:
              schema:
                type: object
                properties:
                  entities:
                    type: array
                    items:
                      $ref: '#/components/schemas/Entity'
                  total:
                    type: integer
                  limit:
                    type: integer
                  offset:
                    type: integer

  /graph/relationships:
    get:
      summary: List relationships in knowledge graph
      tags: [knowledge-graph]
      parameters:
        - name: entity_name
          in: query
          schema:
            type: string
          description: Filter by entity name (source or target)
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
      responses:
        '200':
          description: List of relationships
          content:
            application/json:
              schema:
                type: object
                properties:
                  relationships:
                    type: array
                    items:
                      $ref: '#/components/schemas/Relationship'

components:
  schemas:
    Document:
      type: object
      properties:
        docId:
          type: string
        filePath:
          type: string
        contentType:
          type: string
        status:
          type: string
          enum: [pending, processing, indexed, failed]
        metadata:
          type: object
          additionalProperties: true
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time
        chunkCount:
          type: integer
        entityCount:
          type: integer
        errorMessage:
          type: string
          nullable: true

    Entity:
      type: object
      properties:
        entityName:
          type: string
        entityType:
          type: string
        description:
          type: string
        sourceIds:
          type: array
          items:
            type: string
        metadata:
          type: object
          additionalProperties: true
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    Relationship:
      type: object
      properties:
        srcEntity:
          type: string
        tgtEntity:
          type: string
        relationshipType:
          type: string
        description:
          type: string
        keywords:
          type: string
        weight:
          type: number
          format: float
        sourceIds:
          type: array
          items:
            type: string
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    TextChunk:
      type: object
      properties:
        chunkId:
          type: string
        docId:
          type: string
        content:
          type: string
        chunkIndex:
          type: integer
        tokenCount:
          type: integer
        metadata:
          type: object
          additionalProperties: true
        createdAt:
          type: string
          format: date-time

    QueryResult:
      type: object
      properties:
        queryId:
          type: string
        queryText:
          type: string
        mode:
          type: string
          enum: [local, global, hybrid, naive, mix]
        response:
          type: string
        contextChunks:
          type: array
          items:
            $ref: '#/components/schemas/TextChunk'
        entities:
          type: array
          items:
            $ref: '#/components/schemas/Entity'
        relationships:
          type: array
          items:
            $ref: '#/components/schemas/Relationship'
        metadata:
          type: object
          additionalProperties: true
        latencyMs:
          type: integer
        createdAt:
          type: string
          format: date-time

    ApiError:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object
              additionalProperties: true
            timestamp:
              type: string
              format: date-time
            requestId:
              type: string

  responses:
    BadRequest:
      description: Invalid request parameters
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiError'

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiError'

    InternalError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiError'

  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key for authentication (Phase 2)

security:
  - ApiKeyAuth: []
```

---
