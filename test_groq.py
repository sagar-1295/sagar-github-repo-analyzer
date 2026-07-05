"""
Test script to verify Groq API key is working.
"""

import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print(f"GROQ_API_KEY loaded: {bool(GROQ_API_KEY)}")

if not GROQ_API_KEY:
    print("ERROR: GROQ_API_KEY not found in .env")
    exit(1)

# Test basic completion
try:
    print("\n1. Testing basic completion...")
    response = completion(
        model="groq/llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": "What is 2 + 2?"}
        ],
    )
    print(f"✓ Success! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test with tools
try:
    print("\n2. Testing with tools/functions...")
    response = completion(
        model="groq/llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": "Get info about facebook/react repo. Repository info: 246k stars, 51k forks, JavaScript."}
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_repo_info",
                    "description": "Get repository metadata",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string"},
                            "repo": {"type": "string"},
                        },
                        "required": ["owner", "repo"],
                    },
                },
            }
        ],
    )
    print(f"✓ Success with tools! Response: {response.choices[0].message.content}")
    tool_calls = getattr(response.choices[0].message, "tool_calls", None)
    if tool_calls:
        print(f"  Tool calls found: {len(tool_calls)}")
except Exception as e:
    print(f"✗ Failed with tools: {e}")

print("\n✓ Groq API key is working!")
