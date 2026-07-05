import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession


async def main() -> None:
    server_params = StdioServerParameters(
        command=r"D:\Sagar workspace\GenAI\sagar-github-repo-analyzer\.venv\Scripts\python.exe",
        args=["mcp_server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tool-count", len(tools.tools))
            for tool in tools.tools:
                print(tool.name)


if __name__ == "__main__":
    asyncio.run(main())
