# Tech Stack

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| **Backend Language** | Python | 3.11+ | Core application runtime | Required by LightRAG and RAG-Anything; async/await support; rich ecosystem for ML/AI |
| **Backend Framework** | FastAPI | 0.115+ | REST API server | Async support, automatic OpenAPI generation, high performance, Pydantic integration |
| **RAG Framework** | LightRAG | Latest (0.x) | Graph-based retrieval engine | Graph-augmented retrieval, entity extraction, multi-hop reasoning |
| **Document Processor** | RAG-Anything | Latest (0.x) | Multi-format document parsing | Handles PDF, Office, images, tables, equations via MinerU integration |
| **Graph + Vector DB** | Neo4j | 5.x (Community) | Knowledge graph and vector storage | Native graph + vector support, production-proven, LightRAG requirement |
| **LLM Proxy** | LiteLLM | Latest | Unified LLM interface | OpenAI-compatible API for 100+ LLM providers, cost tracking, fallback logic |
| **Web Server** | Uvicorn | Latest | ASGI server for FastAPI | High-performance async server, production-ready |
| **Embedding Models** | sentence-transformers | Latest | Local embeddings (MVP) | Open-source, good quality, no API costs for MVP |
| **Alternative Embeddings** | OpenAI text-embedding-3 | Latest | Enterprise embeddings (optional) | Higher quality, requires API key, accessed via LiteLLM |
| **Reranking** | Jina reranker / MS Marco | Latest | Result reranking | Improves retrieval precision, optional performance boost |
| **Document Parser** | MinerU | 2.0+ | PDF/Office/image parsing | High-fidelity extraction, OCR support, GPU acceleration |
| **API Documentation** | Swagger UI / ReDoc | Latest (auto-generated) | Interactive API docs | Built-in FastAPI feature, no additional setup |
| **Validation** | Pydantic | 2.x | Data validation and serialization | Type safety, automatic validation, OpenAPI schema generation |
| **Testing Framework** | pytest | Latest | Unit and integration tests | Python standard, async support, fixture-based, plugin ecosystem |
| **Test Coverage** | pytest-cov | Latest | Code coverage reporting | Ensures test completeness |
| **Async Testing** | pytest-asyncio | Latest | Async test support | Required for FastAPI async route testing |
| **HTTP Testing** | httpx | Latest | API integration tests | Async HTTP client, TestClient support for FastAPI |
| **Container Runtime** | Docker | 24.0+ | Service containerization | Industry standard, cross-platform, easy distribution |
| **Container Orchestration** | Docker Compose | V2 | Multi-container orchestration | Single-command deployment, environment management |
| **Configuration Management** | python-dotenv | Latest | Environment variable loading | .env file support for configuration |
| **Logging** | structlog | Latest | Structured logging | JSON logs, context preservation, easy parsing for monitoring |
| **Monitoring** | Prometheus + Grafana | Latest (Phase 2) | Metrics and dashboards | Industry standard, Neo4j metrics integration |
| **CI/CD** | GitHub Actions | N/A | Automated testing and Docker builds | Free for public repos, Docker registry integration |
| **Documentation** | MkDocs | Latest | Project documentation | Markdown-based, auto-generated from code, GitHub Pages deployment |

**NOTE ON NETWORK PORTS**: All services communicate internally via Docker network. Port bindings are configurable via `.env` file:
- Neo4j: Default 7687 (Bolt), 7474 (HTTP) - **USER CONFIGURABLE**
- FastAPI: Default 8000 - **USER CONFIGURABLE**
- LightRAG Server (optional): Default 9621 - **USER CONFIGURABLE**
- LiteLLM: Default 4000 - **USER CONFIGURABLE**

Documentation must emphasize these are EXAMPLE ports and can be changed in `.env` to avoid conflicts.

---
