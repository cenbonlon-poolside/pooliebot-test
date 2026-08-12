import os
import re
import io
import time
import discord
from openai import OpenAI
from dotenv import load_dotenv
import cairosvg

load_dotenv()

client = OpenAI(
    api_key=os.environ["POOLSIDE_API_KEY"],
    base_url="https://inference.poolside.ai/v1",
)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents, reconnect=True)

# Rate limiting: per-user cooldown in seconds
last_call = {}
COOLDOWN = 10

# Channel allowlist - add your channel IDs here
ALLOWED_CHANNELS = {1537076245278359582}

SYSTEM = """You are Poolie, the Poolside community bot. Be brief and factual.

## Poolside Models

**Laguna S 2.1** (118B total, 8B active, MoE, 1M context) - Best for long-horizon agentic coding
**Laguna XS 2.1** (33B total, 3B active, MoE, 256K context) - Fast agentic coding, runs on Mac with 36GB RAM
**Laguna M.1** (225B total, 23B active, MoE, 256K context) - Complex multi-step coding tasks
**Laguna XS.2** - Second gen, trades performance for speed

All Laguna models: native reasoning (thinking off or max), text-to-text only, open-weight releases under OpenMDW-1.1.

## Open Weights & HuggingFace

Download from HuggingFace:
- https://huggingface.co/poolside/Laguna-S-2.1
- https://huggingface.co/poolside/Laguna-XS-2.1

Quantizations: BF16, FP8, INT4, NVFP4, GGUF, MLX
Run locally with: pool, vLLM, SGLang, Ollama, llama.cpp, MLX, TensorRT-LLM

## Inference Access

1. **Poolside Platform** (platform.poolside.ai): `https://inference.poolside.ai/v1`
2. **OpenRouter** (openrouter.ai/poolside): Paid/free Poolside models
3. **Kilo Gateway** (kilo.ai/models/by/poolside): Free Poolside models
4. **Self-managed**: Deploy in your own VPC/on-prem

## Tool Integrations

**Editors**: Poolside Assistant (ACP), Cline, Kilo Code, JetBrains, Zed, Neovim
**Kilo Code**: Settings → Providers → Custom provider → Base URL: `https://inference.poolside.ai/v1`
**OpenRouter**: Available in Cline, Kilo Code, and other tools supporting OpenRouter

## The pool CLI

- Interactive: `pool` (TUI with plan mode, slash commands, skills)
- Automated: `pool exec` (CI/CD, scripts)
- Editor integration: `pool acp` (ACP-compatible editors)

If you don't know something, say so and point to docs.poolside.ai."""

def chunk_text(text, max_len=1900):
    """Discord-safe chunking"""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

def extract_svg(text):
    """Extract SVG code from response"""
    match = re.search(r'<svg[^>]*>.*?</svg>', text, re.DOTALL | re.IGNORECASE)
    return match.group(0) if match else None

def svg_to_png_bytes(svg_code, width=400, height=300):
    """Convert SVG to PNG bytes"""
    try:
        png_bytes = cairosvg.svg2png(bytestring=svg_code.encode('utf-8'), output_width=width, output_height=height)
        return io.BytesIO(png_bytes)
    except Exception as e:
        print(f"SVG conversion failed: {e}")
        return None

@bot.event
async def on_ready():
    print(f"online as {bot.user}")
    print(f"listening in channels: {ALLOWED_CHANNELS}")

@bot.event
async def on_disconnect():
    print("bot disconnected - attempting reconnect...")

@bot.event
async def on_resumed():
    print("bot connection resumed")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user not in message.mentions:
        return

    # Rate limiting
    now = time.time()
    if now - last_call.get(message.author.id, 0) < COOLDOWN:
        return
    last_call[message.author.id] = now

    # Channel restriction
    if message.channel.id not in ALLOWED_CHANNELS:
        return

    prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
    if not prompt:
        return

    async with message.channel.typing():
        try:
            completion = client.chat.completions.create(
                model="poolside/laguna-s-2.1",
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = "Having trouble right now, try again in a moment."
            await message.reply(reply)
            return

    # Check for SVG and convert to image
    svg = extract_svg(reply)
    if svg:
        png_bytes = svg_to_png_bytes(svg)
        if png_bytes:
            # Send image with text explanation
            text_only = re.sub(r'<svg[^>]*>.*?</svg>', '[Image generated below]', reply, flags=re.DOTALL | re.IGNORECASE).strip()
            if not text_only or text_only == '[Image generated below]':
                text_only = "Here's your generated image:"
            await message.reply(text_only)
            await message.reply(file=discord.File(png_bytes, filename="generated.png"))
            return

    # Discord message limit is 2000 chars, use 1900 for safety margin
    for i in range(0, len(reply), 1900):
        await message.reply(reply[i:i+1900])

if __name__ == "__main__":
    while True:
        try:
            bot.run(os.environ["DISCORD_TOKEN"])
        except Exception as e:
            print(f"Bot crashed: {e}. Restarting in 5 seconds...")
            time.sleep(5)
