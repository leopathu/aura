"""
Server-Sent Events (SSE) Service
Handles streaming responses for real-time chat updates
"""

from typing import AsyncGenerator, Dict, Any, Optional
import asyncio
import json
from datetime import datetime
from enum import Enum


class SSEEventType(str, Enum):
    """SSE event types for chat streaming"""
    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOKEN = "token"
    COMPLETION = "completion"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    STATUS = "status"


class SSEFormatter:
    """
    SSE event formatter (TASK-259)
    
    Formats data into Server-Sent Events protocol format
    """
    
    @staticmethod
    def format_event(
        event_type: SSEEventType,
        data: Any,
        event_id: Optional[str] = None
    ) -> str:
        """
        Format data as SSE event
        
        Args:
            event_type: Type of event
            data: Event data (will be JSON serialized)
            event_id: Optional event ID
            
        Returns:
            Formatted SSE string
        """
        lines = []
        
        # Add event ID if provided
        if event_id:
            lines.append(f"id: {event_id}")
        
        # Add event type
        lines.append(f"event: {event_type.value}")
        
        # Add data (JSON serialized)
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        lines.append(f"data: {data_str}")
        
        # SSE format requires double newline at end
        return "\n".join(lines) + "\n\n"
    
    @staticmethod
    def format_heartbeat() -> str:
        """
        Format heartbeat event (TASK-260)
        
        Returns:
            Formatted heartbeat SSE event
        """
        return SSEFormatter.format_event(
            SSEEventType.HEARTBEAT,
            {"timestamp": datetime.utcnow().isoformat()}
        )
    
    @staticmethod
    def format_error(error_message: str, error_code: Optional[str] = None) -> str:
        """
        Format error event (TASK-262)
        
        Args:
            error_message: Error description
            error_code: Optional error code
            
        Returns:
            Formatted error SSE event
        """
        return SSEFormatter.format_event(
            SSEEventType.ERROR,
            {
                "message": error_message,
                "code": error_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def format_thought(
        step: str,
        node: str,
        content: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format thought trace event (TASK-264)
        
        Args:
            step: Step identifier
            node: Graph node name
            content: Thought content
            status: Execution status
            metadata: Additional metadata
            
        Returns:
            Formatted thought SSE event
        """
        return SSEFormatter.format_event(
            SSEEventType.THOUGHT,
            {
                "timestamp": datetime.utcnow().isoformat(),
                "step": step,
                "node": node,
                "content": content,
                "status": status,
                "metadata": metadata or {}
            }
        )
    
    @staticmethod
    def format_tool_call(
        tool_name: str,
        arguments: Dict[str, Any],
        status: str,
        tool_id: Optional[str] = None
    ) -> str:
        """
        Format tool call event (TASK-265)
        
        Args:
            tool_name: Name of tool
            arguments: Tool arguments
            status: Execution status
            tool_id: Optional tool call ID
            
        Returns:
            Formatted tool call SSE event
        """
        return SSEFormatter.format_event(
            SSEEventType.TOOL_CALL,
            {
                "timestamp": datetime.utcnow().isoformat(),
                "tool_id": tool_id or f"{tool_name}_{datetime.utcnow().timestamp()}",
                "tool_name": tool_name,
                "arguments": arguments,
                "status": status
            }
        )
    
    @staticmethod
    def format_tool_result(
        tool_name: str,
        result: Optional[str],
        error: Optional[str],
        duration_ms: Optional[int],
        tool_id: Optional[str] = None
    ) -> str:
        """
        Format tool result event (TASK-265)
        
        Args:
            tool_name: Name of tool
            result: Tool result
            error: Error message if failed
            duration_ms: Execution duration
            tool_id: Optional tool call ID
            
        Returns:
            Formatted tool result SSE event
        """
        return SSEFormatter.format_event(
            SSEEventType.TOOL_RESULT,
            {
                "timestamp": datetime.utcnow().isoformat(),
                "tool_id": tool_id or tool_name,
                "tool_name": tool_name,
                "result": result,
                "error": error,
                "duration_ms": duration_ms,
                "status": "completed" if not error else "failed"
            }
        )
    
    @staticmethod
    def format_token(token: str) -> str:
        """
        Format token event for streaming response (TASK-266)
        
        Args:
            token: Response token/chunk
            
        Returns:
            Formatted token SSE event
        """
        return SSEFormatter.format_event(
            SSEEventType.TOKEN,
            {"token": token}
        )
    
    @staticmethod
    def format_completion(
        final_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format completion event (TASK-267)
        
        Args:
            final_response: Complete response text
            metadata: Additional completion metadata
            
        Returns:
            Formatted completion SSE event
        """
        return SSEFormatter.format_event(
            SSEEventType.COMPLETION,
            {
                "timestamp": datetime.utcnow().isoformat(),
                "response": final_response,
                "metadata": metadata or {}
            }
        )
    
    @staticmethod
    def format_status(status: str, message: str) -> str:
        """
        Format status update event
        
        Args:
            status: Status identifier
            message: Status message
            
        Returns:
            Formatted status SSE event
        """
        return SSEFormatter.format_event(
            SSEEventType.STATUS,
            {
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "message": message
            }
        )


class SSEConnectionManager:
    """
    SSE connection manager (TASK-261)
    
    Manages active SSE connections and handles cleanup
    """
    
    def __init__(self):
        self._active_connections: Dict[str, bool] = {}
    
    def register_connection(self, connection_id: str):
        """Register a new SSE connection"""
        self._active_connections[connection_id] = True
    
    def unregister_connection(self, connection_id: str):
        """Unregister an SSE connection"""
        if connection_id in self._active_connections:
            del self._active_connections[connection_id]
    
    def is_connected(self, connection_id: str) -> bool:
        """Check if connection is still active"""
        return self._active_connections.get(connection_id, False)
    
    def disconnect(self, connection_id: str):
        """Mark connection as disconnected"""
        if connection_id in self._active_connections:
            self._active_connections[connection_id] = False
    
    def get_active_count(self) -> int:
        """Get count of active connections"""
        return sum(1 for active in self._active_connections.values() if active)


# Global connection manager
_connection_manager = SSEConnectionManager()


def get_connection_manager() -> SSEConnectionManager:
    """Get global SSE connection manager"""
    return _connection_manager


async def sse_heartbeat_generator(
    connection_id: str,
    interval_seconds: int = 15
) -> AsyncGenerator[str, None]:
    """
    Generate heartbeat events (TASK-260)
    
    Keeps SSE connection alive with periodic heartbeats
    
    Args:
        connection_id: Connection identifier
        interval_seconds: Heartbeat interval
        
    Yields:
        Heartbeat SSE events
    """
    manager = get_connection_manager()
    
    while manager.is_connected(connection_id):
        yield SSEFormatter.format_heartbeat()
        await asyncio.sleep(interval_seconds)


async def stream_with_heartbeat(
    event_generator: AsyncGenerator[str, None],
    connection_id: str,
    heartbeat_interval: int = 15
) -> AsyncGenerator[str, None]:
    """
    Combine event stream with heartbeats (TASK-260)
    
    Args:
        event_generator: Main event generator
        connection_id: Connection identifier
        heartbeat_interval: Heartbeat interval in seconds
        
    Yields:
        Events from main generator + heartbeats
    """
    manager = get_connection_manager()
    manager.register_connection(connection_id)
    
    try:
        last_heartbeat = asyncio.get_event_loop().time()
        
        async for event in event_generator:
            # Check if we need a heartbeat
            current_time = asyncio.get_event_loop().time()
            if current_time - last_heartbeat >= heartbeat_interval:
                yield SSEFormatter.format_heartbeat()
                last_heartbeat = current_time
            
            yield event
            
            # Check if client disconnected
            if not manager.is_connected(connection_id):
                break
    
    except asyncio.CancelledError:
        # Client disconnected (TASK-268)
        manager.disconnect(connection_id)
        raise
    
    except Exception as e:
        # Error occurred (TASK-262)
        yield SSEFormatter.format_error(str(e))
        manager.disconnect(connection_id)
    
    finally:
        # Cleanup
        manager.unregister_connection(connection_id)


class SSEResponseGenerator:
    """
    SSE response generator (TASK-258)
    
    Main class for generating SSE responses
    """
    
    def __init__(self, connection_id: str):
        self.connection_id = connection_id
        self.formatter = SSEFormatter()
        self.manager = get_connection_manager()
    
    async def generate_events(
        self,
        event_stream: AsyncGenerator[Dict[str, Any], None]
    ) -> AsyncGenerator[str, None]:
        """
        Generate SSE formatted events from event stream
        
        Args:
            event_stream: Async generator of event dictionaries
            
        Yields:
            SSE formatted event strings
        """
        self.manager.register_connection(self.connection_id)
        
        try:
            async for event in event_stream:
                event_type = event.get("type")
                event_data = event.get("data", {})
                
                # Format based on event type
                if event_type == "thought":
                    formatted = self.formatter.format_thought(
                        step=event_data.get("step", ""),
                        node=event_data.get("node", ""),
                        content=event_data.get("content", ""),
                        status=event_data.get("status", "in_progress"),
                        metadata=event_data.get("metadata")
                    )
                
                elif event_type == "tool_call":
                    formatted = self.formatter.format_tool_call(
                        tool_name=event_data.get("tool_name", ""),
                        arguments=event_data.get("arguments", {}),
                        status=event_data.get("status", "pending"),
                        tool_id=event_data.get("tool_id")
                    )
                
                elif event_type == "tool_result":
                    formatted = self.formatter.format_tool_result(
                        tool_name=event_data.get("tool_name", ""),
                        result=event_data.get("result"),
                        error=event_data.get("error"),
                        duration_ms=event_data.get("duration_ms"),
                        tool_id=event_data.get("tool_id")
                    )
                
                elif event_type == "token":
                    formatted = self.formatter.format_token(
                        event_data.get("token", "")
                    )
                
                elif event_type == "completion":
                    formatted = self.formatter.format_completion(
                        final_response=event_data.get("response", ""),
                        metadata=event_data.get("metadata")
                    )
                
                elif event_type == "status":
                    formatted = self.formatter.format_status(
                        status=event_data.get("status", ""),
                        message=event_data.get("message", "")
                    )
                
                elif event_type == "error":
                    formatted = self.formatter.format_error(
                        error_message=event_data.get("message", "Unknown error"),
                        error_code=event_data.get("code")
                    )
                
                else:
                    # Unknown event type
                    continue
                
                yield formatted
                
                # Check connection status
                if not self.manager.is_connected(self.connection_id):
                    break
        
        except asyncio.CancelledError:
            self.manager.disconnect(self.connection_id)
            raise
        
        except Exception as e:
            yield self.formatter.format_error(str(e))
        
        finally:
            self.manager.unregister_connection(self.connection_id)
