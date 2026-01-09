"""
Agent Orchestration Service using LangGraph
Handles the agent's thinking process and tool execution
"""
from typing import List, Dict, Any, AsyncGenerator
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel
import json
from uuid import UUID, uuid4

class AgentState(BaseModel):
    """State maintained throughout agent execution."""
    messages: List[Dict[str, str]] = []
    thought_trace: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    final_answer: str = ""
    pending_approval: bool = False
    conversation_id: UUID = None

class AgentOrchestrator:
    """Orchestrates agent execution using LangGraph."""
    
    def __init__(self, agent_config: Dict[str, Any], llm_client, mcp_registry):
        self.agent_config = agent_config
        self.llm_client = llm_client
        self.mcp_registry = mcp_registry
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("analyze", self._analyze_node)
        graph.add_node("plan", self._plan_node)
        graph.add_node("execute_tools", self._execute_tools_node)
        graph.add_node("synthesize", self._synthesize_node)
        graph.add_node("wait_approval", self._wait_approval_node)
        
        # Add edges
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", "plan")
        graph.add_conditional_edges(
            "plan",
            self._should_use_tools,
            {
                "execute": "execute_tools",
                "synthesize": "synthesize"
            }
        )
        graph.add_conditional_edges(
            "execute_tools",
            self._needs_approval,
            {
                "approve": "wait_approval",
                "continue": "synthesize"
            }
        )
        graph.add_edge("wait_approval", "synthesize")
        graph.add_edge("synthesize", "END")
        
        return graph.compile()
    
    async def _analyze_node(self, state: AgentState) -> AgentState:
        """Analyze the user's request."""
        state.thought_trace.append("Analyzing request...")
        
        # Get available tools
        all_tools = await self.mcp_registry.get_all_tools()
        tool_descriptions = []
        for server_name, tools in all_tools.items():
            for tool in tools:
                tool_descriptions.append(f"{tool.name}: {tool.description}")
        
        state.thought_trace.append(f"Available tools: {len(tool_descriptions)}")
        return state
    
    async def _plan_node(self, state: AgentState) -> AgentState:
        """Create an execution plan."""
        state.thought_trace.append("Creating execution plan...")
        
        # Use LLM to determine which tools to use
        # This is a simplified version - in production, use proper LLM calls
        user_message = state.messages[-1]["content"] if state.messages else ""
        
        # For demo purposes, we'll add a simple planning logic
        state.thought_trace.append(f"Plan: Process request '{user_message}'")
        
        return state
    
    async def _execute_tools_node(self, state: AgentState) -> AgentState:
        """Execute necessary tools."""
        state.thought_trace.append("Executing tools...")
        
        # Tool execution logic would go here
        # This would interact with MCP clients to call tools
        
        return state
    
    async def _synthesize_node(self, state: AgentState) -> AgentState:
        """Synthesize final answer."""
        state.thought_trace.append("Generating response...")
        
        # Generate final response using LLM
        state.final_answer = "Response generated based on analysis"
        
        return state
    
    async def _wait_approval_node(self, state: AgentState) -> AgentState:
        """Wait for human approval."""
        state.thought_trace.append("Waiting for approval...")
        state.pending_approval = True
        return state
    
    def _should_use_tools(self, state: AgentState) -> str:
        """Determine if tools should be executed."""
        # Logic to determine if tools are needed
        return "synthesize"  # Simplified for now
    
    def _needs_approval(self, state: AgentState) -> str:
        """Determine if approval is needed."""
        # Check if any tool calls are "write" operations
        return "continue"  # Simplified for now
    
    async def run(self, message: str, conversation_id: UUID = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the agent and stream results."""
        if not conversation_id:
            conversation_id = uuid4()
        
        initial_state = AgentState(
            messages=[{"role": "user", "content": message}],
            conversation_id=conversation_id
        )
        
        # Yield initial status
        yield {
            "type": "status",
            "content": "Starting agent...",
            "conversation_id": str(conversation_id)
        }
        
        # Execute graph
        try:
            async for state in self.graph.astream(initial_state):
                # Yield thought trace updates
                for thought in state.get("thought_trace", []):
                    yield {
                        "type": "thought",
                        "content": thought
                    }
                
                # Yield tool calls
                for tool_call in state.get("tool_calls", []):
                    yield {
                        "type": "tool_call",
                        "content": tool_call
                    }
            
            # Yield final answer
            yield {
                "type": "answer",
                "content": state.get("final_answer", ""),
                "conversation_id": str(conversation_id)
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Agent execution failed: {str(e)}"
            }
