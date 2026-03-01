"""
Tool: web_search

Searches the web using the Tavily API, which is purpose-built for AI agents.
Requires a TAVILY_API_KEY in the environment.
"""

import json
import urllib.request
import urllib.error

from .base import BaseTool

TAVILY_API_URL = "https://api.tavily.com/search"


class WebSearchTool(BaseTool):

    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web for current information. Returns relevant "
            "snippets and URLs. Use when the user asks about recent events, "
            "documentation, or anything requiring up-to-date knowledge."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (1–10). Default: 5.",
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs) -> str:
        query: str = kwargs["query"]
        max_results: int = kwargs.get("max_results", 5)

        if not self._api_key:
            return "Error: TAVILY_API_KEY is not configured. Set it in your .env file."

        payload = json.dumps({
            "api_key": self._api_key,
            "query": query,
            "max_results": min(max_results, 10),
            "include_answer": True,
        }).encode("utf-8")

        req = urllib.request.Request(
            TAVILY_API_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return f"Error: Tavily API returned HTTP {exc.code}."
        except urllib.error.URLError as exc:
            return f"Error: could not reach Tavily API — {exc.reason}"
        except Exception as exc:
            return f"Error performing web search: {exc}"

        lines = []
        if data.get("answer"):
            lines.append(f"Summary: {data['answer']}\n")

        for i, result in enumerate(data.get("results", []), 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            snippet = result.get("content", "")[:300]
            lines.append(f"{i}. {title}\n   {url}\n   {snippet}")

        return "\n\n".join(lines) if lines else "No results found."
