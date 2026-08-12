# Poolie Discord Bot Architecture

## Overview

Two bots for Poolside community support:

1. **poolie/** - Main community bot (responds to user mentions)
2. **poolie-analytics/** - Admin bot (generates weekly reports from conversations)

Both powered by Poolside's laguna-s-2.1 model via the Poolside Inference API.

---

## Request Flow: Main Bot (poolie/)

```
User mentions @Poolie in Discord
         ↓
Discord Gateway → bot.py on_message()
         ↓
[Cosmetic checks: bot.user, mention detection]
         ↓
[Security: Channel allowlist, rate limiting]
         ↓
Prompt extraction (remove @ mention from message text)
         ↓
OpenAI client → https://inference.poolside.ai/v1/chat/completions
         ↓
Model: poolside/laguna-s-2.1
System prompt: Poolside knowledge base (models, HF, tools, CLI)
User prompt: cleaned question
         ↓
Poolie response streamed back
         ↓
[Error handling: catch API failures, send fallback message]
         ↓
Message chunking (1900 char segments for Discord 2000 limit)
         ↓
Discord Response via message.reply()
```

---

## Request Flow: Analytics Bot (poolie-analytics/)

```
User says !poolie-summary (admin only)
         ↓
Analytics bot on_message()
         ↓
[Admin check via role ID]
         ↓
Load logged conversations from conversation_log.json
         ↓
Build prompt with conversation data
         ↓
OpenAI client → https://inference.poolside.ai/v1/chat/completions
         ↓
Model: poolside/laguna-s-2.1
Prompt: "Analyze Discord conversations for bugs, questions, feature requests"
         ↓
Structured weekly report generated
         ↓
Chunk and send to Discord
```

---

## Components

### Main Bot (bot.py)
- **Discord Client**: Handles gateway connection, message events
- **Rate Limiter**: In-memory dict, 10s per-user cooldown
- **Channel Guard**: ALLOWED_CHANNELS set restricts where bot responds
- **OpenAI Client**: Connects to Poolside Inference API
- **SYSTEM Prompt**: Curated Poolside knowledge base (models, tools, integrations)
- **Chunker**: Splits responses to fit Discord's 2000 char limit

### Analytics Bot (analytics_bot.py)
- **Extended Intents**: Members, guilds, message content
- **Conversation Logger**: Persists Q&A to conversation_log.json
- **Admin Guard**: ADMIN_ROLE_ID restricts summary commands
- **Report Generator**: Uses same Poolside model for analysis

---

## Configuration

```
.env (per bot)
├── DISCORD_TOKEN    # Bot token from Discord Dev Portal
└── POOLSIDE_API_KEY # Key from platform.poolside.ai

bot.py variables
├── ALLOWED_CHANNELS  # Set of channel IDs (empty = all channels)
├── COOLDOWN          # Seconds between calls per user
└── SYSTEM           # Knowledge base prompt

analytics_bot.py variables
├── ADMIN_ROLE_ID     # Role ID for report access
└── LOG_FILE          # conversation_log.json path
```

---

## Deployment

```bash
# Main bot
cd poolie
source .venv/bin/activate
python bot.py

# Analytics bot  
cd poolie-analytics
source .venv/bin/activate  # (or create new venv)
python analytics_bot.py
```

Both require:
- Discord application with Message Content Intent enabled
- Bot invited to server with proper permissions
- Valid Poolside API key
