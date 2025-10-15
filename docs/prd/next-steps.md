# Next Steps

## UX Expert Prompt

**Prompt for UX Expert:**

> Review the RAG Engine PRD (docs/prd.md) and Project Brief (docs/brief.md). Note that RAG Engine uses service-native UIs (LightRAG Server, Neo4j Browser) rather than custom UI development. Your focus should be on:
>
> 1. Evaluating the usability of exposing existing service UIs vs. building custom interfaces
> 2. Reviewing the User Journey Documentation section and identifying gaps or friction points
> 3. Creating user flow diagrams for the 5 primary user journeys documented in the PRD
> 4. Identifying UX gaps or friction points in the API-first + service-native UI approach
> 5. Recommending documentation improvements to compensate for lack of unified custom UI
>
> Begin UX analysis when ready.

## Architect Prompt

**Prompt for Architect:**

> Review the RAG Engine PRD (docs/prd.md), Project Brief (docs/brief.md), and source documentation for LightRAG and RAG-Anything (docs/sources/). Create the technical architecture document covering:
>
> 1. **Service Architecture**: Detailed service communication patterns, data flow diagrams, API contracts between RAG Engine API ↔ LightRAG Integration ↔ RAG-Anything Integration
> 2. **Neo4j Schema Design**: Complete graph schema with nodes (Document, Entity, Metadata), relationships, properties, indexes, constraints; support for both graph traversal and metadata filtering
> 3. **Docker Compose Service Definitions**: Container specifications, networking (internal Docker network), volumes (Neo4j persistence), environment variables, port exposure strategy
> 4. **Integration Patterns**: RAG-Anything parsed output → LightRAG graph input data contracts, API orchestration layer design, error propagation patterns
> 5. **Configuration Management**: .env file structure (all variables documented), YAML schema formats for metadata-schema.yaml and entity-types.yaml with validation rules
> 6. **Security Architecture**: API key authentication implementation, secret management approach, TLS termination strategies for production reverse proxy
> 7. **Monitoring and Observability**: Structured logging format (structlog JSON schema), metrics collection points, health check implementation details, integration with Prometheus (optional)
> 8. **Testing Infrastructure**: Docker Compose test environment setup (docker-compose.test.yml), test database lifecycle management, mock LLM endpoint configuration
>
> **Critical Questions to Address:**
> - Can LightRAG Server run as separate Docker service, or must it be embedded in lightrag-integration service?
> - Does RAG-Anything provide service/API mode, or must we wrap its Python library?
> - What are Neo4j memory configuration requirements for 1k document scale? (Recommend heap size, page cache)
>
> **Consider Story 0.1 Technical Spike:** Before finalizing architecture, recommend prototyping LightRAG Server + RAG-Anything deployment approaches to validate assumptions.
>
> Begin architecture design in create-architecture mode using this PRD as input.

---

**PRD Complete - Version 1.0**
