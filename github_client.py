import os
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_API_BASE = "https://api.github.com"


def _headers() -> Dict[str, str]:
    headers: Dict[str, str] = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get_json(path: str, params: Dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{GITHUB_API_BASE}{path}", headers=_headers(), params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def get_repo_info(owner: str, repo: str) -> Dict[str, Any]:
    data = _get_json(f"/repos/{owner}/{repo}")
    return {
        "name": data.get("name"),
        "description": data.get("description"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "language": data.get("language"),
        "last_updated": data.get("updated_at"),
    }


def list_recent_commits(owner: str, repo: str, limit: int = 5) -> List[Dict[str, Any]]:
    data = _get_json(f"/repos/{owner}/{repo}/commits", params={"per_page": limit})
    commits: List[Dict[str, Any]] = []
    for item in data:
        author = item.get("commit", {}).get("author", {})
        commits.append(
            {
                "message": item.get("commit", {}).get("message"),
                "author": author.get("name"),
                "date": author.get("date"),
            }
        )
    return commits


def list_open_issues(owner: str, repo: str, limit: int = 5) -> List[Dict[str, Any]]:
    data = _get_json(f"/repos/{owner}/{repo}/issues", params={"state": "open", "per_page": limit})
    issues: List[Dict[str, Any]] = []
    for item in data:
        if item.get("pull_request"):
            continue
        issues.append(
            {
                "title": item.get("title"),
                "number": item.get("number"),
                "created_at": item.get("created_at"),
            }
        )
    return issues


if __name__ == "__main__":
    owner = "facebook"
    repo = "react"
    print("Repo info:")
    print(get_repo_info(owner, repo))
    print("\nRecent commits:")
    print(list_recent_commits(owner, repo, limit=3))
    print("\nOpen issues:")
    print(list_open_issues(owner, repo, limit=3))
