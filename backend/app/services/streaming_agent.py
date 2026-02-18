"""
Streaming Agent Orchestration
LangGraph agent with SSE event streaming
"""

from typing import AsyncGenerator, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import asyncio

from app.models.agent import Agent
from app.services.agent_orchestration import (
    AgentState,
    create_agent_graph,
    get_llm_for_agent,
    log_thought,
    log_tool_call,
    ToolExecutor
)
from app.tools import ToolRegistry
from app.models.credential import Credential
from app.services.encryption_service import encryption_service
from langchain_core.messages import HumanMessage, AIMessage


async def stream_agent_execution(
    user_message: str,
    agent: Agent,
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream agent execution with real-time updates (TASK-263, 264, 265, 266)
    
    Args:
        user_message: User's input message
        agent: Agent configuration
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Yields:
        Event dictionaries for SSE formatting
    """
    # Send initial status
    yield {
        "type": "status",
        "data": {
            "status": "initializing",
            "message": "Starting agent..."
        }
    }
    
    # Get available tools
    tools = await ToolRegistry.get_available_tools(db, user_id, org_id)
    
    # Get agent's LLM credentials
    agent_config = agent.config or {}
    
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
    
    # Send status update
    yield {
        "type": "status",
        "data": {
            "status": "analyzing",
            "message": "Analyzing your request..."
        }
    }
    
    # Execute graph nodes with streaming
    state = initial_state
    
    # Analyze
    yield {
        "type": "thought",
        "data": {
            "step": "analyze_request",
            "node": "analyze",
            "content": "Analyzing user request to understand intent and requirements...",
            "status": "in_progress"
        }
    }
    
    # Import nodes
    from app.services.agent_orchestration import (
        analyze_node,
        plan_node,
        execute_node,
        synthesize_node,
        should_continue
    )
    
    # Execute analyze
    state = await analyze_node(state)
    
    # Stream thought trace updates
    if state["thought_trace"]:
        latest_thought = state["thought_trace"][-1]
        yield {
            "type": "thought",
            "data": latest_thought
        }
    
    if state.get("error"):
        yield {
            "type": "error",
            "data": {
                "message": state["error"],
                "code": "analysis_failed"
            }
        }
        return
    
    # Plan
    yield {
        "type": "status",
        "data": {
            "status": "planning",
            "message": "Creating execution plan..."
        }
    }
    
    state = await plan_node(state)
    
    # Stream planning thoughts
    if state["thought_trace"]:
        for thought in state["thought_trace"][-2:]:  # Last 2 thoughts
            yield {
                "type": "thought",
                "data": thought
            }
    
    # Execute tools if needed
    if state.get("next_action") == "execute" and state.get("plan"):
        yield {
            "type": "status",
            "data": {
                "status": "executing",
                "message": "Executing tools..."
            }
        }
        
        # Stream execution with tool calls
        state = await stream_execute_node(state)
        
        # Stream tool calls and results
        for tool_call in state["tool_calls"]:
            # Stream tool call initiation
            yield {
                "type": "tool_call",
                "data": {
                    "tool_name": tool_call["tool_name"],
                    "arguments": tool_call["arguments"],
                    "status": "executing",
                    "tool_id": tool_call.get("timestamp")
                }
            }
            
            # Stream tool result
            yield {
                "type": "tool_result",
                "data": {
                    "tool_name": tool_call["tool_name"],
                    "result": tool_call.get("result"),
                    "error": tool_call.get("error"),
                    "duration_ms": tool_call.get("duration_ms"),
                    "tool_id": tool_call.get("timestamp")
                }
            }
            
            # Small delay for better UX
            await asyncio.sleep(0.1)
    
    # Synthesize
    yield {
        "type": "status",
        "data": {
            "status": "synthesizing",
            "message": "Generating response..."
        }
    }
    
    state = await synthesize_node(state)
    
    # Stream synthesis thoughts
    if state["thought_trace"]:
        for thought in state["thought_trace"][-2:]:
            yield {
                "type": "thought",
                "data": thought
            }
    
    # Stream final response token by token (TASK-266)
    final_response = state.get("final_response", "")
    
    # Simulate token streaming (split by words)
    if final_response:
        words = final_response.split()
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {
                "type": "token",
                "data": {"token": token}
            }
            await asyncio.sleep(0.02)  # Small delay for streaming effect
    
    # Send completion event (TASK-267)
    yield {
        "type": "completion",
        "data": {
            "response": final_response,
            "metadata": {
                "thought_trace": state.get("thought_trace", []),
                "tool_calls": state.get("tool_calls", []),
                "iteration_count": state.get("iteration_count", 0)
            }
        }
    }


async def stream_execute_node(state: AgentState) -> AgentState:
    """
    Execute node with streaming support
    
    Similar to execute_node but designed for streaming
    """
    from app.services.agent_orchestration import get_llm_for_agent
    from langchain_core.messages import SystemMessage, HumanMessage
    import json
    from datetime import datetime
    
    executor = ToolExecutor()
    
    # Get user request for context
    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    latest_message = user_messages[-1].content if user_messages else ""
    
    # Use LLM to determine which tools to call
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
    
    return state
