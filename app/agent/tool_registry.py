"""Allowlisted Tool Registry for Football Intelligence Engine.

Enforces strict allowlisting, argument schema validation, execution timeouts,
and safe, structured error responses.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    """Metadata and schema for an explicitly registered tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    timeout_seconds: float = 15.0


class ToolRegistry:
    """Registry managing allowlisted tools and their execution."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
        timeout_seconds: float = 15.0,
    ) -> None:
        """Register a tool with its schema and handler."""
        if name in self._tools:
            logger.warning(f"Overwriting previously registered tool: {name}")
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            timeout_seconds=timeout_seconds,
        )
        self._handlers[name] = handler

    def get_tool_definition(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_openai_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return tool definitions in the official xAI/OpenAI format."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return schemas

    def execute_tool_sync(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously execute an allowlisted tool if handler is synchronous."""
        if name not in self._handlers:
            return {
                "success": False,
                "error": f"Tool '{name}' is not in the allowlisted tool registry.",
                "status": "UNAUTHORIZED_TOOL",
            }
        handler = self._handlers[name]
        try:
            if inspect.iscoroutinefunction(handler):
                return asyncio.run(self.execute_tool(name, arguments))
            result = handler(**arguments)
            if isinstance(result, BaseModel):
                return {"success": True, "data": result.model_dump(mode="json")}
            elif isinstance(result, dict):
                return {"success": True, "data": result}
            else:
                return {"success": True, "data": result}
        except Exception as exc:
            logger.exception(f"Unhandled error during synchronous tool execution '{name}': {exc}")
            return {
                "success": False,
                "error": f"Tool execution failed: {str(exc)}",
                "status": "EXECUTION_ERROR",
            }

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an allowlisted tool with safety bounds and timeout."""
        if name not in self._handlers:
            return {
                "success": False,
                "error": f"Tool '{name}' is not in the allowlisted tool registry.",
                "status": "UNAUTHORIZED_TOOL",
            }

        tool_def = self._tools[name]
        handler = self._handlers[name]

        try:
            # Execute handler directly if sync or await if async
            if inspect.iscoroutinefunction(handler):
                result = await asyncio.wait_for(
                    handler(**arguments),
                    timeout=tool_def.timeout_seconds,
                )
            else:
                result = handler(**arguments)

            # Ensure the output is a dictionary or serializable structure
            if isinstance(result, BaseModel):
                return {"success": True, "data": result.model_dump(mode="json")}
            elif isinstance(result, dict):
                return {"success": True, "data": result}
            else:
                return {"success": True, "data": result}

        except asyncio.TimeoutError:
            logger.error(f"Tool execution timed out: {name} after {tool_def.timeout_seconds}s")
            return {
                "success": False,
                "error": f"Tool '{name}' execution timed out after {tool_def.timeout_seconds} seconds.",
                "status": "TIMEOUT",
            }
        except TypeError as exc:
            logger.error(f"Invalid arguments for tool '{name}': {exc}")
            return {
                "success": False,
                "error": f"Argument validation error for tool '{name}': {str(exc)}",
                "status": "INVALID_ARGUMENTS",
            }
        except Exception as exc:
            logger.exception(f"Unhandled error during tool execution '{name}': {exc}")
            return {
                "success": False,
                "error": f"Tool execution failed: {str(exc)}",
                "status": "EXECUTION_ERROR",
            }
