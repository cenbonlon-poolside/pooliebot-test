# Poolie Discord Bot - Explanation

## Overview

Poolie is a Poolside community Discord bot that answers questions about Poolside models, tools, and agentic coding. It's powered by `poolside/laguna-s-2.1` via the Poolside Inference API.

---

## Architecture

### Components

```
bot.py
├── Discord Client (discord.py)
├── Poolside API Client (OpenAI-compatible)
├── Rate Limiter (in-memory dict, 10s cooldown)
├── Channel Guard (ALLOWED_CHANNELS allowlist)
├── SVG Converter (cairosvg)
└── SYSTEM Prompt (Poolside knowledge base)
```

### Request Flow

```
User: @Poolie what is laguna-s-2.1?
    ↓
Discord Gateway → on_message()
    ↓
[Filters: self-message, non-mention, rate limit, channel check]
    ↓
Extract prompt (remove @ mention)
    ↓
Poolside Inference API (https://inference.poolside.ai/v1)
    ↓
Response with SYSTEM prompt + user question
    ↓
[SVG detection → convert to PNG image]
    ↓
Chunk response (1900 char segments)
    ↓
Discord reply
```

---

## Current Skills & Functionality

### 1. Poolside Model Knowledge

**Models Supported:**
- **Laguna S 2.1** - 118B total (8B active), MoE, 1M context, reasoning support
- **Laguna XS 2.1** - 33B total (3B active), 256K context, Mac-compatible
- **Laguna M.1** - 225B total (23B active), 256K context, complex tasks
- **Laguna XS.2** - Second generation, speed-focused

### 2. Open Weights & HuggingFace

- Direct links to HF model cards
- Quantization info: BF16, FP8, INT4, NVFP4, GGUF, MLX
- Local runtime options: pool, vLLM, SGLang, Ollama, llama.cpp, MLX, TensorRT-LLM

### 3. Inference Access Methods

- **Poolside Platform** (`platform.poolside.ai`) - Direct API access
- **OpenRouter** (`openrouter.ai/poolside`) - Paid/free models
- **Kilo Gateway** (`kilo.ai/models/by/poolside`) - Free models
- **Self-managed** - VPC/on-prem deployment

### 4. Tool Integrations

- **Editors**: Poolside Assistant (ACP), Cline, Kilo Code, JetBrains, Zed, Neovim
- **Kilo Code setup**: Custom provider with Poolside endpoint
- **OpenRouter**: Compatible with multiple tools

### 5. pool CLI Documentation

- `pool` - Interactive TUI with plan mode, slash commands, skills
- `pool exec` - Automated/CI-CD workflows  
- `pool acp` - Editor integration (ACP protocol)

### 6. SVG to Image Conversion

When the model returns SVG code:
- Automatically detects `<svg>...</svg>` tags
- Converts to PNG using cairosvg library
- Sends as image attachment instead of code block

---

## Configuration

### Environment Variables (.env)

```bash
DISCORD_TOKEN=MTUzNzA1MDI3MTYwNjM4MjU5Mg.GhxLGM...  # Bot token
POOLSIDE_API_KEY=sky_aUj0YNW3.lxSZMz4n8KAuCthKHNWd6duvieaIAmsi  # Poolside API key
```

### Code Variables (bot.py)

```python
ALLOWED_CHANNELS = {1537076245278359582}  # Staff channel only
COOLDOWN = 10  # Seconds between requests per user
```

---

## Deployment

### Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### EC2 Deployment

```bash
# On EC2
sudo yum install -y cairo-devel  # For SVG conversion
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup python3 bot.py > bot.log 2>&1 &
```

### Requirements

- discord.py>=2.3.0
- openai>=1.0.0
- python-dotenv>=1.0.0
- cairosvg>=2.7.0
- Message Content Intent enabled in Discord Dev Portal

---

## Hosting Options

### EC2 (Current)
- ✅ Persistent WebSocket connection
- ✅ Full feature support (mentions, SVG conversion)
- ✅ Always online
- Instance: `t3.micro` in `eu-west-3`

### Lambda (Alternative)
- ❌ No persistent WebSocket
- ✅ Slash commands only (`/ask`)
- ✅ No server management
- Uses AWS API Gateway + Lambda

---

## Security Notes

- `.env` contains secrets - never commit to version control
- `.gitignore` excludes `.env`, `.venv/`, `__pycache__/`
- Bot only responds in allowed channels
- Per-user rate limiting prevents spam

---

## Future Enhancements

- [ ] Analytics bot for weekly community summaries
- [ ] Feedback collection with user consent
- [ ] Slash command support alongside mentions
- [ ] Multi-channel deployment with role-based access