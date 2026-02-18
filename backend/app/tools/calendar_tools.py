"""
Calendar LangChain Tools
Tools for AI agents to interact with Google Calendar
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
import dateutil.parser

from app.services import calendar_service


class ListEventsInput(BaseModel):
    """Input for list events tool"""
    max_results: int = Field(default=10, description="Maximum number of events to list")
    days_ahead: int = Field(default=7, description="Number of days ahead to search for events")


class ListEventsTool(BaseTool):
    """Tool for listing calendar events"""
    
    name: str = "list_calendar_events"
    description: str = """
    List upcoming calendar events.
    Use this to see what's scheduled on the user's calendar.
    Returns event titles, times, locations, and attendees.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, max_results: int = 10, days_ahead: int = 7) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            events = asyncio.run(calendar_service.list_calendar_events(
                self.db,
                self.user_id,
                self.org_id,
                max_results,
                days_ahead
            ))
            
            if not events:
                return f"No upcoming events found in the next {days_ahead} days."
            
            # Format results
            result = f"Found {len(events)} upcoming event(s):\n\n"
            for i, event in enumerate(events, 1):
                result += f"{i}. {event['summary']}\n"
                result += f"   When: {event['start']} to {event['end']}\n"
                
                if event['location']:
                    result += f"   Where: {event['location']}\n"
                
                if event['attendees']:
                    result += f"   Attendees: {', '.join(event['attendees'][:3])}"
                    if len(event['attendees']) > 3:
                        result += f" (+{len(event['attendees']) - 3} more)"
                    result += "\n"
                
                if event['description']:
                    desc = event['description'][:100]
                    result += f"   Description: {desc}{'...' if len(event['description']) > 100 else ''}\n"
                
                result += f"   Link: {event['htmlLink']}\n"
                result += f"   Event ID: {event['id']}\n\n"
            
            return result
        
        except Exception as e:
            return f"Error listing calendar events: {str(e)}"
    
    async def _arun(self, max_results: int = 10, days_ahead: int = 7) -> str:
        """Async execution"""
        return self._run(max_results, days_ahead)


class CreateEventInput(BaseModel):
    """Input for create event tool"""
    summary: str = Field(description="Event title/summary")
    start_time: str = Field(description="Event start time (ISO format or natural language like '2024-03-20 14:00')")
    end_time: str = Field(description="Event end time (ISO format or natural language like '2024-03-20 15:00')")
    description: Optional[str] = Field(default=None, description="Event description")
    location: Optional[str] = Field(default=None, description="Event location")
    attendees: Optional[str] = Field(default=None, description="Comma-separated list of attendee emails")


class CreateEventTool(BaseTool):
    """Tool for creating calendar events"""
    
    name: str = "create_calendar_event"
    description: str = """
    Create a new calendar event.
    Use this to schedule meetings, appointments, or reminders.
    Requires title, start time, and end time. Location and attendees are optional.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[str] = None
    ) -> str:
        """Execute the tool"""
        try:
            # Parse times
            try:
                start_dt = dateutil.parser.parse(start_time)
                end_dt = dateutil.parser.parse(end_time)
            except Exception as e:
                return f"Error parsing time: {str(e)}. Please use ISO format like '2024-03-20T14:00:00' or '2024-03-20 14:00'"
            
            # Parse attendees
            attendee_list = None
            if attendees:
                attendee_list = [email.strip() for email in attendees.split(",")]
            
            # Use async wrapper
            import asyncio
            event = asyncio.run(calendar_service.create_calendar_event(
                self.db,
                self.user_id,
                self.org_id,
                summary=summary,
                start_time=start_dt,
                end_time=end_dt,
                description=description,
                location=location,
                attendees=attendee_list
            ))
            
            result = f"✓ Calendar event created successfully!\n\n"
            result += f"Title: {event['summary']}\n"
            result += f"When: {event['start']} to {event['end']}\n"
            result += f"Link: {event['htmlLink']}\n"
            result += f"Event ID: {event['id']}\n"
            
            return result
        
        except Exception as e:
            return f"Error creating calendar event: {str(e)}"
    
    async def _arun(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[str] = None
    ) -> str:
        """Async execution"""
        return self._run(summary, start_time, end_time, description, location, attendees)


class UpdateEventInput(BaseModel):
    """Input for update event tool"""
    event_id: str = Field(description="The ID of the event to update")
    summary: Optional[str] = Field(default=None, description="New event title")
    start_time: Optional[str] = Field(default=None, description="New start time (ISO format)")
    end_time: Optional[str] = Field(default=None, description="New end time (ISO format)")
    description: Optional[str] = Field(default=None, description="New description")
    location: Optional[str] = Field(default=None, description="New location")


class UpdateEventTool(BaseTool):
    """Tool for updating calendar events"""
    
    name: str = "update_calendar_event"
    description: str = """
    Update an existing calendar event.
    Use this to change the time, title, location, or other details of an event.
    Requires the event ID from list_calendar_events.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> str:
        """Execute the tool"""
        try:
            # Parse times if provided
            start_dt = None
            end_dt = None
            
            if start_time:
                try:
                    start_dt = dateutil.parser.parse(start_time)
                except Exception as e:
                    return f"Error parsing start time: {str(e)}"
            
            if end_time:
                try:
                    end_dt = dateutil.parser.parse(end_time)
                except Exception as e:
                    return f"Error parsing end time: {str(e)}"
            
            # Use async wrapper
            import asyncio
            event = asyncio.run(calendar_service.update_calendar_event(
                self.db,
                self.user_id,
                self.org_id,
                event_id=event_id,
                summary=summary,
                start_time=start_dt,
                end_time=end_dt,
                description=description,
                location=location
            ))
            
            result = f"✓ Calendar event updated successfully!\n\n"
            result += f"Title: {event['summary']}\n"
            result += f"When: {event['start']} to {event['end']}\n"
            result += f"Link: {event['htmlLink']}\n"
            
            return result
        
        except Exception as e:
            return f"Error updating calendar event: {str(e)}"
    
    async def _arun(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> str:
        """Async execution"""
        return self._run(event_id, summary, start_time, end_time, description, location)


def get_calendar_tools(db: Session, user_id: UUID, org_id: UUID) -> List[BaseTool]:
    """
    Get all Calendar tools for an agent
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        List of Calendar tools
    """
    return [
        ListEventsTool(db=db, user_id=user_id, org_id=org_id),
        CreateEventTool(db=db, user_id=user_id, org_id=org_id),
        UpdateEventTool(db=db, user_id=user_id, org_id=org_id)
    ]
