"""MCP server for acis2llm — exposes weather/climate tools to MCP clients."""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from execution import execute_tool_call
from tools import TOOL_REGISTRY


def _convert_tools():
    """Convert registry tool definitions to MCP Tool objects.

    Returns:
        Tuple of (list of Tool objects, set of valid tool names).
    """
    tools = []
    names = set()
    for defn in TOOL_REGISTRY:
        name = defn["name"]
        tools.append(
            Tool(
                name=name,
                description=defn.get("description", ""),
                inputSchema=defn.get("inputSchema", {"type": "object", "properties": {}}),
            )
        )
        names.add(name)
    return tools, names


server = Server("acis2llm")
TOOLS, VALID_NAMES = _convert_tools()


@server.list_tools()
async def list_tools():
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name not in VALID_NAMES:
        raise ValueError(f"Unknown tool: {name}")

    result = await asyncio.to_thread(execute_tool_call, name, arguments)

    return [TextContent(type="text", text=result)]


async def _run():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
