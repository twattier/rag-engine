# Unified Project Structure

```plaintext
rag-engine/
├── .github/                        # CI/CD workflows
│   └── workflows/
│       ├── ci.yaml                 # Lint, test, build on PR
│       ├── docker-build.yaml       # Build and push Docker images
│       └── docs-deploy.yaml        # Deploy MkDocs to GitHub Pages
│
├── services/                       # Microservice containers
│   ├── api/                        # FastAPI REST API service
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── routers/                # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── documents.py        # Document endpoints
│   │   │   ├── queries.py          # Query endpoints
│   │   │   ├── graph.py            # Graph exploration
│   │   │   └── health.py           # Health checks
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── document_service.py
│   │   │   ├── query_service.py
│   │   │   └── graph_service.py
│   │   ├── models/                 # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── requests.py
│   │   │   ├── responses.py
│   │   │   └── errors.py
│   │   ├── middleware.py           # Auth, logging, CORS
│   │   ├── dependencies.py         # Dependency injection
│   │   ├── config.py               # Settings management
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── tests/                  # API tests
│   │       ├── test_documents.py
│   │       ├── test_queries.py
│   │       └── conftest.py         # Pytest fixtures
│   │
│   ├── lightrag/                   # LightRAG integration service
│   │   ├── service.py              # LightRAG wrapper
│   │   ├── storage_adapters.py     # Neo4j adapters
│   │   ├── config.py               # LightRAG config
│   │   ├── Dockerfile              # (Optional if separate)
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_lightrag.py
│   │
│   ├── rag-anything/               # Document processing service
│   │   ├── service.py              # Parsing orchestration
│   │   ├── parsers/
│   │   │   ├── mineru_parser.py    # MinerU integration
│   │   │   └── docling_parser.py   # Future parser
│   │   ├── processors/             # Content processors
│   │   │   ├── image_processor.py
│   │   │   ├── table_processor.py
│   │   │   └── equation_processor.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── tests/
│   │       ├── test_parsers.py
│   │       └── test_processors.py
│
├── shared/                         # Shared Python modules
│   ├── __init__.py
│   ├── models/                     # Shared Pydantic models
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── entity.py
│   │   ├── relationship.py
│   │   └── query.py
│   ├── config/                     # Shared configuration
│   │   ├── __init__.py
│   │   └── settings.py
│   └── utils/                      # Shared utilities
│       ├── __init__.py
│       ├── logging.py              # structlog setup
│       └── validators.py
│
├── integrations/                   # Pre-built integrations
│   ├── openwebui/                  # Open-WebUI function pipeline
│   │   ├── rag_engine_function.py  # Single-file pipeline
│   │   ├── README.md               # Installation instructions
│   │   └── example_config.json     # Configuration template
│   │
│   ├── mcp/                        # MCP server (Phase 2)
│   │   ├── server.py               # MCP protocol implementation
│   │   ├── tools.py                # MCP tool definitions
│   │   └── README.md
│   │
│   └── n8n/                        # n8n nodes (Phase 2)
│       ├── nodes/
│       │   ├── RagEngineIngest.node.ts
│       │   └── RagEngineQuery.node.ts
│       ├── package.json
│       └── README.md
│
├── infrastructure/                 # Deployment configurations
│   ├── docker-compose.yml          # Main Docker Compose file
│   ├── docker-compose.dev.yml      # Development overrides
│   ├── docker-compose.prod.yml     # Production optimizations
│   ├── neo4j/
│   │   └── neo4j.conf              # Neo4j configuration
│   ├── nginx/                      # Optional reverse proxy
│   │   └── nginx.conf
│   └── k8s/                        # Kubernetes manifests (Phase 2)
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
│
├── scripts/                        # Utility scripts
│   ├── setup.sh                    # Initial setup script
│   ├── backup_neo4j.sh             # Backup automation
│   ├── restore_neo4j.sh            # Restore from backup
│   └── health_check.sh             # Deployment health check
│
├── docs/                           # Documentation
│   ├── index.md                    # MkDocs homepage
│   ├── architecture.md             # This document
│   ├── prd.md                      # Product requirements
│   ├── brief.md                    # Project brief
│   ├── api-reference.md            # OpenAPI documentation
│   ├── deployment-guide.md         # Installation instructions
│   ├── integration-guides/         # Per-integration docs
│   │   ├── openwebui.md
│   │   ├── mcp.md
│   │   └── n8n.md
│   ├── sources/                    # Technical research
│   │   ├── lightrag-readme.md
│   │   └── rag-anything-readme.md
│   └── mkdocs.yml                  # MkDocs configuration
│
├── tests/                          # Integration tests
│   ├── integration/
│   │   ├── test_e2e_workflow.py    # End-to-end tests
│   │   └── test_api_integration.py
│   └── performance/
│       └── test_load.py            # Load testing
│
├── .env.example                    # Environment template
├── .gitignore
├── docker-compose.yml              # Symlink to infrastructure/
├── pyproject.toml                  # Python project config
├── pytest.ini                      # Pytest configuration
├── README.md                       # Project README
└── LICENSE                         # Open-source license
```

---
