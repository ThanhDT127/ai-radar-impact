"""Quick smoke test for Vertex AI connection."""
from app.ai.gemini_client import GeminiClient, MODEL_ID

client = GeminiClient()

# 1. List available Gemini models
print("=== Available Gemini Models ===")
try:
    for m in client._client.models.list():
        if "gemini" in m.name.lower():
            print(f"  {m.name}")
except Exception as e:
    print(f"  Could not list models: {e}")

# 2. Smoke test with current MODEL_ID
print(f"\n=== Testing MODEL: {MODEL_ID} ===")
result = client.analyze(
    title="OpenAI launches GPT-5 with multimodal reasoning",
    content="OpenAI announced GPT-5 today, featuring advanced reasoning capabilities and native multimodal support including vision, audio, and code generation.",
)
print(f"Error     : {result.error}")
print(f"Topics    : {result.topics}")
print(f"Event type: {result.event_type}")
print(f"Nature    : {result.nature}")
print(f"Summary   : {result.summary_short}")
print(f"Confidence: {result.confidence}")
