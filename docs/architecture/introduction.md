# Introduction

This document outlines the complete full-stack architecture for RAG Engine, a production-ready Retrieval-Augmented Generation framework designed as an enabler for easy-to-deploy knowledge management assistants. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This architecture integrates LightRAG (graph-based retrieval) and RAG-Anything (multi-format document processing) into a unified, Docker-based system optimized for ultimate RAG performance with operational excellence.

## Starter Template or Existing Project

**Base Project**: This is a greenfield project built on top of:
- **LightRAG** (https://github.com/HKUDS/LightRAG) - Graph-based retrieval engine with Neo4j integration
- **RAG-Anything** (https://github.com/HKUDS/RAG-Anything) - Multi-modal document processing framework

**Constraints**:
- Must maintain compatibility with LightRAG's existing API surface
- Neo4j graph database is mandatory for LightRAG functionality
- Python 3.11+ required for LightRAG/RAG-Anything compatibility
- Docker Compose deployment model as primary installation method

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-15 | 1.0 | Initial architecture document | Winston (Architect Agent) |

---
