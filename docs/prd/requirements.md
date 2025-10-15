# Requirements

## Functional Requirements

**FR1:** The system shall support single-command Docker Compose deployment that initializes all required services (Neo4j, LightRAG, RAG-Anything, RAG Engine API, and optional LiteLLM proxy) with pre-configured default settings

**FR2:** The system shall ingest documents in multiple formats including PDF, Markdown, HTML, Microsoft Word (.doc/.docx), code files (Python, JavaScript, TypeScript, Java), and plain text through RAG-Anything integration

**FR3:** The system shall accept custom metadata fields during document ingestion (e.g., author, department, date, tags, project, category) configurable via API parameters or batch upload files (CSV/JSON)

**FR4:** The system shall accept user-defined expected entity types (e.g., person, organization, concept, product, location, technology) to guide LightRAG's entity extraction process via configuration files or API parameters

**FR5:** The system shall implement graph-based retrieval pipeline combining dense embeddings, sparse search (BM25), and graph traversal for multi-hop reasoning using LightRAG's hybrid retrieval modes

**FR6:** The system shall support metadata-based pre-filtering of search space before retrieval, allowing queries to specify metadata constraints (e.g., `department:engineering`, `date:2024`, `project:alpha`) with AND/OR logic, date ranges, and tag combinations

**FR7:** The system shall provide graph visualization UI through LightRAG Server for exploring knowledge graph structure, viewing entity relationships, visualizing document connections, and debugging retrieval paths

**FR8:** The system shall allow filtering graph visualization by custom metadata fields and entity types defined during ingestion

**FR9:** The system shall integrate open-source reranking using Jina AI reranker or MS Marco cross-encoder models to improve relevance of top-k retrieval results with configurable reranking strategies

**FR10:** The system shall provide an Open-WebUI Function Pipeline as a native Python function deployable directly to Open-WebUI, including configuration templates and setup documentation

**FR11:** The system shall expose a RESTful API with endpoints for document ingestion (with metadata), query/retrieval, knowledge base management, graph exploration, and entity/metadata filtering, documented via auto-generated OpenAPI 3.0 specification

**FR12:** The system shall support environment-based configuration for LLM endpoints (via LiteLLM), embedding models, retrieval parameters, custom entity type schemas, and system resources using `.env` files with optional YAML schema files for advanced customization

**FR13:** The system shall persist all knowledge graph data (entities, relationships, embeddings) to Neo4j with vector support for both graph traversal and vector similarity search

**FR14:** The system shall track document ingestion status and support incremental updates to the knowledge base without re-processing unchanged documents

**FR15:** The system shall extract entities and relationships from ingested documents automatically using LightRAG's entity extraction with LLM-powered natural language understanding

## Non-Functional Requirements

**NFR1:** The system shall achieve P95 query latency of less than 2 seconds for retrieval queries on a knowledge base containing 1,000 documents when running on the recommended hardware (16GB RAM, 8 CPU cores)

**NFR2:** The system shall demonstrate 85%+ retrieval relevance (measured via Mean Reciprocal Rank > 0.80 on BEIR benchmark dataset subset) compared to 60-70% baseline with ChromaDB simple vector search. Validation performed in Epic 5 Story 5.5 using BEIR SciFact dataset (1.1k scientific claims, 5k evidence documents) for domain-agnostic testing.

**Measurement Methodology:**
- **Baseline**: ChromaDB with naive vector search (no graph, no reranking) - expected MRR ~0.65-0.70
- **RAG Engine**: LightRAG hybrid retrieval with reranking - target MRR > 0.80
- **Dataset**: BEIR SciFact (scientific claim verification)
- **Metric**: Mean Reciprocal Rank (MRR) - measures how highly the first relevant document ranks
- **Success**: RAG Engine MRR ≥ baseline MRR × 1.15 (15+ percentage point improvement)

**NFR3:** The system shall complete the end-to-end deployment workflow (docker-compose up, ingest 100+ documents, define entity types, visualize graph, query knowledge base) within 30 minutes for new users

**NFR4:** The system shall achieve 99.9% uptime for the RAG Engine API service excluding external LLM dependencies

**NFR5:** The system shall run entirely on local infrastructure with zero external service dependencies except for optional LiteLLM for enterprise LLM access

**NFR6:** The system shall support knowledge bases up to 1,000 documents with acceptable performance (P95 < 2s) on MVP-recommended hardware as the baseline target

**NFR7:** The system shall provide clear error messages and troubleshooting guidance for common configuration issues across Linux, macOS, and Windows with WSL2 platforms

**NFR8:** The system shall implement automated Neo4j backup and restore functionality for knowledge base persistence

**NFR9:** The system shall demonstrate metadata-based filtering performance gains of 50%+ latency reduction when searching a filtered subset (e.g., 20% of knowledge base) compared to unfiltered search

**NFR10:** The system shall maintain API backward compatibility within major version releases to avoid breaking existing integrations

---
