# Poolie Discord Bot

A Poolside community bot that answers questions about Poolside models, the pool CLI, and agentic coding.

## Features

- Responds when mentioned
- Per-user 10-second cooldown
- Channel allowlist for controlled deployment
- Automatic message chunking (Discord's 2000 char limit)
- Basic error handling
- SVG to PNG image conversion (auto-detects and renders SVG code)

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
├── bot.py              # Main Discord bot
├── explanation.md      # Detailed documentation
├── ARCHITECTURE.md     # Architecture overview
├── requirements.txt    # Python dependencies
├── lambda/             # Lambda deployment alternative
└── terraform/          # Infrastructure as code
