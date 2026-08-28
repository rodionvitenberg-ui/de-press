# AI gateway via OpenAI-compatible HTTP (DeepSeek default)

Support chat goes through Django `apps.ai` only — never from the browser with a secret key. The gateway speaks the OpenAI chat-completions protocol so we can point `AI_BASE_URL` / `AI_MODEL` at DeepSeek (project default), xAI, or another compatible host without rewriting callers. Empty `AI_API_KEY` uses an offline soft template (dev/tests), not silence. Conversations are not stored as training data or emotional maps on the server; crisis heuristics short-circuit before the model.
