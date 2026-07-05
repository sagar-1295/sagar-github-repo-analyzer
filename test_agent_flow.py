"""
Test agent flow with Groq to identify the issue.
"""

import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_repo_summary",
            "description": "Get repository metadata such as stars, forks, language, and last update time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                },
                "required": ["owner", "repo"],
            },
        },
    },
]

print("Test 1: Initial tool-calling request")
try:
    response1 = completion(
        model="groq/llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": "Tell me about facebook/react repo"}
        ],
        tools=TOOLS,
    )
    print(f"✓ First call succeeded")
    message1 = response1.choices[0].message
    tool_calls = getattr(message1, "tool_calls", None) or []
    print(f"  Tool calls: {len(tool_calls)}")
    if tool_calls:
        print(f"  First tool: {tool_calls[0].function.name}")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

print("\nTest 2: Follow-up with tool results")
try:
    # Get the tool_call_id from the first response
    tool_call_id = tool_calls[0].id if tool_calls else "call_123"
    
    follow_up = [
        {"role": "user", "content": "Tell me about facebook/react repo"},
        {"role": "assistant", "content": "I'll get the repo summary for you.", "tool_calls": [{"id": tool_call_id, "type": "function", "function": {"name": "get_repo_summary", "arguments": '{"owner": "facebook", "repo": "react"}'}}]},
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": "get_repo_summary",
            "content": '{"stars": 246261, "forks": 51204, "language": "JavaScript", "updated": "2024-01-15"}',
        }
    ]
    response2 = completion(
        model="groq/llama-3.1-8b-instant",
        messages=follow_up,
    )
    print(f"✓ Follow-up call succeeded")
    print(f"  Response: {response2.choices[0].message.content[:100]}...")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n✓ Agent flow test complete!")
