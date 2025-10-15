I want to create an ultimate RAG engine service to be used by other applications as :
- pydantic agent tool
- n8n agent tool
- MCP server
- function in open-webui (can be manage with n8n webhook)

Objective : create a full docker stack
Provide the requirement and configuration for a full local ai stack (database, ...)
LLM capabilities : embedding, inference, reranker, ... can be local with ollama or with openAI standard API (LIteLLM, ...)

Using RAG-Anything framwork : https://github.com/HKUDS/RAG-Anything
Providing key feature : 
🔄 End-to-End Multimodal Pipeline - Complete workflow from document ingestion and parsing to intelligent multimodal query answering
📄 Universal Document Support - Seamless processing of PDFs, Office documents, images, and diverse file formats
🧠 Specialized Content Analysis - Dedicated processors for images, tables, mathematical equations, and heterogeneous content types
🔗 Multimodal Knowledge Graph - Automatic entity extraction and cross-modal relationship discovery for enhanced understanding
⚡ Adaptive Processing Modes - Flexible MinerU-based parsing or direct multimodal content injection workflows
📋 Direct Content List Insertion - Bypass document parsing by directly inserting pre-parsed content lists from external sources
🎯 Hybrid Intelligent Retrieval - Advanced search capabilities spanning textual and multimodal content with contextual understanding

Expose the API and web UI (LightRAG server ?) to explore the kwnoledge base


