import os
import json
import re
import io
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from openai import OpenAI
import urllib.request

# Discord public key from environment (for signature verification)
PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

client = OpenAI(
    api_key=os.environ.get("POOLSIDE_API_KEY"),
    base_url="https://inference.poolside.ai/v1",
)

SYSTEM = """You are Poolie, the Poolside community bot. Be brief and factual.

## Poolside Models

**Laguna S 2.1** (118B total, 8B active, MoE, 1M context) - Best for long-horizon agentic coding
**Laguna XS 2.1** (33B total, 3B active, MoE, 256K context) - Fast agentic coding, runs on Mac with 36GB RAM
**Laguna M.1** (225B total, 23B active, MoE, 256K context) - Complex multi-step coding tasks

## Open Weights & HuggingFace
- https://huggingface.co/poolside/Laguna-S-2.1

## Inference Access
1. Poolside Platform: https://inference.poolside.ai/v1
2. OpenRouter: https://openrouter.ai/poolside

## Tool Integrations
- Editors: Poolside Assistant, Cline, Kilo Code, JetBrains, Zed, Neovim

If you don't know something, say so and point to docs.poolside.ai."""

def verify_signature(event):
    """Verify Discord signature"""
    signature = event['headers'].get('x-signature-ed25519')
    timestamp = event['headers'].get('x-signature-timestamp')
    body = event['body']
    
    if not signature or not timestamp:
        return False
    
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    try:
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False

def lambda_handler(event, context):
    # API Gateway v2 format
    if event.get('requestContext', {}).get('http', {}).get('method') == 'POST':
        headers = event.get('headers', {}) or {}
        
        # Verify Discord signature
        signature = headers.get('x-signature-ed25519') or headers.get('X-Signature-Ed25519')
        timestamp = headers.get('x-signature-timestamp') or headers.get('X-Signature-Timestamp')
        body = event.get('body', '')
        
        if signature and timestamp:
            try:
                verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
                verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
            except (BadSignatureError, Exception) as e:
                return {'statusCode': 401, 'body': 'Unauthorized'}
        
        body_json = json.loads(body) if body else {}
        
        # Ping/Pong for Discord verification
        if body_json.get('type') == 1:
            return {'statusCode': 200, 'body': json.dumps({'type': 1})}
        
        # Slash command interaction
        if body_json.get('type') == 2:
            command = body_json.get('data', {}).get('name')
            
            if command == 'ask':
                prompt = body_json['data']['options'][0]['value']
                
                try:
                    completion = client.chat.completions.create(
                        model="poolside/laguna-s-2.1",
                        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                    )
                    reply = completion.choices[0].message.content
                except Exception as e:
                    reply = "Having trouble right now, try again in a moment."
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'type': 4,
                        'data': {
                            'content': reply[:2000]
                        }
                    })
                }
    
    return {'statusCode': 200, 'body': 'OK'}
