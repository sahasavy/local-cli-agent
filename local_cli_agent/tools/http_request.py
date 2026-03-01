"""
Tool: http_request

Makes HTTP GET or POST requests and returns the response.
"""

import json
import urllib.request
import urllib.error

from .base import BaseTool

TIMEOUT_SECONDS = 15
MAX_RESPONSE_CHARS = 5000


class HttpRequestTool(BaseTool):

    @property
    def name(self) -> str:
        return "http_request"

    @property
    def description(self) -> str:
        return (
            "Make an HTTP GET or POST request to a URL and return the response. "
            "Useful for calling REST APIs, checking endpoints, or fetching web content."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to request.",
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST"],
                    "description": "HTTP method. Default: GET.",
                },
                "headers": {
                    "type": "object",
                    "description": "Optional HTTP headers as key-value pairs.",
                },
                "body": {
                    "type": "string",
                    "description": "Request body for POST requests (typically a JSON string).",
                },
            },
            "required": ["url"],
        }

    def execute(self, **kwargs) -> str:
        url: str = kwargs["url"]
        method: str = kwargs.get("method", "GET").upper()
        headers: dict = kwargs.get("headers", {})
        body: str | None = kwargs.get("body")

        if not url.startswith(("http://", "https://")):
            return "Error: URL must start with http:// or https://"

        data = body.encode("utf-8") if body else None
        if data and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                status = resp.status
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")[:1000]
            return f"HTTP {exc.code} {exc.reason}\n\n{error_body}"
        except urllib.error.URLError as exc:
            return f"Error: could not connect — {exc.reason}"
        except Exception as exc:
            return f"Error: {exc}"

        truncated = ""
        if len(raw) > MAX_RESPONSE_CHARS:
            raw = raw[:MAX_RESPONSE_CHARS]
            truncated = f"\n\n[... truncated to {MAX_RESPONSE_CHARS} chars]"

        # Pretty-print JSON responses for readability
        if "json" in content_type:
            try:
                parsed = json.loads(raw[:MAX_RESPONSE_CHARS])
                raw = json.dumps(parsed, indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, ValueError):
                pass

        return f"HTTP {status} | {content_type}\n\n{raw}{truncated}"
