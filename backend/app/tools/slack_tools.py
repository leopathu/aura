"""
Slack LangChain Tools
Tools for interacting with Slack workspace
"""

from typing import Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.slack_service import (
    send_slack_message,
    list_slack_channels,
    read_slack_messages
)


# ===== SEND SLACK MESSAGE TOOL =====

class SendSlackMessageInput(BaseModel):
    """Input schema for SendSlackMessageTool"""
    channel: str = Field(
        description="Channel ID or name to send message to (e.g., 'C1234567890' or '#general')"
    )
    text: str = Field(
        description="The message text to send"
    )
    thread_ts: Optional[str] = Field(
        default=None,
        description="Optional timestamp of parent message to reply in thread"
    )


class SendSlackMessageTool(BaseTool):
    """
    Tool for sending messages to Slack channels or threads
    
    Use this tool to:
    - Send messages to public channels
    - Send messages to private channels
    - Reply to threads
    - Notify team members
    """
    name: str = "send_slack_message"
    description: str = """
    Send a message to a Slack channel or thread.
    
    Examples:
    - Send announcement to #general: channel='#general', text='Meeting at 3pm'
    - Reply to thread: channel='#general', text='I agree', thread_ts='1234567890.123456'
    - Send to private channel: channel='engineering-private', text='Deploy complete'
    
    The channel can be:
    - Channel ID (C1234567890)
    - Channel name with # (#general)
    - Channel name without # (general)
    
    Returns: Success message with timestamp of sent message
    """
    args_schema: Type[BaseModel] = SendSlackMessageInput
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    async def _arun(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None
    ) -> str:
        """Execute the tool"""
        try:
            result = await send_slack_message(
                self.db,
                self.user_id,
                self.org_id,
                channel,
                text,
                thread_ts=thread_ts
            )
            
            if thread_ts:
                return f"✅ Message sent to thread in {channel} at {result['ts']}"
            else:
                return f"✅ Message sent to {channel} at {result['ts']}"
        
        except Exception as e:
            return f"❌ Failed to send message: {str(e)}"
    
    def _run(self, *args, **kwargs) -> str:
        """Sync version not implemented"""
        return "Use async version (_arun) instead"


# ===== READ SLACK MESSAGES TOOL =====

class ReadSlackMessagesInput(BaseModel):
    """Input schema for ReadSlackMessagesTool"""
    channel: str = Field(
        description="Channel ID or name to read messages from (e.g., 'C1234567890' or '#general')"
    )
    limit: int = Field(
        default=10,
        description="Number of messages to retrieve (1-100, default 10)"
    )
    oldest: Optional[str] = Field(
        default=None,
        description="Only messages after this Unix timestamp (e.g., '1609459200')"
    )


class ReadSlackMessagesTool(BaseTool):
    """
    Tool for reading message history from Slack channels
    
    Use this tool to:
    - Read recent channel messages
    - Get conversation context
    - Review team discussions
    - Find mentioned information
    """
    name: str = "read_slack_messages"
    description: str = """
    Read message history from a Slack channel.
    
    Examples:
    - Get last 10 messages: channel='#general', limit=10
    - Get last 5 messages: channel='engineering', limit=5
    - Get messages since timestamp: channel='#general', oldest='1609459200'
    
    The channel can be:
    - Channel ID (C1234567890)
    - Channel name with # (#general)
    - Channel name without # (general)
    
    Returns: List of messages with user names, timestamps, and text
    """
    args_schema: Type[BaseModel] = ReadSlackMessagesInput
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    async def _arun(
        self,
        channel: str,
        limit: int = 10,
        oldest: Optional[str] = None
    ) -> str:
        """Execute the tool"""
        try:
            messages = await read_slack_messages(
                self.db,
                self.user_id,
                self.org_id,
                channel,
                limit=limit,
                oldest=oldest
            )
            
            if not messages:
                return f"No messages found in {channel}"
            
            # Format messages for display
            formatted = [f"📬 Messages from {channel} (showing {len(messages)}):\n"]
            
            for msg in messages:
                user = msg.get('user_name', 'Unknown User')
                timestamp = msg.get('timestamp', '')
                text = msg.get('text', '')
                
                # Handle thread replies
                thread_info = ""
                if msg.get('thread_ts'):
                    thread_info = " [Thread Reply]"
                
                formatted.append(f"• {user} ({timestamp}){thread_info}: {text}")
            
            return "\n".join(formatted)
        
        except Exception as e:
            return f"❌ Failed to read messages: {str(e)}"
    
    def _run(self, *args, **kwargs) -> str:
        """Sync version not implemented"""
        return "Use async version (_arun) instead"


# ===== LIST SLACK CHANNELS TOOL =====

class ListSlackChannelsInput(BaseModel):
    """Input schema for ListSlackChannelsTool"""
    exclude_archived: bool = Field(
        default=True,
        description="Exclude archived channels (default True)"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of channels to return (default 100)"
    )


class ListSlackChannelsTool(BaseTool):
    """
    Tool for listing available Slack channels
    
    Use this tool to:
    - Find channel IDs
    - Discover available channels
    - Check channel names
    - See channel topics
    """
    name: str = "list_slack_channels"
    description: str = """
    List all available Slack channels in the workspace.
    
    Examples:
    - List all active channels: exclude_archived=True
    - List all channels including archived: exclude_archived=False
    - Limit results: limit=50
    
    Returns: List of channels with names, IDs, member counts, and topics
    """
    args_schema: Type[BaseModel] = ListSlackChannelsInput
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    async def _arun(
        self,
        exclude_archived: bool = True,
        limit: int = 100
    ) -> str:
        """Execute the tool"""
        try:
            channels = await list_slack_channels(
                self.db,
                self.user_id,
                self.org_id,
                exclude_archived=exclude_archived,
                limit=limit
            )
            
            if not channels:
                return "No channels found"
            
            # Format channels for display
            formatted = [f"📋 Slack Channels ({len(channels)} found):\n"]
            
            for ch in channels:
                name = ch.get('name', 'unknown')
                channel_id = ch.get('id', '')
                is_private = ch.get('is_private', False)
                num_members = ch.get('num_members', 0)
                topic = ch.get('topic', {}).get('value', 'No topic')
                
                privacy = "🔒 Private" if is_private else "🌐 Public"
                
                formatted.append(
                    f"• #{name} ({channel_id}) - {privacy} - {num_members} members\n"
                    f"  Topic: {topic[:80]}{'...' if len(topic) > 80 else ''}"
                )
            
            return "\n".join(formatted)
        
        except Exception as e:
            return f"❌ Failed to list channels: {str(e)}"
    
    def _run(self, *args, **kwargs) -> str:
        """Sync version not implemented"""
        return "Use async version (_arun) instead"


# ===== TOOL REGISTRY HELPERS =====

def get_slack_tools(db: Session, user_id: UUID, org_id: UUID) -> list[BaseTool]:
    """
    Get all Slack tools for an agent
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
    
    Returns:
        List of instantiated Slack tools
    """
    return [
        SendSlackMessageTool(db=db, user_id=user_id, org_id=org_id),
        ReadSlackMessagesTool(db=db, user_id=user_id, org_id=org_id),
        ListSlackChannelsTool(db=db, user_id=user_id, org_id=org_id),
    ]
