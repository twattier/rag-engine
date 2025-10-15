# Project Brief: RAG Engine

## Executive Summary

RAG Engine is a general-purpose, production-ready Retrieval-Augmented Generation framework designed as an enabler for easy-to-deploy knowledge management assistants. The platform provides an ultimate, optimized RAG implementation that allows a single knowledge base to serve multiple use cases across different interfaces and deployment scenarios.

**Primary Problem:** Organizations and developers struggle with fragmented RAG implementations that are difficult to deploy, lack optimization, and cannot serve multiple use cases from a shared knowledge base. Existing solutions often compromise on either ease-of-use or performance, forcing users to choose between quick deployment and sophisticated retrieval capabilities.

**Target Market:**
- Developers building AI applications with Pydantic or n8n
- End-users deploying generic AI chatbots with MCP support
- Open-WebUI users leveraging function pipelines
- Organizations requiring versatile knowledge management solutions

**Key Value Proposition:** RAG Engine delivers ultimate RAG performance with multi-format input support, intelligent reranking, and multiple advanced retrieval strategies—all packaged for easy deployment and flexible integration. A single knowledge base can power developer-focused applications, end-user chatbots, and Open-WebUI pipelines simultaneously.

---

## Problem Statement

**Current State & Pain Points:**

The RAG landscape today forces developers and organizations into difficult compromises. While basic RAG implementations are relatively easy to deploy, they suffer from poor retrieval accuracy, lack of optimization, and inability to handle diverse document formats. Enterprise-grade solutions exist but come with complexity barriers—requiring extensive DevOps expertise, custom integration work, and often locking users into specific deployment patterns.

**Critical Pain Points:**
- **Fragmented Knowledge Bases:** Organizations maintain separate knowledge bases for different applications (chatbot, API, internal tools), creating synchronization nightmares and multiplying storage costs
- **Retrieval Quality Issues:** Naive chunking strategies and single-pass retrieval produce irrelevant results, eroding user trust in AI assistants
- **Deployment Friction:** Even sophisticated RAG frameworks require significant infrastructure setup, making iteration slow and experimentation costly
- **Integration Complexity:** Connecting RAG systems to modern development workflows (Pydantic, n8n) or user-facing tools (Open-WebUI, MCP) requires custom glue code and maintenance overhead
- **Format Limitations:** Most solutions handle only specific document types, forcing preprocessing pipelines and limiting knowledge source flexibility

**Impact & Scale:**

- **Developer Productivity Loss:** Teams spend 40-60% of RAG project time on infrastructure and integration rather than improving retrieval quality
- **User Experience Degradation:** Poor retrieval accuracy (typical 60-70% relevance) leads to user abandonment of AI assistants
- **Operational Overhead:** Managing multiple knowledge base instances increases costs and creates data consistency problems
- **Innovation Slowdown:** Deployment complexity prevents rapid experimentation with advanced retrieval strategies (reranking, hybrid search, query reformulation)

**Why Existing Solutions Fall Short:**

- **Basic RAG Libraries (LangChain, LlamaIndex):** Provide building blocks but require extensive configuration and lack production optimizations
- **Managed RAG Services:** Easy deployment but limited customization, vendor lock-in, and inability to serve multiple client patterns from one KB
- **Custom Solutions:** Optimized for specific use cases but not generalizable, expensive to maintain, and difficult to extend

**Urgency & Importance:**

The proliferation of LLM-powered applications creates immediate demand for production-ready RAG infrastructure. Organizations deploying AI assistants today face:
- **Competitive Pressure:** Companies with superior retrieval quality gain significant user satisfaction advantages
- **Cost Escalation:** Inefficient RAG implementations waste tokens on irrelevant context, multiplying LLM costs
- **Opportunity Cost:** Developers building custom RAG infrastructure aren't building differentiating features

The market window for a unified, optimized RAG solution is now—before fragmentation becomes entrenched and switching costs become prohibitive.

---

## Proposed Solution

**Core Concept & Approach:**

RAG Engine is a **production-grade deployment platform** that integrates best-in-class open-source RAG technologies into a unified, Docker-based system. Rather than reinventing RAG algorithms, we curate and optimize proven components to deliver ultimate retrieval quality with operational excellence.

**Architecture Philosophy:**

1. **Stand on Giants' Shoulders:** Integrate leading open-source RAG frameworks (LightRAG for graph-based retrieval, RAG-Anything for multi-format ingestion) rather than rebuild from scratch
2. **No Compromises on Quality:** Deploy sophisticated infrastructure (Neo4j for graph relationships, advanced reranking, hybrid retrieval) accepting operational complexity to achieve "ultimate" performance
3. **Local-First, Open-Source Only:** Everything runs in Docker containers on local infrastructure; the only external dependency is optional LiteLLM for enterprise LLM access
4. **One Knowledge Base, Multiple Interfaces:** Unified graph-backed knowledge store serves all deployment patterns without data duplication

**Technical Stack Decisions:**

**Vector & Graph Storage:**
- **Neo4j with vector support:** Enables LightRAG-style graph-based retrieval while maintaining vector similarity search
- **Trade-off:** More complex than pgvector, but required for true "ultimate" RAG quality
- **Deployment:** Fully containerized Neo4j instance with automated backup/restore

**RAG Framework Integration:**
- **LightRAG:** Graph-based retrieval for superior context preservation and relationship understanding
- **RAG-Anything:** Multi-format document processing (PDF, Word, Markdown, HTML, code, structured data)
- **Custom Integration Layer:** Unified API abstracting framework differences

**Retrieval Pipeline:**
- **Stage 1 - Hybrid Retrieval:** Combined dense embeddings + sparse (BM25) + graph traversal
- **Stage 2 - Reranking:** Open-source cross-encoder models (Jina reranker, MS Marco)
- **Stage 3 - Context Optimization:** LLM context window-aware chunk assembly

**LLM Integration:**
- **Primary:** LiteLLM proxy supporting enterprise OpenAI-compatible endpoints
- **Fallback:** Local embedding models for air-gapped deployments
- **Design:** All LLM calls abstracted through LiteLLM interface

**Key Differentiators:**

**1. Production-Ready Integration of Cutting-Edge RAG**
- LightRAG is powerful but complex to deploy and operate
- RAG-Anything handles multi-format but lacks graph capabilities
- **RAG Engine:** Combines both with operational excellence (error handling, scaling, backups)

**2. Graph-Based Retrieval for All Use Cases**
Neo4j graph relationships provide:
- **Entity-relationship awareness:** "Show me documents about X that mention Y" with true semantic understanding
- **Multi-hop reasoning:** Follow knowledge graph edges for complex queries
- **Better chunking:** Preserve document structure and relationships in graph form
- **Conversation context:** Track discussion threads as graph paths

**3. Universal Interface Layer with Zero External Dependencies**
Pre-built integrations, all running locally:
- **Open-WebUI Function Pipelines:** Native Python functions deployable directly to Open-WebUI
- **MCP Server:** Model Context Protocol server for Claude, other AI assistants
- **Pydantic SDK:** Type-safe Python client with generated models
- **n8n Nodes:** Custom nodes for workflow automation
- **REST API:** OpenAPI-documented endpoints for custom integrations

**4. Docker-Compose Simplicity Despite Sophisticated Architecture**
```yaml
# Single command deployment
docker-compose up -d

# Includes:
# - Neo4j (graph + vector)
# - LightRAG service
# - RAG-Anything service
# - RAG Engine API
# - Optional: LiteLLM proxy
```

**Why This Solution Will Succeed:**

**Where Others Haven't:**

- **vs. LightRAG Directly:** We solve the deployment/operations problem—LightRAG users struggle with production setup
- **vs. RAG-Anything Directly:** We add graph-based retrieval and comprehensive integration layer
- **vs. Managed RAG Services:** We provide 100% local deployment, no vendor lock-in, full data control
- **vs. Cloud Vector DB Solutions:** We run entirely on-premise with open-source components

**The "Deployment Wrapper" Value:**

This positioning is honest and valuable:
- **For researchers:** Access to cutting-edge RAG (LightRAG graphs) without infrastructure expertise
- **For enterprises:** Production-grade operations around open-source RAG technologies
- **For privacy-conscious users:** 100% local deployment with no external dependencies (except optional LiteLLM)
- **For Open-WebUI community:** Best-in-class RAG backend purpose-built for Open-WebUI integration

**Clear Value Path:**

- **Day 1:** `docker-compose up` → Running graph-based RAG system
- **Week 1:** Ingest documents, see graph relationships in Neo4j browser
- **Week 2:** Connect Open-WebUI function pipeline, compare vs. basic RAG
- **Month 1:** Measure retrieval quality improvement (target: 85%+ relevance vs. 60-70% baseline)
- **Month 2+:** Add n8n workflows, MCP server, or custom Pydantic integrations

**High-Level Product Vision:**

RAG Engine becomes the **default production deployment** for open-source RAG technologies—specifically:

- **"LightRAG in production"** → Deploy RAG Engine
- **"Multi-format RAG with graphs"** → Deploy RAG Engine
- **"RAG for Open-WebUI"** → Deploy RAG Engine

Success metrics:
- **Deployment simplicity:** Setup time < 30 minutes (vs. days for manual LightRAG setup)
- **Retrieval quality:** Match LightRAG paper benchmarks in production
- **Operational maturity:** 99.9% uptime, automated backups
- **Integration adoption:** Becomes reference implementation for Open-WebUI RAG backends

---

## Target Users

### Primary User Segment: Open-WebUI Self-Hosters & Power Users

**Demographic/Firmographic Profile:**
- **Individual developers** running personal AI assistants on home servers or local machines
- **Small teams (2-10 people)** in tech startups or agencies deploying shared knowledge bases
- **Privacy-conscious professionals** (lawyers, healthcare, finance) requiring on-premise AI
- **Technical sophistication:** Comfortable with Docker, command-line tools, and basic infrastructure concepts
- **Geographic:** Global, with concentration in regions with strong data sovereignty requirements (EU, healthcare/finance sectors)

**Current Behaviors & Workflows:**
- Currently run Open-WebUI with basic RAG (ChromaDB, simple vector search)
- Maintain document collections in folders, Google Drive, Notion, or local file systems
- Experience frustration with poor retrieval quality ("it can't find the right documents")
- Experiment with different LLM providers (OpenAI, local Ollama, cloud services)
- Active in Open-WebUI community (Discord, GitHub discussions)

**Specific Needs & Pain Points:**
- **Better retrieval without complexity:** Want LightRAG-quality results without becoming infrastructure experts
- **Multi-format ingestion:** Need to index PDFs, code repos, Markdown notes, web pages without manual preprocessing
- **Single source of truth:** Tired of maintaining separate knowledge bases for different tools
- **Privacy/data control:** Cannot use managed RAG services due to sensitivity of knowledge content
- **Quick experimentation:** Want to test RAG improvements rapidly without multi-day setup processes

**Goals They're Trying to Achieve:**
- Build reliable personal/team knowledge assistant that actually finds relevant information
- Index their entire technical documentation, research papers, or business documents
- Reduce time spent searching for information manually
- Deploy AI assistant that can be trusted with sensitive/proprietary information
- Learn advanced RAG techniques (graphs, reranking) through hands-on use

---

### Secondary User Segment: Workflow Automation Developers (n8n/Pydantic)

**Demographic/Firmographic Profile:**
- **API-first developers** building automation workflows or data processing pipelines
- **Integration specialists** at small-to-medium companies connecting systems
- **AI application developers** building custom LLM-powered products
- **Technical sophistication:** Strong Python/TypeScript skills, API integration experience
- **Context:** Building products or internal tools, not just personal use

**Current Behaviors & Workflows:**
- Use n8n for workflow automation, connecting multiple services
- Build Python applications with Pydantic for data validation and API clients
- Currently implement RAG using LangChain or LlamaIndex with custom code
- Struggle with production reliability and performance optimization
- Need to connect RAG to business logic (webhooks, scheduled jobs, event triggers)

**Specific Needs & Pain Points:**
- **Type-safe integrations:** Want strong typing and validation for RAG API calls
- **Workflow nodes:** Need plug-and-play n8n nodes, not custom HTTP request configurations
- **Reliability:** Current DIY RAG implementations break with edge cases or scale issues
- **Reusable infrastructure:** Don't want to rebuild RAG for every project
- **API-first design:** Need clean REST/GraphQL interfaces, not chatbot-centric designs

**Goals They're Trying to Achieve:**
- Build automated workflows that retrieve and process knowledge (e.g., "when support ticket arrives, find relevant docs and draft response")
- Create custom applications with RAG as a backend service
- Reduce time spent on RAG infrastructure so they can focus on business logic
- Deploy reliable systems that don't require constant maintenance
- Offer RAG-powered features to their own customers/users

---

## Goals & Success Metrics

### Business Objectives

- **Become default RAG deployment for Open-WebUI community** - Achieve 100+ GitHub stars and 10+ community contributions within 6 months of launch
- **Demonstrate measurable retrieval quality improvement** - Users report 85%+ retrieval relevance (vs. 60-70% baseline with ChromaDB simple vector search) in benchmark tests
- **Achieve rapid deployment time-to-value** - Average user goes from `docker-compose up` to first successful query in < 30 minutes
- **Establish integration ecosystem adoption** - 3+ integration types actively used (Open-WebUI, MCP, n8n/Pydantic) within first year
- **Validate "ultimate RAG" positioning** - Match or exceed LightRAG paper benchmark results in production environment
- **Enable graph-based knowledge understanding** - Provide built-in graph visualization managed through LightRAG Server for knowledge structure exploration and retrieval validation

### User Success Metrics

- **Retrieval accuracy improvement:** Users achieve 15-25 percentage point improvement in relevant results returned (measured via user feedback or benchmark datasets)
- **Deployment simplicity:** 90%+ of users successfully deploy and query knowledge base within first hour
- **Knowledge base scale:** Users successfully index and query 1,000 documents across multiple formats with acceptable performance (P95 < 2s)
- **Graph visualization adoption:** Users actively leverage graph visualization UI to understand knowledge structure, validate entity relationships, and debug retrieval paths
- **Multi-interface usage:** 30%+ of users connect RAG Engine to 2+ different interfaces (e.g., Open-WebUI + n8n)
- **User satisfaction:** Net Promoter Score (NPS) > 40 among active users
- **Community engagement:** Active Discord/GitHub discussions, user-contributed examples and use cases

### Key Performance Indicators (KPIs)

- **Adoption Rate:** Monthly active deployments (tracked via optional telemetry or GitHub release downloads) - Target: 500+ within 12 months
- **Query Performance:** P95 latency < 2 seconds for retrieval queries on 1k document knowledge base (MVP baseline)
- **Retrieval Quality (MRR):** Mean Reciprocal Rank > 0.80 on standard RAG benchmarks (BEIR, MS MARCO)
- **System Reliability:** 99.9% uptime for core RAG Engine API (excluding external LLM dependencies)
- **Graph Visualization Usage:** % of users accessing graph UI within first week of deployment - Target: >70%
- **Integration Usage:** % of deployments using each interface type (Open-WebUI, MCP, API, n8n) - Target: Open-WebUI >60%, API >30%, others >15%
- **Documentation Completeness:** 100% API coverage in OpenAPI spec, setup guides for each integration type
- **Community Health:** GitHub issue response time < 48 hours, monthly community calls or updates

---

## MVP Scope

### Core Features (Must Have)

- **Docker-Compose Deployment Stack:** Single-command deployment (`docker-compose up -d`) including Neo4j, LightRAG service, RAG-Anything service, RAG Engine API, and optional LiteLLM proxy. Pre-configured with sensible defaults for immediate use.

- **Multi-Format Document Ingestion with Metadata & Entity Customization:** Seamless ingestion of PDF, Markdown, HTML, Word documents, plain text, and code files (Python, JavaScript, TypeScript, Java, etc.) via RAG-Anything integration. Automatic format detection and optimized parsing strategies per format. **CRITICAL:** Support for custom metadata fields (author, department, date, tags, project, category, etc.) and user-defined expected graph entity types (person, organization, concept, product, location, technology, etc.) to guide entity extraction and improve graph quality. Configuration via ingestion API parameters, batch upload metadata files (CSV/JSON), and optional schema definition files for domain-specific entity types.

- **Graph-Based Retrieval Pipeline with Metadata Filtering:** LightRAG integration with Neo4j for graph-augmented retrieval including entity extraction, relationship mapping, and graph traversal for multi-hop reasoning. Hybrid retrieval combining dense embeddings, sparse search (BM25), and graph relationships. **CRITICAL OPTIMIZATION:** Metadata-based pre-filtering to narrow search space before retrieval—queries can specify metadata constraints (e.g., "department:engineering", "date:2024", "project:alpha") to search only relevant subset of knowledge base, dramatically improving both performance and precision. Supports complex metadata queries (AND/OR logic, date ranges, tag combinations).

- **Graph Visualization UI (LightRAG Server):** **MUST HAVE** - Built-in web interface managed through LightRAG Server for visualizing knowledge graph structure, exploring entity relationships, viewing document connections, filtering by custom metadata fields and entity types, and debugging retrieval paths. Users can interact with the graph to understand how documents are connected, see entity distributions, and validate retrieval quality.

- **Reranking Pipeline:** Integrated open-source reranking using Jina reranker or MS Marco cross-encoder models to improve relevance of top-k results. Configurable reranking strategy based on query type.

- **Open-WebUI Function Pipeline:** Native Python function implementation deployable directly to Open-WebUI for seamless integration. Includes configuration templates and setup documentation.

- **REST API with OpenAPI Spec:** Complete RESTful API for document ingestion (with metadata), query/retrieval, knowledge base management, graph exploration, and entity/metadata filtering. Auto-generated OpenAPI documentation for easy integration.

- **Basic Configuration Management:** Environment-based configuration for LLM endpoints (LiteLLM), embedding models, retrieval parameters, custom entity type schemas, and system resources. Simple .env file-based setup with optional YAML schema files for advanced entity customization.

### Out of Scope for MVP

- **Advanced monitoring and observability:** Prometheus, Grafana, or distributed tracing (can use Docker logs and Neo4j browser for MVP)
- **Multi-tenancy:** Single knowledge base per deployment (users can run multiple docker-compose instances for separate KBs)
- **Kubernetes deployment:** Docker-compose only for MVP
- **n8n custom nodes:** Pre-built n8n nodes deferred to Phase 2 (users can use REST API via HTTP request node)
- **Pydantic SDK:** Type-safe Python client deferred to Phase 2 (users can call REST API directly)
- **MCP server implementation:** MCP protocol support deferred to Phase 2
- **Advanced query analytics:** Query performance insights, user behavior tracking
- **Fine-tuned embedding models:** Use pre-trained open-source models only (no custom training)
- **Real-time collaboration features:** Multiple users editing/querying simultaneously
- **Advanced access control:** Authentication/authorization beyond basic API keys
- **Automatic document sync:** Watch folders, cloud storage integrations (manual ingestion only for MVP)
- **GUI-based metadata editor:** Metadata and entity schema defined via API/files only (no admin UI for MVP)
- **Entity disambiguation and linking:** Basic entity extraction only; advanced entity resolution deferred to Phase 2

### MVP Success Criteria

The MVP is successful when:

1. **End-to-End Workflow Complete:** User can run `docker-compose up`, ingest 100+ documents across 3+ formats with custom metadata, define expected entity types for their domain, visualize the resulting knowledge graph with metadata filters, query the knowledge base, and receive relevant results—all within 30 minutes. System demonstrates stable performance with knowledge bases up to 1,000 documents

2. **Metadata & Entity Customization Works:** Users can specify custom metadata fields during ingestion (e.g., "department: engineering"), define domain-specific entity types (e.g., "API", "Service", "Database"), and see these reflected in the graph visualization and query results

3. **Graph Visualization Functional:** Users can open the graph UI, see their documents as nodes with entity/relationship connections, filter by document type, custom metadata, or entity types, and click through to understand retrieval paths

4. **Retrieval Quality & Performance Validated:** Achieves measurable improvement over basic vector search on standard test queries (target: 15+ percentage point improvement in relevance). Metadata-based pre-filtering demonstrates both precision gains (fewer irrelevant results) and performance gains (faster retrieval on filtered subsets, e.g., 50%+ latency reduction when searching 20% of knowledge base)

5. **Open-WebUI Integration Works:** Users can deploy the Open-WebUI function pipeline and successfully query their knowledge base from Open-WebUI interface, with metadata filters available as query parameters

6. **API Documented and Functional:** Complete OpenAPI spec available, all core endpoints (ingest with metadata, query with filters, graph explore, entity schema management) working with example requests in documentation

7. **Deployment Reliability:** Docker stack starts consistently across Linux/macOS/Windows with WSL2, with clear error messages for common configuration issues

---

## Post-MVP Vision

### Phase 2 Features

**Enhanced Integration Ecosystem:**
- **n8n Custom Nodes:** Pre-built n8n nodes for document ingestion, query/retrieval, and knowledge base management—eliminating need for HTTP request node configuration
- **Pydantic SDK:** Type-safe Python client with auto-generated models from OpenAPI spec, IDE autocomplete support, and async/await patterns
- **MCP Server Implementation:** Full Model Context Protocol server enabling RAG Engine as context provider for Claude, other AI assistants, and MCP-compatible tools

**Advanced Entity & Knowledge Graph Features:**
- **Entity Disambiguation & Linking:** Resolve entity mentions to canonical entities, link to external knowledge bases (Wikidata, DBpedia)
- **Relationship Type Customization:** User-defined relationship types beyond LightRAG defaults (e.g., "implements", "depends_on", "supersedes")
- **Temporal Graph Capabilities:** Track document/entity evolution over time, query historical knowledge state, visualize changes

**Scale & Performance Enhancements:**
- **10k+ Document Support:** Optimize for knowledge bases with 10,000-100,000 documents
- **Kubernetes Deployment:** Helm charts, horizontal scaling, distributed Neo4j clusters
- **Advanced Caching:** Query result caching, embedding caching, intelligent cache invalidation
- **Batch Processing:** Efficient bulk document ingestion with progress tracking

**Automation & Sync:**
- **Document Watchers:** Monitor local folders, Google Drive, Notion, Confluence for automatic ingestion
- **Webhook Support:** Trigger ingestion or queries via external events
- **Scheduled Re-indexing:** Periodic knowledge base updates and optimization

### Long-Term Vision (12-24 months)

**The "RAG Operating System":**

RAG Engine evolves beyond a deployment wrapper into a comprehensive RAG platform where users can:

1. **Compose RAG Strategies:** Mix and match retrieval strategies (graph traversal, vector similarity, BM25, metadata filters) with declarative configuration rather than code
2. **Plugin Ecosystem:** Community-contributed plugins for specialized document types (CAD files, scientific papers, legal documents), custom embedding models, and domain-specific entity extractors
3. **Multi-Modal Knowledge Graphs:** Extend beyond text to images, audio transcriptions, video content with cross-modal retrieval
4. **Collaborative Knowledge Bases:** Multi-user editing, access control, change tracking, and knowledge base forking/merging
5. **RAG Analytics Dashboard:** Comprehensive insights into retrieval quality, query patterns, knowledge coverage gaps, and entity distribution

**Market Position Goals:**
- **100k+ deployments** across individual users, teams, and enterprises
- **Top 3 RAG framework** by GitHub stars and community size
- **Reference architecture** cited in RAG research papers and production guides
- **Active plugin marketplace** with 50+ community contributions

### Expansion Opportunities

**Vertical-Specific Packages:**
- **Legal RAG:** Pre-configured for legal documents with case law citations, statute linking
- **Medical RAG:** HIPAA-compliant deployment with medical terminology entity extraction
- **Code RAG:** Optimized for codebases with syntax-aware chunking, API documentation linking
- **Research RAG:** Academic paper ingestion with citation graphs, author networks

**Enterprise Features:**
- **Multi-Tenancy:** Isolated knowledge bases per tenant with shared infrastructure
- **Advanced RBAC:** Role-based access control, document-level permissions, audit logs
- **SSO Integration:** SAML, OAuth, LDAP authentication
- **Compliance Certifications:** SOC 2, ISO 27001 readiness

**Managed Offering (Optional):**
- **RAG Engine Cloud:** Managed deployment option for users who prefer cloud convenience while maintaining open-source core
- **Hybrid Deployment:** Cloud control plane with on-premise data plane

---

## Technical Considerations

### Platform Requirements

- **Target Platforms:** Linux (primary), macOS, Windows with WSL2
- **Container Runtime:** Docker 24.0+ and Docker Compose V2
- **Minimum Hardware:** 8GB RAM, 4 CPU cores, 50GB storage (for 1k document MVP)
- **Recommended Hardware:** 16GB RAM, 8 CPU cores, 100GB+ storage for optimal performance
- **Network:** Internet access required for LLM API calls (LiteLLM), optional for air-gapped embedding models

### Technology Preferences

**Backend:**
- **Primary Language:** Python 3.11+ (for LightRAG/RAG-Anything integration and API layer)
- **API Framework:** FastAPI (async support, automatic OpenAPI generation, production-ready)
- **Task Queue:** Optional Celery/Redis for async document ingestion (Phase 2)

**Graph & Vector Storage:**
- **Database:** Neo4j 5.x with vector index plugin
- **Justification:** Graph capabilities essential for LightRAG, native vector support eliminates need for separate vector DB
- **Backup Strategy:** Automated Neo4j dumps to local volumes

**RAG Framework Integration:**
- **LightRAG:** Python library integration for graph-based retrieval
- **RAG-Anything:** Python library for multi-format document processing
- **Custom Orchestration:** Unified API layer abstracting both frameworks

**LLM & Embedding Models:**
- **LLM Proxy:** LiteLLM for OpenAI-compatible API interface
- **Local Embeddings:** sentence-transformers (all-MiniLM-L6-v2 or similar for MVP)
- **Enterprise Embeddings:** Support for OpenAI embeddings via LiteLLM
- **Reranking:** Jina reranker or MS Marco cross-encoder models

**Frontend (Graph Visualization):**
- **LightRAG Server:** Built-in visualization capabilities
- **Fallback:** Neo4j Browser for graph exploration
- **Phase 2:** Custom React-based UI for enhanced UX

### Architecture Considerations

**Repository Structure:**
```
rag-engine/
├── docker-compose.yml          # Single-command deployment
├── services/
│   ├── api/                    # FastAPI REST API
│   ├── lightrag/               # LightRAG integration service
│   ├── rag-anything/           # Document processing service
│   └── litellm/                # Optional LLM proxy
├── shared/
│   ├── models/                 # Data models (Pydantic)
│   ├── config/                 # Configuration schemas
│   └── utils/                  # Shared utilities
├── tests/                      # Unit and integration tests
└── docs/                       # Documentation and examples
```

**Service Architecture:**
- **Microservices Pattern:** Separate containers for API, LightRAG, RAG-Anything, Neo4j, LiteLLM
- **Communication:** Internal Docker network, REST APIs between services
- **State Management:** Neo4j as single source of truth for knowledge graph
- **Configuration:** Environment variables + optional YAML config files

**Integration Requirements:**
- **Open-WebUI:** Python function pipeline (single .py file deployment)
- **REST API:** OpenAPI 3.0 spec with auto-generated documentation (Swagger/ReDoc)
- **MCP (Phase 2):** Implement MCP protocol for Claude integration
- **n8n (Phase 2):** Custom node package following n8n development standards
- **Pydantic SDK (Phase 2):** Auto-generated from OpenAPI spec using openapi-python-client

**Security/Compliance:**
- **Authentication:** API key-based authentication for MVP
- **Data Encryption:** At-rest encryption via Neo4j Enterprise (optional) or volume encryption
- **In-Transit Encryption:** TLS for external API access
- **Secrets Management:** Environment variables, optional HashiCorp Vault integration (Phase 2)
- **Compliance:** Design for GDPR data portability (export functionality), HIPAA considerations documented

**Scalability Considerations (Phase 2):**
- **Horizontal Scaling:** Kubernetes deployment with multiple API replicas
- **Database Scaling:** Neo4j clustering for read replicas and high availability
- **Caching Layer:** Redis for query result caching
- **Load Balancing:** Nginx or cloud load balancer for distributed requests

---

## Constraints & Assumptions

### Constraints

**Budget:**
- **Development:** Solo developer or small team (<3 people) assumed
- **Infrastructure Costs:** Zero external service costs required (all open-source, local deployment)
- **Optional Costs:** LLM API usage (user-provided), domain-specific fine-tuned models (future consideration)
- **Implication:** MVP must be achievable without significant capital investment; community contributions welcome but not required

**Timeline:**
- **MVP Target:** 3-6 months from project start to deployable MVP
- **Phase 2:** Additional 6-12 months for enhanced integrations and scale
- **Market Window:** RAG space evolving rapidly; MVP needed within 6 months to remain competitive
- **Implication:** Prioritize integration over innovation; leverage existing frameworks (LightRAG, RAG-Anything) rather than building from scratch

**Resources:**
- **Team Size:** 1-2 core developers assumed for MVP
- **Expertise Required:** Python, FastAPI, Docker, Neo4j, RAG fundamentals, LLM integration
- **Community Dependency:** Success relies on LightRAG and RAG-Anything continued development and stability
- **Documentation:** Comprehensive docs critical due to small team size—users must be self-sufficient
- **Implication:** Simple, well-documented architecture prioritized over sophisticated but complex solutions

**Technical:**
- **Docker Compose Limitation:** No built-in orchestration for multi-host deployment (requires Kubernetes for Phase 2)
- **Neo4j Community Edition:** Feature limitations vs. Enterprise (no clustering, limited backup options)
- **Python Performance:** Not suitable for extreme low-latency requirements (<100ms), acceptable for RAG use case
- **LightRAG/RAG-Anything Coupling:** Tight dependency on upstream library quality and breaking changes
- **1k Document Scale:** MVP optimized for 1k documents; 10k+ requires Phase 2 optimizations
- **Single Tenant:** No isolation between users/projects in MVP; requires multiple deployments for separation

### Key Assumptions

**Market & User Assumptions:**
- Open-WebUI community is large enough (1000+ potential users) to sustain adoption
- Users experiencing RAG quality pain, not just deployment pain
- Self-hosters comfortable with Docker are willing to adopt more sophisticated RAG infrastructure
- Privacy-conscious users value local deployment enough to accept operational complexity
- Developers will tolerate REST API integration (n8n HTTP nodes) until custom nodes available

**Technical Assumptions:**
- LightRAG paper benchmarks are reproducible in production environments
- Neo4j vector indexes perform adequately for 1k document scale without extensive tuning
- LightRAG visualization server provides sufficient graph UI capabilities for MVP
- FastAPI async performance meets <2s P95 latency target without optimization
- Docker Compose resource limits acceptable on typical developer hardware (16GB RAM)
- sentence-transformers embedding quality sufficient for MVP (no fine-tuning needed)

**Dependency Assumptions:**
- LightRAG maintains active development, no major breaking changes during MVP timeline
- RAG-Anything continues supporting new document formats
- Neo4j vector plugin remains in Community Edition (doesn't move to Enterprise-only)
- LiteLLM maintains OpenAI compatibility layer without regressions
- Open-WebUI function pipeline API remains stable

**Integration Assumptions:**
- Open-WebUI users can deploy Python function files without significant friction
- REST API with OpenAPI spec is sufficient for most integration needs
- MCP protocol stabilizes sufficiently for Phase 2 implementation
- n8n community node development process is straightforward

**Adoption & Growth Assumptions:**
- MVP quality sufficient to generate word-of-mouth in Open-WebUI community
- GitHub stars correlate with actual usage/deployments
- Community will contribute issues, feedback, and eventually PRs
- Documentation and examples lower barrier to adoption sufficiently
- "Deployment wrapper" positioning resonates rather than being perceived as "not innovative enough"

**Competitive Assumptions:**
- LightRAG/RAG-Anything won't significantly improve their own deployment stories before MVP launch
- Managed RAG services won't aggressively target self-hoster segment with local deployment options
- Graph-based RAG complexity remains barrier for DIY implementations
- No dominant "RAG Engine" equivalent emerges before MVP launch

---

## Risks & Open Questions

### Key Risks

- **Upstream Dependency Risk:** LightRAG or RAG-Anything could introduce breaking changes, abandon maintenance, or pivot direction. If LightRAG stops development, our "ultimate RAG" positioning collapses.
  - *Mitigation:* Fork critical dependencies if needed; maintain abstraction layer for potential framework swaps; monitor upstream activity closely

- **Benchmark Reproducibility Risk:** LightRAG paper benchmarks may not translate to production environments with real-world documents. If retrieval quality doesn't meaningfully exceed basic vector search, value proposition weakens.
  - *Mitigation:* Early prototype validation with benchmark datasets; gather real-world quality feedback from MVP users; be transparent about performance vs. claims

- **Neo4j Complexity Barrier:** Users may struggle with Neo4j operational requirements (memory tuning, backup, troubleshooting) despite Docker packaging. If >30% of users fail deployment, "easy deployment" claim fails.
  - *Mitigation:* Comprehensive troubleshooting documentation; pre-configured defaults; active community support; fallback to simplified architecture if needed

- **Open-WebUI Market Size Risk:** Open-WebUI community may be smaller than assumed, or users may be satisfied with existing ChromaDB integration. If addressable market <500 potential users, growth stalls.
  - *Mitigation:* Validate community size via Discord/GitHub metrics before committing; expand to adjacent communities (Ollama users, self-hosted AI enthusiasts); pivot to different primary segment if needed

- **Performance at Scale Risk:** 1k document target may hit performance walls sooner than expected due to Neo4j query complexity or graph traversal overhead. P95 latency >5s would degrade user experience significantly.
  - *Mitigation:* Early load testing with realistic datasets; optimization sprint if needed; metadata filtering to reduce search space; caching strategies

- **Metadata Complexity Risk:** Custom metadata and entity schema configuration may prove too complex for users, reducing adoption. If <50% of users leverage metadata features, key differentiator underutilized.
  - *Mitigation:* Provide domain-specific templates (code, legal, medical); excellent examples and tutorials; optional wizard for schema generation

- **Competitive Timing Risk:** Competing solution emerges before MVP launch, capturing Open-WebUI mindshare. LightRAG/RAG-Anything could release official deployment solutions.
  - *Mitigation:* Rapid MVP delivery (target 3 months minimum); community engagement early; focus on superior integration/UX as differentiator

- **Integration Maintenance Burden:** Open-WebUI, MCP, n8n APIs could change, requiring ongoing maintenance effort beyond small team capacity.
  - *Mitigation:* Versioned integrations; community contributions for integration maintenance; prioritize stable APIs first

### Open Questions

**Technical Questions:**
1. **LightRAG Visualization:** Does LightRAG Server provide production-ready graph visualization UI, or do we need to build custom UI from day one?
2. **Neo4j Licensing:** Are there Community Edition limitations that would force Enterprise upgrade for MVP use cases?
3. **RAG-Anything Integration:** How much custom code is required to integrate RAG-Anything, or does it provide clean APIs?
4. **Embedding Model Choice:** Is all-MiniLM-L6-v2 sufficient quality, or should we default to larger models (with performance trade-off)?
5. **Reranking Performance:** What's the latency impact of reranking on 1k document corpus? Is it acceptable for <2s P95 target?
6. **Metadata Indexing:** Does Neo4j efficiently index custom metadata fields, or do we need specialized index strategies?

**Market & Positioning Questions:**
1. **Open-WebUI Adoption:** What's the actual size and growth rate of Open-WebUI community?
2. **Deployment Wrapper Perception:** Will users see "deployment wrapper" as valuable or dismiss it as "not innovative"?
3. **Pricing Strategy:** Should we plan for commercial support/enterprise offerings, or stay pure open-source?
4. **Primary Segment:** Should we validate Open-WebUI as primary segment, or hedge with multi-segment MVP?

**Product & Feature Questions:**
1. **MCP Priority:** Should MCP server be elevated to MVP given its potential importance and lower complexity?
2. **Multi-Format Priority:** Which document formats are most critical for MVP (PDF + Markdown + ?, or broader coverage)?
3. **Query Interface:** Do users need advanced query DSL, or is natural language + metadata filters sufficient?
4. **Graph Complexity:** Should users be able to customize graph schema (node types, edge types), or is LightRAG default sufficient?

**Go-to-Market Questions:**
1. **Launch Strategy:** Release on GitHub + Open-WebUI Discord announcement sufficient, or broader outreach needed?
2. **Documentation Scope:** How much documentation is "enough" for self-sufficient users?
3. **Community Building:** Discord server vs. GitHub Discussions vs. both for community engagement?
4. **Success Metrics:** How do we actually measure retrieval quality improvement in production (user surveys, benchmark dataset)?

### Areas Needing Further Research

**Technical Research:**
- Benchmark LightRAG with 1k documents on typical hardware (8-core, 16GB RAM) to validate latency targets
- Test Neo4j Community Edition memory requirements and query performance at MVP scale
- Prototype RAG-Anything integration to estimate development effort and identify gotchas
- Evaluate LightRAG Server UI capabilities to determine if custom UI needed for MVP
- Research metadata indexing strategies in Neo4j for optimal filter performance

**Market Research:**
- Survey Open-WebUI Discord community for RAG pain points and feature priorities
- Analyze competitor positioning (how do they describe themselves—framework, platform, service?)
- Identify adjacent communities (Ollama, LocalAI, self-hosted AI) as potential secondary segments
- Research vertical-specific RAG needs (legal, medical, code) to validate expansion opportunities

**User Research:**
- Interview 5-10 Open-WebUI power users about current RAG setup and frustrations
- Validate "deployment wrapper" positioning with target users (value perception)
- Test metadata/entity customization UX with potential users (complexity assessment)
- Understand integration preferences (n8n vs. Pydantic vs. MCP priority)

---

## Next Steps

### Immediate Actions

1. **Validate LightRAG Integration Feasibility** - Prototype LightRAG + Neo4j integration with sample 100-document dataset to validate benchmark reproducibility and identify integration challenges (Week 1-2, 16 hours)

2. **Assess Open-WebUI Community Size** - Survey Open-WebUI Discord/GitHub to validate market size, identify power users for interviews, and gauge RAG pain points (Week 1, 8 hours)

3. **Evaluate LightRAG Server Visualization** - Deploy LightRAG Server demo to assess graph UI capabilities and determine if custom UI needed for MVP (Week 1, 4 hours)

4. **Define MVP Repository Structure** - Set up GitHub repository with services/, shared/, docs/ structure and docker-compose.yml skeleton (Week 2, 8 hours)

5. **Create Technical Architecture Document** - Detail service communication patterns, API contracts, data models, and deployment architecture (Week 2-3, 16 hours)

6. **Conduct User Interviews** - Interview 5-10 Open-WebUI power users to validate assumptions and prioritize features (Week 3-4, 20 hours)

7. **Build Minimal LightRAG Prototype** - End-to-end prototype: ingest 10 documents, query via REST API, visualize graph (Week 4-5, 40 hours)

8. **Validate Metadata Filtering Performance** - Test Neo4j metadata indexing strategies with 1k documents to ensure <2s P95 latency (Week 5, 8 hours)

9. **Draft API Specification** - Create OpenAPI 3.0 spec for core endpoints (ingest, query, graph explore, metadata management) (Week 6, 16 hours)

10. **Establish Community Presence** - Create GitHub repository with README, setup Discord/GitHub Discussions, announce in Open-WebUI community (Week 6, 8 hours)

### PM Handoff

**Context for Product Manager:**

This Project Brief provides comprehensive context for the RAG Engine project—a production-grade deployment platform integrating LightRAG and RAG-Anything for ultimate graph-based retrieval with easy Docker deployment.

**Key Strategic Decisions Made:**
- **Positioning:** "Deployment wrapper" for open-source RAG frameworks, not building novel algorithms
- **Quality over Simplicity:** Neo4j + graph-based retrieval despite operational complexity
- **Primary Segment:** Open-WebUI self-hosters and power users
- **MVP Scale:** 1,000 documents, 3-6 month timeline, solo/small team
- **Must-Have Features:** Graph visualization, metadata/entity customization, multi-format ingestion

**Critical Assumptions to Validate:**
1. LightRAG benchmarks are reproducible in production environments
2. Open-WebUI community size supports 500+ deployments within 12 months
3. Metadata filtering provides significant performance + precision gains
4. "Deployment wrapper" positioning resonates (not seen as "not innovative")

**High-Priority Open Questions:**
1. Does LightRAG Server provide adequate graph visualization UI for MVP?
2. Should MCP server be elevated to MVP (vs. Phase 2)?
3. Which document formats are most critical (PDF + Markdown + ?)?
4. What's the optimal launch strategy (GitHub + Discord vs. broader outreach)?

**Next Phase: PRD Generation**

Please start in **PRD Generation Mode** and work with me to create the Product Requirements Document section by section. The PRD should translate this strategic brief into detailed functional specifications, user stories, and acceptance criteria.

**Areas requiring PRD detail:**
- User stories for each core feature (ingestion, retrieval, graph visualization, metadata management)
- API endpoint specifications with request/response schemas
- Graph visualization UI requirements and user workflows
- Metadata/entity schema definition formats and examples
- Open-WebUI function pipeline integration specifications
- Deployment and configuration documentation requirements
- Testing strategy and success criteria per feature

**Questions for PRD Development:**
- Should we prioritize features beyond MVP scope definition (e.g., specific metadata templates)?
- How detailed should API specs be in PRD vs. separate OpenAPI document?
- Should we include wireframes for graph visualization UI, or defer to design phase?
- What level of technical detail is appropriate for handoff to development team?

Please review this brief thoroughly, ask clarifying questions, and let's begin PRD development when ready.

---

