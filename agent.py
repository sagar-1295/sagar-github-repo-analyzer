import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from litellm import completion
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

load_dotenv()

MODEL = os.getenv("MODEL", "ollama/llama3.1")
API_BASE = os.getenv("OLLAMA_API_BASE") or os.getenv("API_BASE") or "http://localhost:11434"

TOOLS: List[Dict[str, Any]] = [
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
    {
        "type": "function",
        "function": {
            "name": "get_recent_commits",
            "description": "List recent commit messages, authors, and dates for a repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["owner", "repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_open_issues",
            "description": "List open bug and issue tickets for a repository, excluding pull requests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["owner", "repo"],
            },
        },
    },
]


async def _call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content


def _safe_parse_arguments(raw_arguments: Optional[str]) -> Dict[str, Any]:
    if not raw_arguments:
        return {}
    try:
        parsed = json.loads(raw_arguments)
        if isinstance(parsed, dict):
            return parsed
        return {}
    except json.JSONDecodeError:
        return {}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if hasattr(value, "text"):
        return _json_safe(value.text)
    if hasattr(value, "content"):
        return _json_safe(value.content)
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    return str(value)


def _normalize_tool_result(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize_tool_result(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_tool_result(item) for key, item in value.items()}
    if hasattr(value, "content"):
        return _normalize_tool_result(value.content)
    if hasattr(value, "text"):
        text = getattr(value, "text")
        if isinstance(text, str):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
    if hasattr(value, "model_dump"):
        return _normalize_tool_result(value.model_dump())
    return str(value)


def _tool_result_to_text(value: Any) -> str:
    normalized = _normalize_tool_result(value)
    if isinstance(normalized, str):
        return normalized
    try:
        return json.dumps(normalized, default=str)
    except TypeError:
        return str(normalized)


def _fallback_summary(user_question: str, owner: str, repo: str) -> str:
    from github_client import get_repo_info, list_open_issues, list_recent_commits

    repo_info = get_repo_info(owner, repo)
    issues = list_open_issues(owner, repo, limit=3)
    commits = list_recent_commits(owner, repo, limit=3)
    return (
        f"I couldn't reach the configured LLM endpoint, so here is a lightweight summary for {owner}/{repo}:\n"
        f"- Stars: {repo_info.get('stars')} | Forks: {repo_info.get('forks')} | Language: {repo_info.get('language')}\n"
        f"- Recent commits: {', '.join(c.get('message', '') for c in commits[:2]) if commits else 'none'}\n"
        f"- Open issues: {len(issues)}"
    )


def run_agent(user_question: str, owner: str, repo: str) -> str:
    prompt = (
        f"You are a GitHub repository assistant. "
        f"User asks: {user_question}\n"
        f"Repository: {owner}/{repo}. "
        "Use the available tools when helpful. "
        "If you need repository details, call the appropriate tool. "
        "Answer in a concise natural-language summary."
    )

    try:
        completion_kwargs: Dict[str, Any] = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "tools": TOOLS,
        }
        if MODEL.startswith("ollama/"):
            completion_kwargs["api_base"] = API_BASE
        response = completion(**completion_kwargs)
    except Exception as exc:  # noqa: BLE001
        return _fallback_summary(user_question, owner, repo)

    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", None) or []

    if not tool_calls:
        return getattr(message, "content", "") or "I couldn't produce a response."

    tool_results: List[Dict[str, Any]] = []
    for tool_call in tool_calls:
        function = getattr(tool_call, "function", None)
        tool_name = None
        raw_arguments = None
        if isinstance(function, dict):
            tool_name = function.get("name")
            raw_arguments = function.get("arguments")
        else:
            tool_name = getattr(function, "name", None)
            raw_arguments = getattr(function, "arguments", None)
        if not tool_name:
            continue
        arguments = _safe_parse_arguments(raw_arguments)
        try:
            result = asyncio.run(_call_mcp_tool(tool_name, arguments))
            normalized_result = _normalize_tool_result(result)
            tool_results.append({"tool_name": tool_name, "result": normalized_result})
        except Exception as exc:  # noqa: BLE001
            tool_results.append({"tool_name": tool_name, "result": f"Tool error: {exc}"})

    follow_up_messages = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": "I used the available tools to inspect the repository."},
    ]
    for item in tool_results:
        follow_up_messages.append(
            {
                "role": "tool",
                "name": item["tool_name"],
                "content": _tool_result_to_text(item["result"]),
            }
        )

    try:
        final_kwargs: Dict[str, Any] = {
            "model": MODEL,
            "messages": follow_up_messages,
        }
        if MODEL.startswith("ollama/"):
            final_kwargs["api_base"] = API_BASE
        final_response = completion(**final_kwargs)
    except Exception as exc:  # noqa: BLE001
        return _fallback_summary(user_question, owner, repo)

    final_message = final_response.choices[0].message
    return getattr(final_message, "content", "") or "I couldn't produce a final summary."


if __name__ == "__main__":
    print(run_agent("What is happening in this repo lately?", "facebook", "react"))
