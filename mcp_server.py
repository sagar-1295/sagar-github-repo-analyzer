from mcp.server.fastmcp import FastMCP

from github_client import get_repo_info, list_open_issues, list_recent_commits

mcp = FastMCP("github-repo-analyzer")


@mcp.tool()
def get_repo_summary(owner: str, repo: str) -> dict:
    """Get repository metadata such as stars, forks, language, and last update time."""
    return get_repo_info(owner, repo)


@mcp.tool()
def get_recent_commits(owner: str, repo: str, limit: int = 5) -> list:
    """List recent commit messages, authors, and dates for a repository."""
    return list_recent_commits(owner, repo, limit=limit)


@mcp.tool()
def get_open_issues(owner: str, repo: str, limit: int = 5) -> list:
    """List open bug and issue tickets for a repository, excluding pull requests."""
    return list_open_issues(owner, repo, limit=limit)


if __name__ == "__main__":
    mcp.run()
