#!/usr/bin/env python3
"""Read-only MCP server for your personal assistant API.

Tools exposed:
  get_tasks       — pending tasks
  get_events      — upcoming events
  get_inbox       — inbox items with filters
  search_items    — semantic search

Requires env vars:
  PA_API_URL      — https://your-assistant.example.com
  PA_API_TOKEN    — long-lived service token (generate via /api/v1/auth/service-token)
"""
import asyncio
import json
import os

import httpx
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

API_URL = os.environ.get("PA_API_URL", "https://your-assistant.example.com")
API_TOKEN = os.environ.get("PA_API_TOKEN", "")

server = Server("personal-assistant")


def _headers() -> dict:
    return {"Authorization": f"Bearer {API_TOKEN}"}


async def _get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(base_url=API_URL, headers=_headers(), timeout=15) as client:
        r = await client.get(path, params=params or {})
        r.raise_for_status()
        return r.json()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_tasks",
            description="Get Jonah's pending tasks from his personal assistant. Returns title, due_date, tags, notes, status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20, "description": "Max tasks to return"},
                    "include_snoozed": {"type": "boolean", "default": False},
                },
            },
        ),
        types.Tool(
            name="get_events",
            description="Get Jonah's upcoming events from his personal assistant.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "include_archived": {"type": "boolean", "default": False},
                },
            },
        ),
        types.Tool(
            name="get_inbox",
            description="Get items from Jonah's inbox with optional type and status filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_type": {
                        "type": "string",
                        "enum": ["task", "event", "note", "receipt", "contact", "shopping", "link"],
                        "description": "Filter by item type",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "completed", "archived", "triaged", "snoozed"],
                        "description": "Filter by status (default: all)",
                    },
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        types.Tool(
            name="search_items",
            description="Semantically search Jonah's personal assistant inbox using natural language.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "item_type": {"type": "string", "description": "Optionally filter by type"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "get_tasks":
            statuses = ["pending"]
            if arguments.get("include_snoozed"):
                statuses.append("snoozed")
            results = []
            for status in statuses:
                data = await _get("/api/v1/inbox/", {"type": "task", "status": status, "limit": arguments.get("limit", 20)})
                results.extend(data.get("items", []))
            return [types.TextContent(type="text", text=json.dumps({"items": results, "total": len(results)}, indent=2, default=str))]

        elif name == "get_events":
            params = {
                "type": "event",
                "status": "pending",
                "limit": arguments.get("limit", 10),
                "include_archived": arguments.get("include_archived", False),
            }
            data = await _get("/api/v1/inbox/", params)
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "get_inbox":
            params = {
                "limit": arguments.get("limit", 20),
                "offset": arguments.get("offset", 0),
            }
            if arguments.get("item_type"):
                params["type"] = arguments["item_type"]
            if arguments.get("status"):
                params["status"] = arguments["status"]
            data = await _get("/api/v1/inbox/", params)
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "search_items":
            params = {"q": arguments["query"], "limit": arguments.get("limit", 10)}
            if arguments.get("item_type"):
                params["type"] = arguments["item_type"]
            data = await _get("/api/v1/inbox/search/memory", params)
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.HTTPStatusError as e:
        return [types.TextContent(type="text", text=f"API error {e.response.status_code}: {e.response.text}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
