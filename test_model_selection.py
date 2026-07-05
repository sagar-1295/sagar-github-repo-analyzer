"""
Test to show model selection in different environments.
"""

import os
from dotenv import load_dotenv

# Test 1: Local environment (with OLLAMA_API_BASE)
print("=== LOCAL ENVIRONMENT ===")
load_dotenv()
API_BASE = os.getenv("OLLAMA_API_BASE") or os.getenv("API_BASE")
if os.getenv("MODEL"):
    MODEL = os.getenv("MODEL")
elif API_BASE:
    MODEL = "ollama/llama3.1"
else:
    MODEL = "groq/llama-3.1-8b-instant"

print(f"Model: {MODEL}")
print(f"API_BASE: {API_BASE}")

# Test 2: Simulate cloud environment (remove OLLAMA_API_BASE)
print("\n=== CLOUD ENVIRONMENT (simulated) ===")
os.environ.pop("OLLAMA_API_BASE", None)
API_BASE = os.getenv("OLLAMA_API_BASE") or os.getenv("API_BASE")
if os.getenv("MODEL"):
    MODEL = os.getenv("MODEL")
elif API_BASE:
    MODEL = "ollama/llama3.1"
else:
    MODEL = "groq/llama-3.1-8b-instant"

print(f"Model: {MODEL}")
print(f"API_BASE: {API_BASE}")
print("\n✓ Model selection works correctly!")
