"""
Base Agent class using LangGraph.

Provides foundational agent capabilities including:
- LLM integration
- MCP tool calling
- State management
- Conversation handling
"""

from typing import List, Dict, Any, Optional, TypedDict
from dataclasses import dataclass
import structlog
from langgraph.graph import StateGraph, END
import os
import sys

# Add project root to path for logging_config
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from llm_abstraction import (
    LLMProvider,
    Message,
    MessageRole,
    ToolDefinition,
    ToolCall,
    LLMResponse
)
from mcp_client import MCPClient, MCPTool, MCPError

# Import and configure logging
try:
    from logging_config import configure_logging
    configure_logging(log_level="INFO", log_to_file=True)
except ImportError:
    pass  # Logging config not available

logger = structlog.get_logger("agents")


class AgentState(TypedDict):
    """State for the agent graph."""
    messages: List[Message]
    next_action: str
    tool_results: Dict[str, Any]
    iteration: int
    max_iterations: int
    error: Optional[str]


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    role: str
    system_prompt: str
    max_iterations: int = 10
    temperature: float = 0.7


class BaseAgent:
    """
    Base agent class using LangGraph for workflow orchestration.

    This class provides:
    - Integration with LLM providers
    - MCP tool calling capabilities
    - Conversation state management
    - Iterative reasoning loop

    Specialized agents should inherit from this class and:
    - Define their system prompt
    - Optionally override methods for custom behavior
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_provider: LLMProvider,
        mcp_client: MCPClient
    ):
        """
        Initialize the base agent.

        Args:
            config: Agent configuration
            llm_provider: LLM provider for generation
            mcp_client: MCP client for tool calls
        """
        self.config = config
        self.llm_provider = llm_provider
        self.mcp_client = mcp_client

        # Build the agent graph
        self.graph = self._build_graph()

        logger.info(
            "agent_initialized",
            agent_name=config.name,
            role=config.role,
            provider=llm_provider.get_provider_name()
        )

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Compiled state graph
        """
        # Create graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("think", self._think_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("observe", self._observe_node)

        # Set entry point
        workflow.set_entry_point("think")

        # Add edges
        workflow.add_conditional_edges(
            "think",
            self._should_continue,
            {
                "act": "act",
                "end": END
            }
        )
        workflow.add_edge("act", "observe")
        workflow.add_edge("observe", "think")

        # Compile
        return workflow.compile()

    async def _think_node(self, state: AgentState) -> AgentState:
        """
        Thinking node: Generate next action using LLM.

        Args:
            state: Current agent state

        Returns:
            Updated state
        """
        logger.info(
            "agent_thinking",
            agent=self.config.name,
            iteration=state["iteration"]
        )

        try:
            # Get available tools
            mcp_tools = await self.mcp_client.get_tools()
            tools = self._convert_mcp_tools_to_llm_format(mcp_tools)

            # Call LLM
            response = await self.llm_provider.complete(
                messages=state["messages"],
                tools=tools,
                system=self.config.system_prompt
            )

            # Add assistant message to history
            assistant_msg = Message(
                role=MessageRole.ASSISTANT,
                content=response.content
            )
            state["messages"].append(assistant_msg)

            # Check if there are tool calls
            if response.tool_calls and len(response.tool_calls) > 0:
                state["next_action"] = "act"
                # Store tool calls in state for the act node
                state["tool_results"] = {
                    "pending_calls": response.tool_calls
                }
            else:
                # No more actions, we're done
                state["next_action"] = "end"

            logger.info(
                "agent_thought",
                agent=self.config.name,
                next_action=state["next_action"],
                tool_calls=len(response.tool_calls) if response.tool_calls else 0
            )

        except Exception as e:
            logger.error(
                "agent_think_error",
                agent=self.config.name,
                error=str(e)
            )
            state["error"] = str(e)
            state["next_action"] = "end"

        return state

    async def _act_node(self, state: AgentState) -> AgentState:
        """
        Acting node: Execute tool calls.

        Args:
            state: Current agent state

        Returns:
            Updated state
        """
        logger.info("agent_acting", agent=self.config.name)

        pending_calls = state["tool_results"].get("pending_calls", [])
        results = []

        for tool_call in pending_calls:
            try:
                logger.info(
                    "agent_calling_tool",
                    agent=self.config.name,
                    tool=tool_call.name
                )

                # Call the MCP tool
                result = await self.mcp_client.call_tool(
                    tool_name=tool_call.name,
                    parameters=tool_call.arguments
                )

                results.append({
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_call.name,
                    "result": result,
                    "success": True
                })

                logger.info(
                    "agent_tool_success",
                    agent=self.config.name,
                    tool=tool_call.name
                )

            except MCPError as e:
                logger.error(
                    "agent_tool_error",
                    agent=self.config.name,
                    tool=tool_call.name,
                    error=str(e)
                )

                results.append({
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_call.name,
                    "result": {"error": str(e)},
                    "success": False
                })

        # Store results for observe node
        state["tool_results"] = {"results": results}

        return state

    async def _observe_node(self, state: AgentState) -> AgentState:
        """
        Observation node: Process tool results.

        Args:
            state: Current agent state

        Returns:
            Updated state
        """
        logger.info("agent_observing", agent=self.config.name)

        results = state["tool_results"].get("results", [])

        # Add tool results as messages
        for result in results:
            # Format result as a message
            result_content = self._format_tool_result(result)

            tool_msg = Message(
                role=MessageRole.ASSISTANT,  # Tool results go as assistant messages
                content=result_content
            )
            state["messages"].append(tool_msg)

        # Increment iteration counter
        state["iteration"] += 1

        # Clear tool results
        state["tool_results"] = {}

        return state

    def _should_continue(self, state: AgentState) -> str:
        """
        Decide whether to continue or end.

        Args:
            state: Current agent state

        Returns:
            Next node name
        """
        # Check for errors
        if state.get("error"):
            return "end"

        # Check iteration limit
        if state["iteration"] >= state["max_iterations"]:
            logger.warning(
                "agent_max_iterations",
                agent=self.config.name,
                iterations=state["iteration"]
            )
            return "end"

        # Check next action
        return state.get("next_action", "end")

    async def run(self, user_message: str) -> str:
        """
        Run the agent with a user message.

        Args:
            user_message: User input

        Returns:
            Agent's final response
        """
        logger.info(
            "agent_run_start",
            agent=self.config.name,
            message_length=len(user_message)
        )

        # Initialize state
        initial_state: AgentState = {
            "messages": [Message(role=MessageRole.USER, content=user_message)],
            "next_action": "",  # Will be set by think node
            "tool_results": {},
            "iteration": 0,
            "max_iterations": self.config.max_iterations,
            "error": None
        }

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        # Extract final response
        messages = final_state["messages"]
        assistant_messages = [
            msg for msg in messages
            if msg.role == MessageRole.ASSISTANT
        ]

        if assistant_messages:
            final_response = assistant_messages[-1].content
        else:
            final_response = "I encountered an error and couldn't complete the task."

        logger.info(
            "agent_run_complete",
            agent=self.config.name,
            iterations=final_state["iteration"],
            error=final_state.get("error")
        )

        return final_response

    def _convert_mcp_tools_to_llm_format(
        self,
        mcp_tools: List[MCPTool]
    ) -> List[ToolDefinition]:
        """
        Convert MCP tools to LLM provider format.

        Args:
            mcp_tools: MCP tool definitions

        Returns:
            LLM tool definitions
        """
        return [
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters=tool.input_schema
            )
            for tool in mcp_tools
        ]

    def _format_tool_result(self, result: Dict[str, Any]) -> str:
        """
        Format a tool result as a string.

        Args:
            result: Tool result dictionary

        Returns:
            Formatted string
        """
        import json

        tool_name = result.get("tool_name", "unknown")
        success = result.get("success", False)
        result_data = result.get("result", {})

        if success:
            return f"Tool '{tool_name}' result:\n{json.dumps(result_data, indent=2)}"
        else:
            error_msg = result_data.get("error", "Unknown error")
            return f"Tool '{tool_name}' failed: {error_msg}"
