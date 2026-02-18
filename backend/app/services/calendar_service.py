"""
Google Calendar Service
Provides Calendar API functionality for reading and managing calendar events
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session
from uuid import UUID
import pytz

from app.services.oauth_service import get_oauth_token
from app.services.encryption_service import encryption_service


# Calendar API scopes
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar"
]


class CalendarClient:
    """Wrapper around Google Calendar API"""
    
    def __init__(self, access_token: str):
        """
        Initialize Calendar client with OAuth access token
        
        Args:
            access_token: OAuth access token for Calendar API
        """
        credentials = Credentials(token=access_token)
        self.service = build("calendar", "v3", credentials=credentials)
    
    def list_events(
        self,
        max_results: int = 10,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        calendar_id: str = "primary",
        timezone: str = "UTC"
    ) -> List[Dict[str, Any]]:
        """
        List calendar events
        
        Args:
            max_results: Maximum number of events to return
            time_min: Start time for event search
            time_max: End time for event search
            calendar_id: Calendar ID (default: primary)
            timezone: Timezone for events
            
        Returns:
            List of calendar events
        """
        try:
            # Default to events from now onwards
            if time_min is None:
                time_min = datetime.utcnow()
            
            # Convert to RFC3339 format
            time_min_str = time_min.isoformat() + "Z"
            time_max_str = time_max.isoformat() + "Z" if time_max else None
            
            # Build request parameters
            params = {
                "calendarId": calendar_id,
                "timeMin": time_min_str,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
                "timeZone": timezone
            }
            
            if time_max_str:
                params["timeMax"] = time_max_str
            
            # Execute request
            events_result = self.service.events().list(**params).execute()
            events = events_result.get("items", [])
            
            # Format events
            formatted_events = []
            for event in events:
                formatted_event = {
                    "id": event.get("id"),
                    "summary": event.get("summary", "No Title"),
                    "description": event.get("description", ""),
                    "location": event.get("location", ""),
                    "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
                    "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
                    "attendees": [
                        attendee.get("email") 
                        for attendee in event.get("attendees", [])
                    ],
                    "htmlLink": event.get("htmlLink"),
                    "status": event.get("status"),
                    "organizer": event.get("organizer", {}).get("email")
                }
                formatted_events.append(formatted_event)
            
            return formatted_events
        
        except HttpError as error:
            raise Exception(f"Calendar API error: {error}")
    
    def get_event(self, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """
        Get a specific calendar event
        
        Args:
            event_id: Event ID
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            Event details
        """
        try:
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return {
                "id": event.get("id"),
                "summary": event.get("summary", "No Title"),
                "description": event.get("description", ""),
                "location": event.get("location", ""),
                "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
                "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
                "attendees": [
                    attendee.get("email") 
                    for attendee in event.get("attendees", [])
                ],
                "htmlLink": event.get("htmlLink"),
                "status": event.get("status"),
                "organizer": event.get("organizer", {}).get("email")
            }
        
        except HttpError as error:
            raise Exception(f"Calendar API error: {error}")
    
    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        timezone: str = "UTC",
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """
        Create a calendar event
        
        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description
            location: Event location
            attendees: List of attendee email addresses
            timezone: Timezone for event
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            Created event details
        """
        try:
            # Build event object
            event_body = {
                "summary": summary,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone
                }
            }
            
            if description:
                event_body["description"] = description
            
            if location:
                event_body["location"] = location
            
            if attendees:
                event_body["attendees"] = [{"email": email} for email in attendees]
            
            # Create event
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()
            
            return {
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": event.get("start", {}).get("dateTime"),
                "end": event.get("end", {}).get("dateTime"),
                "htmlLink": event.get("htmlLink")
            }
        
        except HttpError as error:
            raise Exception(f"Calendar API error: {error}")
    
    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        timezone: str = "UTC",
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """
        Update a calendar event
        
        Args:
            event_id: Event ID to update
            summary: New event title
            start_time: New start time
            end_time: New end time
            description: New description
            location: New location
            attendees: New list of attendee emails
            timezone: Timezone for event
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            Updated event details
        """
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields
            if summary is not None:
                event["summary"] = summary
            
            if start_time is not None:
                event["start"] = {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone
                }
            
            if end_time is not None:
                event["end"] = {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone
                }
            
            if description is not None:
                event["description"] = description
            
            if location is not None:
                event["location"] = location
            
            if attendees is not None:
                event["attendees"] = [{"email": email} for email in attendees]
            
            # Update event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            return {
                "id": updated_event.get("id"),
                "summary": updated_event.get("summary"),
                "start": updated_event.get("start", {}).get("dateTime"),
                "end": updated_event.get("end", {}).get("dateTime"),
                "htmlLink": updated_event.get("htmlLink")
            }
        
        except HttpError as error:
            raise Exception(f"Calendar API error: {error}")
    
    def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id: Event ID to delete
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            True if deleted successfully
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return True
        
        except HttpError as error:
            raise Exception(f"Calendar API error: {error}")


async def get_calendar_client(
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> CalendarClient:
    """
    Get Calendar client for user with OAuth credentials
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        CalendarClient instance
        
    Raises:
        Exception if no valid OAuth token found
    """
    # Get OAuth token
    oauth_token = await get_oauth_token(db, user_id, org_id, "google")
    
    if not oauth_token or not oauth_token.is_active:
        raise Exception("No active Google Calendar connection found. Please connect your Google account.")
    
    # Decrypt access token
    access_token = encryption_service.decrypt(oauth_token.encrypted_access_token)
    
    # Create and return client
    return CalendarClient(access_token)


# Convenience async functions

async def list_calendar_events(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    max_results: int = 10,
    days_ahead: int = 7,
    timezone: str = "UTC"
) -> List[Dict[str, Any]]:
    """
    List upcoming calendar events
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        max_results: Maximum events to return
        days_ahead: Number of days ahead to search
        timezone: Timezone for events
        
    Returns:
        List of calendar events
    """
    client = await get_calendar_client(db, user_id, org_id)
    
    time_min = datetime.utcnow()
    time_max = time_min + timedelta(days=days_ahead)
    
    return client.list_events(
        max_results=max_results,
        time_min=time_min,
        time_max=time_max,
        timezone=timezone
    )


async def get_calendar_event(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    event_id: str
) -> Dict[str, Any]:
    """
    Get specific calendar event
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        event_id: Event ID
        
    Returns:
        Event details
    """
    client = await get_calendar_client(db, user_id, org_id)
    return client.get_event(event_id)


async def create_calendar_event(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    summary: str,
    start_time: datetime,
    end_time: datetime,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    """
    Create calendar event
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        summary: Event title
        start_time: Start time
        end_time: End time
        description: Event description
        location: Event location
        attendees: Attendee emails
        timezone: Timezone
        
    Returns:
        Created event details
    """
    client = await get_calendar_client(db, user_id, org_id)
    
    return client.create_event(
        summary=summary,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
        attendees=attendees,
        timezone=timezone
    )


async def update_calendar_event(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    event_id: str,
    summary: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    """
    Update calendar event
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        event_id: Event ID
        summary: New title
        start_time: New start time
        end_time: New end time
        description: New description
        location: New location
        attendees: New attendees
        timezone: Timezone
        
    Returns:
        Updated event details
    """
    client = await get_calendar_client(db, user_id, org_id)
    
    return client.update_event(
        event_id=event_id,
        summary=summary,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
        attendees=attendees,
        timezone=timezone
    )


async def delete_calendar_event(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    event_id: str
) -> bool:
    """
    Delete calendar event
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        event_id: Event ID
        
    Returns:
        True if deleted
    """
    client = await get_calendar_client(db, user_id, org_id)
    return client.delete_event(event_id)
