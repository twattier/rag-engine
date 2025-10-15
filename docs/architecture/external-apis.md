# External APIs

## OpenAI API (Optional)

- **Purpose:** LLM completions and embeddings for advanced use cases
- **Documentation:** https://platform.openai.com/docs/api-reference
- **Base URL(s):** `https://api.openai.com/v1`
- **Authentication:** Bearer token (API key in Authorization header)
- **Rate Limits:** Varies by tier (check OpenAI dashboard)

**Key Endpoints Used:**
- `POST /chat/completions` - Generate chat responses (via LiteLLM)
- `POST /embeddings` - Generate embedding vectors (via LiteLLM)

**Integration Notes:** Accessed via LiteLLM proxy, not directly. Users configure API keys in LiteLLM config. Fallback to local models supported.

---

## Anthropic API (Optional)

- **Purpose:** Claude models for high-quality reasoning and long-context queries
- **Documentation:** https://docs.anthropic.com/claude/reference
- **Base URL(s):** `https://api.anthropic.com/v1`
- **Authentication:** x-api-key header
- **Rate Limits:** Varies by tier

**Key Endpoints Used:**
- `POST /messages` - Claude chat completions (via LiteLLM OpenAI-compatible wrapper)

**Integration Notes:** Accessed via LiteLLM proxy with OpenAI-compatible interface. Requires `litellm` to translate OpenAI format to Anthropic format.

---

## Jina AI Reranker API (Optional)

- **Purpose:** Reranking retrieved chunks for improved relevance
- **Documentation:** https://jina.ai/reranker/
- **Base URL(s):** `https://api.jina.ai/v1`
- **Authentication:** Bearer token
- **Rate Limits:** Varies by plan

**Key Endpoints Used:**
- `POST /rerank` - Rerank text passages by relevance to query

**Integration Notes:** LightRAG supports Jina reranker natively. Configure via `rerank_model_func` parameter. Can also use local MS Marco reranker model (no API required).

---
