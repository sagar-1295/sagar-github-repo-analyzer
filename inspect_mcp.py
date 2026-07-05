import asyncio
import json
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
from agent import _json_safe


async def main() -> None:
    server_params = StdioServerParameters(
        command=r"D:\Sagar workspace\GenAI\sagar-github-repo-analyzer\.venv\Scripts\python.exe",
        args=["mcp_server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_repo_summary", {"owner": "facebook", "repo": "react"})
            print(type(result))
            print(result)
            print("content type", type(result.content))
            print("content repr", repr(result.content))
            print("safe", _json_safe(result.content))
            print("json", json.dumps(_json_safe(result.content)))


if __name__ == "__main__":
    asyncio.run(main())
