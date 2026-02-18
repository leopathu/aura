"""
Slack Service
Provides Slack API functionality for messaging and channel management
"""

from typing import Optional, List, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.oauth_service import get_oauth_token
from app.services.encryption_service import encryption_service


class SlackClient:
    """Wrapper around Slack API"""
    
    def __init__(self, access_token: str):
        """
        Initialize Slack client with OAuth access token
        
        Args:
            access_token: OAuth access token for Slack API
        """
        self.client = WebClient(token=access_token)
        self.access_token = access_token
    
    def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a Slack channel
        
        Args:
            channel: Channel ID or name (e.g., "#general" or "C1234567890")
            text: Message text
            thread_ts: Thread timestamp to reply to (optional)
            blocks: Rich message blocks (optional)
            
        Returns:
            Message details including timestamp
        """
        try:
            kwargs = {
                "channel": channel,
                "text": text
            }
            
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            
            if blocks:
                kwargs["blocks"] = blocks
            
            response = self.client.chat_postMessage(**kwargs)
            
            return {
                "ok": response["ok"],
                "channel": response["channel"],
                "ts": response["ts"],
                "message": response["message"]["text"]
            }
        
        except SlackApiError as error:
            raise Exception(f"Slack API error: {error.response['error']}")
    
    def list_channels(
        self,
        exclude_archived: bool = True,
        limit: int = 100,
        types: str = "public_channel,private_channel"
    ) -> List[Dict[str, Any]]:
        """
        List Slack channels
        
        Args:
            exclude_archived: Exclude archived channels
            limit: Maximum channels to return
            types: Channel types to include
            
        Returns:
            List of channels
        """
        try:
            response = self.client.conversations_list(
                exclude_archived=exclude_archived,
                limit=limit,
                types=types
            )
            
            channels = []
            for channel in response["channels"]:
                channels.append({
                    "id": channel["id"],
                    "name": channel["name"],
                    "is_channel": channel.get("is_channel", False),
                    "is_private": channel.get("is_private", False),
                    "is_member": channel.get("is_member", False),
                    "num_members": channel.get("num_members", 0),
                    "topic": channel.get("topic", {}).get("value", ""),
                    "purpose": channel.get("purpose", {}).get("value", "")
                })
            
            return channels
        
        except SlackApiError as error:
            raise Exception(f"Slack API error: {error.response['error']}")
    
    def read_messages(
        self,
        channel: str,
        limit: int = 10,
        oldest: Optional[str] = None,
        latest: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Read messages from a Slack channel
        
        Args:
            channel: Channel ID
            limit: Maximum messages to return
            oldest: Oldest timestamp to include
            latest: Latest timestamp to include
            
        Returns:
            List of messages
        """
        try:
            kwargs = {
                "channel": channel,
                "limit": limit
            }
            
            if oldest:
                kwargs["oldest"] = oldest
            
            if latest:
                kwargs["latest"] = latest
            
            response = self.client.conversations_history(**kwargs)
            
            messages = []
            for msg in response["messages"]:
                # Get user info for the message
                user_id = msg.get("user")
                user_name = "Unknown"
                
                if user_id:
                    try:
                        user_info = self.client.users_info(user=user_id)
                        user_name = user_info["user"].get("real_name") or user_info["user"].get("name")
                    except:
                        user_name = user_id
                
                messages.append({
                    "ts": msg["ts"],
                    "user": user_name,
                    "user_id": user_id,
                    "text": msg.get("text", ""),
                    "type": msg.get("type", "message"),
                    "thread_ts": msg.get("thread_ts"),
                    "reply_count": msg.get("reply_count", 0)
                })
            
            return messages
        
        except SlackApiError as error:
            raise Exception(f"Slack API error: {error.response['error']}")
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """
        Get information about the connected Slack workspace
        
        Returns:
            Workspace details
        """
        try:
            # Get team info
            team_response = self.client.team_info()
            team = team_response["team"]
            
            # Get auth test to verify token
            auth_response = self.client.auth_test()
            
            return {
                "team_id": team["id"],
                "team_name": team["name"],
                "team_domain": team.get("domain", ""),
                "user_id": auth_response["user_id"],
                "user": auth_response["user"],
                "url": auth_response.get("url", "")
            }
        
        except SlackApiError as error:
            raise Exception(f"Slack API error: {error.response['error']}")
    
    def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """
        Get information about a specific channel
        
        Args:
            channel: Channel ID
            
        Returns:
            Channel details
        """
        try:
            response = self.client.conversations_info(channel=channel)
            channel_data = response["channel"]
            
            return {
                "id": channel_data["id"],
                "name": channel_data["name"],
                "is_channel": channel_data.get("is_channel", False),
                "is_private": channel_data.get("is_private", False),
                "is_member": channel_data.get("is_member", False),
                "num_members": channel_data.get("num_members", 0),
                "topic": channel_data.get("topic", {}).get("value", ""),
                "purpose": channel_data.get("purpose", {}).get("value", ""),
                "created": channel_data.get("created", 0)
            }
        
        except SlackApiError as error:
            raise Exception(f"Slack API error: {error.response['error']}")


async def get_slack_client(
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> SlackClient:
    """
    Get Slack client for user with OAuth credentials
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        SlackClient instance
        
    Raises:
        Exception if no valid Slack OAuth token found
    """
    # Get Slack OAuth token
    oauth_token = await get_oauth_token(db, user_id, org_id, "slack")
    
    if not oauth_token or not oauth_token.is_active:
        raise Exception("No active Slack connection found. Please connect your Slack workspace.")
    
    # Decrypt access token
    access_token = encryption_service.decrypt(oauth_token.encrypted_access_token)
    
    # Create and return client
    return SlackClient(access_token)


# Convenience async functions

async def send_slack_message(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    channel: str,
    text: str,
    thread_ts: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a Slack message
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        channel: Channel ID or name
        text: Message text
        thread_ts: Thread timestamp
        
    Returns:
        Message details
    """
    client = await get_slack_client(db, user_id, org_id)
    return client.send_message(channel, text, thread_ts)


async def list_slack_channels(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    exclude_archived: bool = True,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List Slack channels
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        exclude_archived: Exclude archived channels
        limit: Maximum channels to return
        
    Returns:
        List of channels
    """
    client = await get_slack_client(db, user_id, org_id)
    return client.list_channels(exclude_archived, limit)


async def read_slack_messages(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    channel: str,
    limit: int = 10,
    oldest: Optional[str] = None,
    latest: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Read Slack messages
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        channel: Channel ID
        limit: Maximum messages
        oldest: Only messages after this timestamp
        latest: Only messages before this timestamp
        
    Returns:
        List of messages
    """
    client = await get_slack_client(db, user_id, org_id)
    return client.read_messages(channel, limit, oldest, latest)


async def get_slack_workspace_info(
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> Dict[str, Any]:
    """
    Get Slack workspace info
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        Workspace details
    """
    client = await get_slack_client(db, user_id, org_id)
    return client.get_workspace_info()
