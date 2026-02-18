"""
LangGraph Agent Orchestration
Complete agent state machine with thought trace and tool execution
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import asyncio
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from app.tools import ToolRegistry
from app.models.agent import Agent
from app.models.credential import Credential
from app.services.encryption_service import encryption_service


# ===== AGENT STATE DEFINITION (TASK-239, 247) =====

class ThoughtTraceEntry(TypedDict):
    """Single entry in the thought trace"""
    timestamp: str
    step: str
    node: str
    content: str
    status: Literal["in_progress", "completed", "failed"]
    metadata: Optional[Dict[str, Any]]


class ToolCallEntry(TypedDict):
    """Tool call record"""
    timestamp: str
    tool_name: str
    arguments: Dict[str, Any]
    status: Literal["pending", "executing", "completed", "failed"]
    result: Optional[str]
    error: Optional[str]
    duration_ms: Optional[int]


class AgentState(TypedDict):
    """
    Complete agent state for LangGraph orchestration
    
    Tracks messages, thoughts, tool calls, and execution status
    """
    # Core conversation
    messages: List[BaseMessage]
    
    # User context
    user_id: str
    org_id: str
    agent_id: str
    
    # Agent configuration
    agent_config: Dict[str, Any]
    available_tools: List[BaseTool]
    
    # Thought process (TASK-247)
    thought_trace: List[ThoughtTraceEntry]
    current_step: str
    
    # Tool execution (TASK-249)
    tool_calls: List[ToolCallEntry]
    pending_approvals: List[Dict[str, Any]]
    
    # Execution state
    plan: Optional[List[str]]
    next_action: Optional[str]
    should_continue: bool
    iteration_count: int
    max_iterations: int
    
    # Final output
    final_response: Optional[str]
    error: Optional[str]


# ===== THOUGHT TRACE LOGGING (TASK-248, 250) =====

def log_thought(
    state: AgentState,
    step: str,
    node: str,
    content: str,
    status: Literal["in_progress", "completed", "failed"] = "in_progress",
    metadata: Optional[Dict[str, Any]] = None
) -> AgentState:
    """
    Log a thought/step in the agent's reasoning process
    
    Args:
        state: Current agent state
        step: Step identifier (e.g., "analyze_request", "plan_tools")
        node: Graph node name
        content: Thought content
        status: Execution status
        metadata: Additional metadata
    
    Returns:
        Updated state with new thought entry
    """
    thought_entry: ThoughtTraceEntry = {
        "timestamp": datetime.utcnow().isoformat(),
        "step": step,
        "node": node,
        "content": content,
        "status": status,
        "metadata": metadata or {}
    }
    
    state["thought_trace"].append(thought_entry)
    state["current_step"] = step
    
    return state


def log_tool_call(
    state: AgentState,
    tool_name: str,
    arguments: Dict[str, Any],
    status: Literal["pending", "executing", "completed", "failed"] = "pending",
    result: Optional[str] = None,
    error: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> AgentState:
    """
    Log a tool call in the agent's execution trace
    
    Args:
        state: Current agent state
        tool_name: Name of tool being called
        arguments: Tool arguments
        status: Execution status
        result: Tool result (if completed)
        error: Error message (if failed)
        duration_ms: Execution duration
    
    Returns:
        Updated state with tool call entry
    """
    tool_entry: ToolCallEntry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool_name": tool_name,
        "arguments": arguments,
        "status": status,
        "result": result,
        "error": error,
        "duration_ms": duration_ms
    }
    
    state["tool_calls"].append(tool_entry)
    
    return state


def format_thought_trace(thought_trace: List[ThoughtTraceEntry]) -> str:
    """
    Format thought trace for display (TASK-251)
    
    Args:
        thought_trace: List of thought entries
        
    Returns:
        Formatted string representation
    """
    if not thought_trace:
        return "No thoughts recorded."
    
    formatted_lines = ["🧠 Agent Thought Process:\n"]
    
    for i, entry in enumerate(thought_trace, 1):
        status_icon = {
            "in_progress": "⏳",
            "completed": "✅",
            "failed": "❌"
        }.get(entry["status"], "•")
        
        formatted_lines.append(
            f"{status_icon} Step {i} [{entry['node']}]: {entry['step']}\n"
            f"   {entry['content']}\n"
        )
    
    return "\n".join(formatted_lines)


# ===== TOOL EXECUTOR SERVICE (TASK-252 to 256) =====

class ToolExecutor:
    """
    Service for executing agent tools with validation and error handling
    """
    
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
    
    async def validate_tool_parameters(
        self,
        tool: BaseTool,
        arguments: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate tool parameters (TASK-253)
        
        Args:
            tool: Tool to validate
            arguments: Arguments to validate
            
        Returns:
            (is_valid, error_message)
        """
        try:
            # Check if tool has args_schema
            if hasattr(tool, 'args_schema') and tool.args_schema:
                # Pydantic validation
                tool.args_schema(**arguments)
            
            return True, None
        
        except Exception as e:
            return False, f"Parameter validation failed: {str(e)}"
    
    async def execute_tool(
        self,
        tool: BaseTool,
        arguments: Dict[str, Any],
        state: AgentState
    ) -> tuple[Optional[str], Optional[str], int]:
        """
        Execute tool with timeout and error handling (TASK-252, 254, 256)
        
        Args:
            tool: Tool to execute
            arguments: Tool arguments
            state: Current agent state
            
        Returns:
            (result, error, duration_ms)
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate parameters
            is_valid, validation_error = await self.validate_tool_parameters(tool, arguments)
            if not is_valid:
                return None, validation_error, 0
            
            # Execute with timeout (TASK-256)
            if hasattr(tool, '_arun'):
                # Async tool
                result = await asyncio.wait_for(
                    tool._arun(**arguments),
                    timeout=self.timeout_seconds
                )
            else:
                # Sync tool
                result = await asyncio.wait_for(
                    asyncio.to_thread(tool._run, **arguments),
                    timeout=self.timeout_seconds
                )
            
            # Format result (TASK-255)
            formatted_result = self.format_tool_result(result)
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return formatted_result, None, duration_ms
        
        except asyncio.TimeoutError:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return None, f"Tool execution timed out after {self.timeout_seconds}s", duration_ms
        
        except Exception as e:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return None, f"Tool execution failed: {str(e)}", duration_ms
    
    def format_tool_result(self, result: Any) -> str:
        """
        Format tool result for agent consumption (TASK-255)
        
        Args:
            result: Raw tool result
            
        Returns:
            Formatted string result
        """
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        elif isinstance(result, list):
            return "\n".join(str(item) for item in result)
        else:
            return str(result)


# ===== AGENT GRAPH NODES (TASK-240 to 244) =====

async def analyze_node(state: AgentState) -> AgentState:
    """
    Analyze node - Understand user request (TASK-240)
    
    Analyzes the user's message to understand intent and requirements
    """
    state = log_thought(
        state,
        step="analyze_request",
        node="analyze",
        content="Analyzing user request to understand intent and requirements...",
        status="in_progress"
    )
    
    try:
        # Get the latest user message
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            state["error"] = "No user message found"
            return state
        
        latest_message = user_messages[-1].content
        
        # Use LLM to analyze intent
        llm = await get_llm_for_agent(state)
        
        analysis_prompt = f"""Analyze this user request and identify:
1. Primary intent
2. Required information or actions
3. Complexity level (simple/moderate/complex)
4. Urgency indicators

User request: {latest_message}

Provide a brief analysis."""
        
        analysis_message = SystemMessage(content=analysis_prompt)
        response = await llm.ainvoke([analysis_message])
        
        analysis_content = response.content if hasattr(response, 'content') else str(response)
        
        state = log_thought(
            state,
            step="analyze_request",
            node="analyze",
            content=f"Request analysis: {analysis_content}",
            status="completed",
            metadata={"user_message": latest_message}
        )
        
        state["should_continue"] = True
        
    except Exception as e:
        state = log_thought(
            state,
            step="analyze_request",
            node="analyze",
            content=f"Analysis failed: {str(e)}",
            status="failed"
        )
        state["error"] = str(e)
        state["should_continue"] = False
    
    return state


async def plan_node(state: AgentState) -> AgentState:
    """
    Plan node - Decide which tools to use (TASK-241)
    
    Creates an execution plan based on available tools
    """
    state = log_thought(
        state,
        step="create_plan",
        node="plan",
        content="Creating execution plan and selecting appropriate tools...",
        status="in_progress"
    )
    
    try:
        # Get available tools
        tool_descriptions = [
            f"- {tool.name}: {tool.description}"
            for tool in state["available_tools"]
        ]
        
        if not tool_descriptions:
            # No tools available - go straight to synthesis
            state["plan"] = []
            state["next_action"] = "synthesize"
            state = log_thought(
                state,
                step="create_plan",
                node="plan",
                content="No tools available. Will generate direct response.",
                status="completed"
            )
            return state
        
        # Get user request
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        latest_message = user_messages[-1].content if user_messages else ""
        
        # Use LLM to create plan
        llm = await get_llm_for_agent(state)
        
        planning_prompt = f"""Given the user request and available tools, create a step-by-step execution plan.

User request: {latest_message}

Available tools:
{chr(10).join(tool_descriptions)}

Create a numbered plan. If no tools are needed, respond with "NO_TOOLS_NEEDED".
"""
        
        planning_message = SystemMessage(content=planning_prompt)
        response = await llm.ainvoke([planning_message])
        
        plan_content = response.content if hasattr(response, 'content') else str(response)
        
        if "NO_TOOLS_NEEDED" in plan_content:
            state["plan"] = []
            state["next_action"] = "synthesize"
        else:
            # Parse plan into steps
            plan_steps = [
                line.strip()
                for line in plan_content.split('\n')
                if line.strip() and any(line.strip().startswith(str(i)) for i in range(1, 10))
            ]
            state["plan"] = plan_steps
            state["next_action"] = "execute" if plan_steps else "synthesize"
        
        state = log_thought(
            state,
            step="create_plan",
            node="plan",
            content=f"Execution plan created:\n{plan_content}",
            status="completed",
            metadata={"plan_steps": state["plan"]}
        )
        
    except Exception as e:
        state = log_thought(
            state,
            step="create_plan",
            node="plan",
            content=f"Planning failed: {str(e)}",
            status="failed"
        )
        state["error"] = str(e)
        state["next_action"] = "synthesize"  # Fallback to synthesis
    
    return state


async def execute_node(state: AgentState) -> AgentState:
    """
    Execute node - Call tools based on plan (TASK-242)
    
    Executes planned tool calls
    """
    state = log_thought(
        state,
        step="execute_tools",
        node="execute",
        content="Executing tools according to plan...",
        status="in_progress"
    )
    
    try:
        executor = ToolExecutor()
        
        # Get user request for context
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        latest_message = user_messages[-1].content if user_messages else ""
        
        # Use LLM to determine which tools to call and with what arguments
        llm = await get_llm_for_agent(state)
        
        tool_descriptions = [
            f"{tool.name}: {tool.description}"
            for tool in state["available_tools"]
        ]
        
        execution_prompt = f"""Based on the plan, determine which tool(s) to call and with what arguments.

User request: {latest_message}
Plan: {state.get('plan', [])}

Available tools:
{chr(10).join(tool_descriptions)}

Respond with JSON in this format:
{{
    "tool_calls": [
        {{"tool_name": "tool_name", "arguments": {{"arg1": "value1"}}}}
    ]
}}

If no tools should be called, respond with {{"tool_calls": []}}
"""
        
        execution_message = SystemMessage(content=execution_prompt)
        response = await llm.ainvoke([execution_message])
        
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse tool calls from response
        try:
            # Extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                tool_calls_data = json.loads(response_content[json_start:json_end])
                tool_calls_list = tool_calls_data.get("tool_calls", [])
            else:
                tool_calls_list = []
        except:
            tool_calls_list = []
        
        # Execute each tool call
        for tool_call in tool_calls_list:
            tool_name = tool_call.get("tool_name")
            arguments = tool_call.get("arguments", {})
            
            # Find the tool
            tool = next((t for t in state["available_tools"] if t.name == tool_name), None)
            
            if not tool:
                state = log_tool_call(
                    state,
                    tool_name=tool_name,
                    arguments=arguments,
                    status="failed",
                    error=f"Tool '{tool_name}' not found"
                )
                continue
            
            # Log pending tool call
            state = log_tool_call(
                state,
                tool_name=tool_name,
                arguments=arguments,
                status="executing"
            )
            
            # Execute tool
            result, error, duration_ms = await executor.execute_tool(tool, arguments, state)
            
            # Update tool call status
            if state["tool_calls"]:
                state["tool_calls"][-1]["status"] = "completed" if not error else "failed"
                state["tool_calls"][-1]["result"] = result
                state["tool_calls"][-1]["error"] = error
                state["tool_calls"][-1]["duration_ms"] = duration_ms
            
            # Log the execution
            status_msg = f"✅ {tool_name} completed" if not error else f"❌ {tool_name} failed"
            state = log_thought(
                state,
                step=f"execute_tool_{tool_name}",
                node="execute",
                content=f"{status_msg}: {result or error}",
                status="completed" if not error else "failed",
                metadata={"tool": tool_name, "duration_ms": duration_ms}
            )
        
        state["next_action"] = "synthesize"
        
        state = log_thought(
            state,
            step="execute_tools",
            node="execute",
            content=f"Tool execution completed. {len(tool_calls_list)} tools executed.",
            status="completed"
        )
        
    except Exception as e:
        state = log_thought(
            state,
            step="execute_tools",
            node="execute",
            content=f"Execution failed: {str(e)}",
            status="failed"
        )
        state["next_action"] = "synthesize"  # Continue to synthesis even on error
    
    return state


async def synthesize_node(state: AgentState) -> AgentState:
    """
    Synthesize node - Generate final response (TASK-243)
    
    Combines tool results and generates coherent response
    """
    state = log_thought(
        state,
        step="synthesize_response",
        node="synthesize",
        content="Synthesizing final response from tool results...",
        status="in_progress"
    )
    
    try:
        # Gather context
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        latest_message = user_messages[-1].content if user_messages else ""
        
        # Gather tool results
        tool_results = []
        for tool_call in state["tool_calls"]:
            if tool_call["status"] == "completed" and tool_call["result"]:
                tool_results.append(
                    f"Tool: {tool_call['tool_name']}\nResult: {tool_call['result']}"
                )
        
        # Use LLM to synthesize response
        llm = await get_llm_for_agent(state)
        
        synthesis_prompt = f"""Generate a helpful response to the user's request.

User request: {latest_message}

Tool results:
{chr(10).join(tool_results) if tool_results else 'No tools were used.'}

Provide a clear, concise response that directly addresses the user's request.
"""
        
        synthesis_message = SystemMessage(content=synthesis_prompt)
        response = await llm.ainvoke([synthesis_message])
        
        final_response = response.content if hasattr(response, 'content') else str(response)
        
        state["final_response"] = final_response
        state["should_continue"] = False
        
        # Add AI message to conversation
        state["messages"].append(AIMessage(content=final_response))
        
        state = log_thought(
            state,
            step="synthesize_response",
            node="synthesize",
            content=f"Final response generated: {final_response[:100]}...",
            status="completed"
        )
        
    except Exception as e:
        state = log_thought(
            state,
            step="synthesize_response",
            node="synthesize",
            content=f"Synthesis failed: {str(e)}",
            status="failed"
        )
        state["error"] = str(e)
        state["final_response"] = "I apologize, but I encountered an error generating a response."
        state["should_continue"] = False
    
    return state


async def reflect_node(state: AgentState) -> AgentState:
    """
    Reflect node - Learn from execution (TASK-244)
    
    Analyzes the execution for improvements and learning
    """
    state = log_thought(
        state,
        step="reflect",
        node="reflect",
        content="Reflecting on execution for improvements...",
        status="in_progress"
    )
    
    try:
        # Analyze execution metrics
        total_tools = len(state["tool_calls"])
        successful_tools = sum(1 for tc in state["tool_calls"] if tc["status"] == "completed")
        failed_tools = total_tools - successful_tools
        
        total_duration = sum(
            tc.get("duration_ms", 0)
            for tc in state["tool_calls"]
        )
        
        reflection = f"""Execution Summary:
- Total steps: {len(state['thought_trace'])}
- Tools called: {total_tools}
- Successful: {successful_tools}
- Failed: {failed_tools}
- Total duration: {total_duration}ms
- Iterations: {state['iteration_count']}
"""
        
        state = log_thought(
            state,
            step="reflect",
            node="reflect",
            content=reflection,
            status="completed",
            metadata={
                "total_tools": total_tools,
                "successful_tools": successful_tools,
                "failed_tools": failed_tools,
                "total_duration_ms": total_duration
            }
        )
        
    except Exception as e:
        state = log_thought(
            state,
            step="reflect",
            node="reflect",
            content=f"Reflection failed: {str(e)}",
            status="failed"
        )
    
    return state


# ===== CONDITIONAL EDGES (TASK-245) =====

def should_continue(state: AgentState) -> str:
    """
    Determine next node based on state
    
    Controls the flow through the agent graph
    """
    # Check iteration limit
    if state["iteration_count"] >= state["max_iterations"]:
        return "end"
    
    # Check for errors
    if state.get("error"):
        return "synthesize"
    
    # Check next action
    next_action = state.get("next_action", "")
    
    if next_action == "execute":
        return "execute"
    elif next_action == "synthesize":
        return "synthesize"
    elif state["should_continue"]:
        return "plan"
    else:
        return "reflect"


def needs_approval(state: AgentState) -> str:
    """
    Check if action needs user approval (TASK-246)
    
    Approval gate for dangerous or sensitive actions
    """
    # Check for pending approvals
    if state.get("pending_approvals"):
        return "approval_gate"
    
    # Check for dangerous tool calls
    dangerous_tools = ["delete", "remove", "drop", "truncate"]
    
    for tool_call in state["tool_calls"]:
        if tool_call["status"] == "pending":
            tool_name_lower = tool_call["tool_name"].lower()
            if any(dangerous in tool_name_lower for dangerous in dangerous_tools):
                # Add to pending approvals
                state["pending_approvals"].append({
                    "tool_call": tool_call,
                    "reason": "Dangerous operation requires approval"
                })
                return "approval_gate"
    
    return "continue"


# ===== HELPER FUNCTIONS =====

async def get_llm_for_agent(state: AgentState) -> Any:
    """
    Get configured LLM for agent
    
    Args:
        state: Agent state with configuration
        
    Returns:
        Configured LLM instance
    """
    config = state["agent_config"]
    provider = config.get("llm_provider", "openai")
    model = config.get("llm_model", "gpt-4")
    api_key = config.get("llm_api_key", "")
    
    if provider == "openai":
        return ChatOpenAI(model=model, api_key=api_key, temperature=0.7)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, api_key=api_key, temperature=0.7)
    elif provider == "google":
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0.7)
    else:
        # Default to OpenAI
        return ChatOpenAI(model=model, api_key=api_key, temperature=0.7)


def create_agent_graph() -> StateGraph:
    """
    Create the complete agent orchestration graph (TASK-245)
    
    Returns:
        Configured StateGraph
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("reflect", reflect_node)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "analyze",
        should_continue,
        {
            "plan": "plan",
            "synthesize": "synthesize",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "plan",
        should_continue,
        {
            "execute": "execute",
            "synthesize": "synthesize",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "synthesize": "synthesize",
            "plan": "plan",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "synthesize",
        should_continue,
        {
            "reflect": "reflect",
            "end": END
        }
    )
    
    workflow.add_edge("reflect", END)
    
    return workflow


async def run_agent_graph(
    user_message: str,
    agent: Agent,
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> AgentState:
    """
    Run the complete agent graph
    
    Args:
        user_message: User's input message
        agent: Agent configuration
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        Final agent state with response
    """
    # Get available tools
    tools = await ToolRegistry.get_available_tools(db, user_id, org_id)
    
    # Get agent's LLM credentials
    agent_config = agent.config or {}
    
    # If agent has credential_id, load it
    if hasattr(agent, 'credential_id') and agent.credential_id:
        credential = db.query(Credential).filter(
            Credential.id == agent.credential_id,
            Credential.is_active == True
        ).first()
        
        if credential:
            api_key = encryption_service.decrypt(credential.encrypted_api_key)
            agent_config["llm_api_key"] = api_key
            agent_config["llm_provider"] = credential.credential_type
            agent_config["llm_model"] = credential.metadata.get("model", "gpt-4") if credential.metadata else "gpt-4"
    
    # Initialize state
    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": str(user_id),
        "org_id": str(org_id),
        "agent_id": str(agent.id),
        "agent_config": agent_config,
        "available_tools": tools,
        "thought_trace": [],
        "current_step": "initialize",
        "tool_calls": [],
        "pending_approvals": [],
        "plan": None,
        "next_action": None,
        "should_continue": True,
        "iteration_count": 0,
        "max_iterations": 10,
        "final_response": None,
        "error": None
    }
    
    # Create and compile graph
    graph = create_agent_graph()
    app = graph.compile()
    
    # Run graph
    final_state = await app.ainvoke(initial_state)
    
    return final_state
