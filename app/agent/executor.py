"""Agent Tool Executor and Reasoning Loop.

Enforces bounded reasoning rounds, anti-loop detection, multi-turn tool execution,
and structured execution traces.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.agent.groq_client import BaseLLMClient, GroqClient, GroqAPIError
from app.agent.tool_registry import ToolRegistry
from app.agent.web_research import WebEvidenceBuilder, WebResearchPolicy
from app.config.settings import settings
from app.schemas.models import WebSourceEvidence

logger = logging.getLogger(__name__)


class ToolExecutionRecord(BaseModel):
    """Log of an executed tool call."""
    round_index: int
    tool_call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    success: bool


class ExecutionResult(BaseModel):
    """Complete trace and result of agent reasoning and tool loop."""
    final_response: str
    tool_records: List[ToolExecutionRecord] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    web_sources: List[WebSourceEvidence] = Field(default_factory=list)
    web_search_records: List[Dict[str, Any]] = Field(default_factory=list)
    rounds_executed: int
    terminated_by_limit: bool = False
    circular_loop_detected: bool = False


class AgentExecutor:
    """Manages the interactive multi-turn tool-calling loop between Groq and tools."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_rounds: Optional[int] = None,
        enable_web_search: bool = True,
        # Backwards compatibility alias
        grok_client: Optional[BaseLLMClient] = None,
    ):
        self.llm_client = llm_client or grok_client or GroqClient()
        self.grok_client = self.llm_client  # Compatibility alias
        self.tool_registry = tool_registry or ToolRegistry()
        self.max_rounds = max_rounds or getattr(settings, "groq_max_tool_rounds", 8)
        self.enable_web_search = enable_web_search

    def run_sync(
        self,
        system_prompt: str,
        user_message: str,
        context_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> ExecutionResult:
        """Synchronous wrapper for run."""
        import asyncio
        return asyncio.run(self.run(system_prompt, user_message, context_messages))

    async def run(
        self,
        system_prompt: str,
        user_message: str,
        context_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> ExecutionResult:
        """Run the reasoning-action loop until completion or safety boundary."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]
        if context_messages:
            messages.extend(context_messages)
        messages.append({"role": "user", "content": user_message})

        # Check selective web research policy
        should_search, search_reason, _ = WebResearchPolicy.should_research(user_message)
        use_web_search = self.enable_web_search and should_search

        tool_schemas = self.tool_registry.get_openai_tool_schemas()
        tool_records: List[ToolExecutionRecord] = []
        accumulated_citations: List[str] = []
        accumulated_web_search_records: List[Dict[str, Any]] = []
        seen_calls: Dict[str, int] = {}  # signature -> count for anti-looping

        round_idx = 0
        final_text = ""
        terminated_by_limit = False
        circular_loop_detected = False

        while round_idx < self.max_rounds:
            round_idx += 1
            logger.info(f"Agent reasoning round {round_idx}/{self.max_rounds}")

            try:
                response = await self.llm_client.generate_response(
                    messages=messages,
                    tools=tool_schemas if tool_schemas else None,
                    enable_web_search=use_web_search,
                )
            except GroqAPIError as exc:
                logger.error(f"Groq API error during round {round_idx}: {exc}")
                return ExecutionResult(
                    final_response=f"Error executing agent workflow: {str(exc)}",
                    tool_records=tool_records,
                    citations=accumulated_citations,
                    rounds_executed=round_idx,
                    terminated_by_limit=True,
                )

            # Collect citations and server-side search activities from Groq response
            round_citations = response.get("citations") or []
            for c in round_citations:
                if c not in accumulated_citations:
                    accumulated_citations.append(c)

            round_ws = response.get("executed_tools") or response.get("web_search_calls") or []
            for ws in round_ws:
                accumulated_web_search_records.append(ws)

            tool_calls = response.get("tool_calls")
            assistant_content = response.get("content")

            if not tool_calls:
                # Groq completed reasoning and provided final synthesis
                final_text = assistant_content or "Analysis completed with no additional comments."
                break

            # Append the assistant message with its tool calls
            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": tool_calls,
            }
            messages.append(assistant_msg)

            # Process each requested tool call
            for call in tool_calls:
                call_id = call.get("id", f"call_{round_idx}")
                function_info = call.get("function", {})
                tool_name = function_info.get("name", "")
                raw_args = function_info.get("arguments", "{}")

                try:
                    parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    parsed_args = {}

                # Anti-loop check
                call_signature = f"{tool_name}:{json.dumps(parsed_args, sort_keys=True)}"
                seen_calls[call_signature] = seen_calls.get(call_signature, 0) + 1
                if seen_calls[call_signature] > 2:
                    logger.warning(f"Circular tool call detected for {tool_name}. Halting repeat execution.")
                    circular_loop_detected = True
                    result_data = {
                        "success": False,
                        "error": "Repeated identical tool call halted to prevent infinite loop.",
                        "status": "CIRCULAR_CALL_DETECTED",
                    }
                else:
                    # Execute tool through allowlisted registry
                    result_data = await self.tool_registry.execute_tool(tool_name, parsed_args)

                tool_records.append(ToolExecutionRecord(
                    round_index=round_idx,
                    tool_call_id=call_id,
                    tool_name=tool_name,
                    arguments=parsed_args,
                    result=result_data,
                    success=result_data.get("success", False),
                ))

                # Feed result back to conversation context
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(result_data),
                })

            if circular_loop_detected:
                final_text = (
                    "Execution halted early due to repeated circular tool calls. "
                    "Partial results preserved."
                )
                break
        else:
            terminated_by_limit = True
            final_text = (
                f"Agent reached maximum execution rounds ({self.max_rounds}). "
                "Returning preliminary findings."
            )

        web_sources = [
            WebEvidenceBuilder.create_evidence(
                url=c,
                claim_supported="Contextual information examined during Groq web research",
                inline_id=f"[{idx + 1}]",
            )
            for idx, c in enumerate(accumulated_citations)
        ]

        return ExecutionResult(
            final_response=final_text,
            tool_records=tool_records,
            citations=accumulated_citations,
            web_sources=web_sources,
            web_search_records=accumulated_web_search_records,
            rounds_executed=round_idx,
            terminated_by_limit=terminated_by_limit,
            circular_loop_detected=circular_loop_detected,
        )
