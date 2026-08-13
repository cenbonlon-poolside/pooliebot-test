import os
import re
import io
import time
import json
import asyncio
from collections import defaultdict
from functools import lru_cache
import discord
from discord import app_commands
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import cairosvg

load_dotenv()

# Async client for better performance
client = AsyncOpenAI(
    api_key=os.environ["POOLSIDE_API_KEY"],
    base_url="https://inference.poolside.ai/v1",
)

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = discord.Client(intents=intents, reconnect=True)
tree = app_commands.CommandTree(bot)

# Rate limiting
last_call = {}
COOLDOWN = 10

# Channel allowlist
ALLOWED_CHANNELS = {1537076245278359582}

# Conversation history (rolling buffer per channel)
message_history = defaultdict(list)
HISTORY_MAX = 10

# Feedback tracking
feedback_log = []

# Channel topics/contexts
CHANNEL_CONTEXT = {
    1537076245278359582: "Staff testing and internal discussions",
}

# Tool detection keywords
TOOL_KEYWORDS = {
    "kilo code": "Kilo Code: Settings → Providers → Custom provider → Base URL: `https://inference.poolside.ai/v1`",
    "cline": "Cline: Use OpenAI-compatible endpoint at `https://inference.poolside.ai/v1`",
    "jetbrains": "JetBrains: Use `pool acp` for ACP integration",
    "zed": "Zed: Configure external agent at `https://docs.poolside.ai/tools/zed`",
    "copilot": "GitHub Copilot: Poolside models available via OpenRouter",
}

# Docs links
DOCS_LINKS = {
    "laguna": "https://docs.poolside.ai/get-started/supported-models",
    "pool": "https://docs.poolside.ai/cli/pool",
    "api": "https://docs.poolside.ai/api/overview",
    "huggingface": "https://huggingface.co/poolside",
}

SYSTEM_BASE = """You are Poolie, the Poolside community bot. Be brief and factual.

## Poolside Models

**Laguna S 2.1** (118B total, 8B active, MoE, 1M context) - Best for long-horizon agentic coding
**Laguna XS 2.1** (33B total, 3B active, MoE, 256K context) - Fast agentic coding, runs on Mac with 36GB RAM
**Laguna M.1** (225B total, 23B active, MoE, 256K context) - Complex multi-step coding tasks

## Open Weights & HuggingFace
- https://huggingface.co/poolside/Laguna-S-2.1
- https://huggingface.co/poolside/Laguna-XS-2.1

## Inference Access
1. Poolside Platform: https://inference.poolside.ai/v1
2. OpenRouter: https://openrouter.ai/poolside
3. Kilo Gateway: https://kilo.ai/models/by/poolside

## Tool Integrations
- Editors: Poolside Assistant (ACP), Cline, Kilo Code, JetBrains, Zed, Neovim

## The pool CLI
- Interactive: `pool` (TUI with plan mode, slash commands, skills)
- Automated: `pool exec` (CI/CD)
- Editor: `pool acp` (ACP editors)

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

@lru_cache(maxsize=32)
def get_cached_response(prompt_hash):
    """Cache frequent responses"""
    return None

def detect_tool(text):
    """Detect tool mentions and return relevant info"""
    text_lower = text.lower()
    for tool, info in TOOL_KEYWORDS.items():
        if tool in text_lower:
            return info
    return None

def build_system_prompt(channel_id):
    """Build SYSTEM prompt with channel context"""
    base = SYSTEM_BASE
    if channel_id in CHANNEL_CONTEXT:
        base += f"\n\nChannel context: {CHANNEL_CONTEXT[channel_id]}"
    return base

@bot.event
async def on_ready():
    print(f"online as {bot.user}")
    print(f"listening in channels: {ALLOWED_CHANNELS}")
    # Register slash commands
    try:
        await tree.sync()
        print("Slash commands synced")
    except Exception as e:
        print(f"Slash command sync failed: {e}")

@bot.event
async def on_disconnect():
    print("bot disconnected - attempting reconnect...")

@bot.event
async def on_resumed():
    print("bot connection resumed")

@bot.event
async def on_raw_reaction_add(payload):
    """Track feedback via reactions"""
    if payload.emoji.name in ["👍", "👎"]:
        try:
            channel = bot.get_channel(payload.channel_id)
            if channel:
                message = await channel.fetch_message(payload.message_id)
                feedback_log.append({
                    "timestamp": time.time(),
                    "emoji": payload.emoji.name,
                    "channel_id": payload.channel_id,
                    "user_id": payload.user_id,
                    "bot_message": message.content[:200] if message.author == bot.user else None
                })
                # Save to file
                with open("feedback_log.json", "w") as f:
                    json.dump(feedback_log[-100:], f)
        except Exception as e:
            print(f"Feedback tracking error: {e}")

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

    # Update conversation history
    message_history[message.channel.id].append({"role": "user", "content": prompt})
    message_history[message.channel.id] = message_history[message.channel.id][-HISTORY_MAX:]

    async with message.channel.typing():
        try:
            # Check for tool-specific help
            tool_info = detect_tool(prompt)
            
            # Build messages with history
            messages = [{"role": "system", "content": build_system_prompt(message.channel.id)}]
            
            # Add recent history
            for msg in message_history[message.channel.id][-5:]:
                messages.append(msg)
            
            if tool_info:
                prompt = f"{prompt}\n\n{tool_info}"
                messages[-1] = {"role": "user", "content": prompt}

            completion = await client.chat.completions.create(
                model="poolside/laguna-s-2.1",
                messages=messages,
            )
            reply = completion.choices[0].message.content
            
            # Update history with bot response
            message_history[message.channel.id].append({"role": "assistant", "content": reply})
            
        except Exception as e:
            reply = "Having trouble right now, try again in a moment."
            await message.reply(reply)
            return

    # Check for SVG and convert to image
    svg = extract_svg(reply)
    if svg:
        png_bytes = svg_to_png_bytes(svg)
        if png_bytes:
            text_only = re.sub(r'<svg[^>]*>.*?</svg>', '[Image generated below]', reply, flags=re.DOTALL | re.IGNORECASE).strip()
            if not text_only or text_only == '[Image generated below]':
                text_only = "Here's your generated image:"
            await message.reply(text_only)
            await message.reply(file=discord.File(png_bytes, filename="generated.png"))
            return

    # Rich embed for structured responses
    if "laguna" in reply.lower():
        embed = discord.Embed(
            title="Poolie Response",
            description=reply[:4096],
            color=0x0066ff
        )
        embed.add_field(name="Models", value="[Laguna S 2.1](https://huggingface.co/poolside/Laguna-S-2.1)", inline=True)
        embed.add_field(name="Docs", value="[docs.poolside.ai](https://docs.poolside.ai)", inline=True)
        await message.reply(embed=embed)
        return

    # Regular text reply with chunking
    for i in range(0, len(reply), 1900):
        await message.reply(reply[i:i+1900])

@tree.command(name="ask", description="Ask Poolie about Poolside models, CLI, or tools")
async def ask(interaction: discord.Interaction, question: str):
    """Slash command for asking Poolie questions"""
    if interaction.channel_id not in ALLOWED_CHANNELS:
        await interaction.response.send_message("Bot not available in this channel.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        completion = await client.chat.completions.create(
            model="poolside/laguna-s-2.1",
            messages=[
                {"role": "system", "content": build_system_prompt(interaction.channel_id)},
                {"role": "user", "content": question}
            ]
        )
        reply = completion.choices[0].message.content
        
        embed = discord.Embed(
            title="Poolie",
            description=reply[:4096],
            color=0x0066ff
        )
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send("Having trouble right now, try again in a moment.")

@tree.command(name="feedback", description="Provide feedback about Poolie's responses")
async def feedback(interaction: discord.Interaction, response_id: str, rating: int, comments: str = None):
    """Feedback command for training data"""
    feedback_log.append({
        "timestamp": time.time(),
        "rating": rating,
        "comments": comments,
        "user_id": interaction.user.id
    })
    with open("feedback_log.json", "w") as f:
        json.dump(feedback_log[-100:], f)
    await interaction.response.send_message("Thanks for the feedback! 👍", ephemeral=True)

if __name__ == "__main__":
    while True:
        try:
            bot.run(os.environ["DISCORD_TOKEN"])
        except Exception as e:
            print(f"Bot crashed: {e}. Restarting in 5 seconds...")
            time.sleep(5)