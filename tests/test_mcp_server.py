import pytest
import asyncio
from unittest.mock import patch, MagicMock
from mcp_server import _convert_tools, list_tools, call_tool, VALID_NAMES, TOOLS
from tools import TOOL_REGISTRY

def test_convert_tools():
    tools, names = _convert_tools()
    assert len(tools) == len(TOOL_REGISTRY)
    assert len(names) == len(TOOL_REGISTRY)

    # Check if tools are correctly converted
    for defn in TOOL_REGISTRY:
        name = defn["name"]
        assert name in names
        tool_obj = next(t for t in tools if t.name == name)
        assert tool_obj.description == defn.get("description", "")
        assert tool_obj.inputSchema == defn.get("inputSchema", {"type": "object", "properties": {}})

def test_list_tools():
    result = asyncio.run(list_tools())
    assert result == TOOLS

def test_call_tool_success():
    tool_name = "get_data"
    arguments = {"station": "KNYC"}
    mock_result = "Mocked result"

    with patch("mcp_server.execute_tool_call", return_value=mock_result) as mock_execute:
        result = asyncio.run(call_tool(tool_name, arguments))

        mock_execute.assert_called_once_with(tool_name, arguments)
        assert len(result) == 1
        assert result[0].text == mock_result

def test_call_tool_unknown():
    with pytest.raises(ValueError, match="Unknown tool: invalid_tool"):
        asyncio.run(call_tool("invalid_tool", {}))
