import sys
from unittest.mock import MagicMock

class MockTool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

class MockTextContent:
    def __init__(self, type, text):
        self.type = type
        self.text = text

class MockServer:
    def __init__(self, name):
        self.name = name
    def list_tools(self):
        def decorator(func):
            self._list_tools_func = func
            return func
        return decorator
    def call_tool(self):
        def decorator(func):
            self._call_tool_func = func
            return func
        return decorator
    def create_initialization_options(self):
        return MagicMock()
    async def run(self, *args, **kwargs):
        pass

mcp = MagicMock()
mcp.server = MagicMock()
mcp.server.stdio = MagicMock()
mcp.server.Server = MockServer
mcp.types = MagicMock()
mcp.types.Tool = MockTool
mcp.types.TextContent = MockTextContent

sys.modules["mcp"] = mcp
sys.modules["mcp.server"] = mcp.server
sys.modules["mcp.server.stdio"] = mcp.server.stdio
sys.modules["mcp.types"] = mcp.types
sys.modules["pandas"] = MagicMock()
sys.modules["xmacis2py"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["numpy"] = MagicMock()
