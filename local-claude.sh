#!/bin/zsh
# Run Claude Code against a local Ollama model.
# usage: local-claude [model] [extra claude args...]
#   default model: qwen3.5:9b   (others: mimo-v2.6:9b, qwen3.5:4b-mtp-q4_K_M)
# Uses a sized variant (num_ctx baked in) when one exists, because the Ollama app defaults to 4096:
#   qwen3.5:9b-48k, mimo-v2.6:9b-48k, qwen3.5:4b-mtp-q4_K_M-64k   (sizes chosen from a memory sweep on 16 GB)
if [[ -n $1 && $1 != -* ]]; then MODEL=$1; shift; else MODEL=qwen3.5:9b; fi
CTX=32768
if [[ $MODEL =~ -([0-9]+)k$ ]]; then
  CTX=$(( ${match[1]} * 1024 ))
else
  for s in 64 48 32; do
    if ollama show "$MODEL-${s}k" >/dev/null 2>&1; then MODEL=$MODEL-${s}k; CTX=$(( s * 1024 )); break; fi
  done
fi
echo "local-claude: $MODEL (context $CTX)" >&2

export ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama ANTHROPIC_API_KEY=""
export ANTHROPIC_MODEL=$MODEL ANTHROPIC_DEFAULT_OPUS_MODEL=$MODEL ANTHROPIC_DEFAULT_SONNET_MODEL=$MODEL
export ANTHROPIC_DEFAULT_HAIKU_MODEL=$MODEL CLAUDE_CODE_SUBAGENT_MODEL=$MODEL
# Without this, Claude Code reserves 32K for output and a small window thrashes on autocompact.
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=4096
# Real window = CTX. The auto-compact window has a 100K floor in Claude Code, so it is set to that floor.
export CLAUDE_CODE_MAX_CONTEXT_TOKENS=$CTX CLAUDE_CODE_AUTO_COMPACT_WINDOW=100000
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 API_TIMEOUT_MS=3000000 CLAUDE_CODE_ATTRIBUTION_HEADER=0
exec claude "$@"
