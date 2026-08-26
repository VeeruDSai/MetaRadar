# MetaRadar Local Models Directory (`models/`)

This directory stores local quantized reasoning models in GGUF format (`*.gguf`) for offline, zero-latency, private reasoning inference.

## How to use:
1. Place any GGUF reasoning model (e.g. `gemma-3-4b-it-Q4_K_M.gguf`, `qwen2.5-7b-instruct-q4_k_m.gguf`, `llama-3.2-3b-instruct-q4_k_m.gguf`) into this directory.
2. MetaRadar automatically scans this folder upon startup and loads the `.gguf` model for:
   - Four-Question Narrative Synthesis
   - Red-Team Contradiction Reasoning
   - Ask Athena Grounded Clinical Q&A
3. You can also specify an exact model file in `.env`:
   ```env
   LOCAL_GGUF_MODEL=gemma-3-4b-it-Q4_K_M.gguf
   ```
4. If no `.gguf` file is present in `models/`, MetaRadar checks the local Ollama daemon (`http://localhost:11434`), and falls back to Hosted Grok (if configured) or BART Degraded Factual mode.
