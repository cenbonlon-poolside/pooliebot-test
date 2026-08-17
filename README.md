# Poolie Discord Bot

A Poolside community bot that answers questions about Poolside models, the pool CLI, and agentic coding. Powered by `poolside/laguna-s-2.1`.

Poolie acts like a supportive colleague - asking follow-up questions, keeping conversations natural, and helping you build cool stuff.

## Features

- **Mention responses** - Bot replies when `@Poolie` is mentioned
- **Slash commands** - `/ask <question>` and `/feedback` endpoints
- **Per-user 10-second cooldown** - Rate limiting prevents spam
- **Channel allowlist** - Controlled deployment (staff channel only)
- **Conversation history** - Rolling buffer maintains context (10 messages)
- **Agent loop with tool calling** - Model can call tools for model info, docs, replies
- **Automatic SVG to PNG conversion** - Renders SVG code as images
- **Rich embeds** - Formatted responses for model-related questions
- **Feedback tracking** - Logs 👍/👎 reactions for training data

## Deployment

### Local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### EC2
```bash
# Install dependencies
sudo yum install -y cairo-devel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup python3 bot.py > bot.log 2>&1 &
```

### Lambda (Slash Commands Only)
See `lambda/` directory and `terraform/` for infrastructure-as-code deployment.

## Repository Structure

```
poolie/
├── bot.py              # Main Discord bot with agent loop
├── explanation.md      # Detailed documentation  
├── ARCHITECTURE.md     # Architecture overview
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── lambda/             # Serverless alternative (slash commands only)
│   └── app.py
└── terraform/          # Infrastructure as code
    └── modules/aws/
        └── main.tf
```

## Test Commands

- `@Poolie what is laguna-s-2.1?`
- `@Poolie tell me about Kilo Code integration`
- `/ask how do I use pool CLI?`
- `/feedback` (with rating)