"""
Google Calendar Operations Module

This module provides functions for creating, reading, updating, and deleting
calendar events, as well as utilities for parsing dates and scheduling.
"""

import datetime
import pytz
from dateutil import parser
from dateutil.relativedelta import relativedelta
from googleapiclient.errors import HttpError
from auth import get_authenticated_service

class CalendarManager:
    """Manages Google Calendar operations."""
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Initialize the CalendarManager.
        
        Args:
            credentials_file (str): Path to OAuth credentials file
        """
        self.service = get_authenticated_service(credentials_file)
        self.timezone = pytz.timezone('America/New_York')  # Default timezone
    
    def set_timezone(self, timezone_str):
        """
        Set the default timezone for calendar operations.
        
        Args:
            timezone_str (str): Timezone string (e.g., 'America/New_York')
        """
        try:
            self.timezone = pytz.timezone(timezone_str)
            print(f"Timezone set to {timezone_str}")
        except pytz.exceptions.UnknownTimeZoneError:
            print(f"Unknown timezone: {timezone_str}. Using default.")
    
    def parse_datetime(self, date_str, default_time=None):
        """
        Parse a natural language date/time string.
        
        Args:
            date_str (str): Date/time string to parse
            default_time (str): Default time if none specified (e.g., '09:00')
        
        Returns:
            datetime.datetime: Parsed datetime object
        """
        try:
            # Handle relative dates
            now = datetime.datetime.now(self.timezone)
            
            if 'today' in date_str.lower():
                base_date = now.date()
            elif 'tomorrow' in date_str.lower():
                base_date = (now + datetime.timedelta(days=1)).date()
            elif 'next week' in date_str.lower():
                base_date = (now + datetime.timedelta(weeks=1)).date()
            elif 'next monday' in date_str.lower():
                days_ahead = 0 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                base_date = (now + datetime.timedelta(days=days_ahead)).date()
            elif 'next tuesday' in date_str.lower():
                days_ahead = 1 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                base_date = (now + datetime.timedelta(days=days_ahead)).date()
            elif 'next wednesday' in date_str.lower():
                days_ahead = 2 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                base_date = (now + datetime.timedelta(days=days_ahead)).date()
            elif 'next thursday' in date_str.lower():
                days_ahead = 3 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                base_date = (now + datetime.timedelta(days=days_ahead)).date()
            elif 'next friday' in date_str.lower():
                days_ahead = 4 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                base_date = (now + datetime.timedelta(days=days_ahead)).date()
            else:
                # Try to parse the date string directly
                parsed = parser.parse(date_str, default=now)
                return self.timezone.localize(parsed) if parsed.tzinfo is None else parsed
            
            # Extract time from the string or use default
            time_str = default_time or '09:00'
            for word in date_str.split():
                if ':' in word or ('am' in word.lower()) or ('pm' in word.lower()):
                    time_str = word
                    break
            
            # Combine date and time
            if default_time and not any(t in date_str.lower() for t in ['am', 'pm', ':']):
                time_str = default_time
            
            time_obj = parser.parse(time_str).time()
            dt = datetime.datetime.combine(base_date, time_obj)
            
            return self.timezone.localize(dt)
            
        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
            # Return a default time (1 hour from now)
            return datetime.datetime.now(self.timezone) + datetime.timedelta(hours=1)
    
    def create_event(self, title, start_time, end_time=None, description=None, 
                    location=None, attendees=None, calendar_id='primary'):
        """
        Create a new calendar event.
        
        Args:
            title (str): Event title
            start_time (datetime or str): Start time
            end_time (datetime or str): End time (defaults to 1 hour after start)
            description (str): Event description
            location (str): Event location
            attendees (list): List of attendee email addresses
            calendar_id (str): Calendar ID to create event in
        
        Returns:
            dict: Created event information
        """
        try:
            # Parse start time
            if isinstance(start_time, str):
                start_time = self.parse_datetime(start_time)
            
            # Parse or calculate end time
            if end_time is None:
                end_time = start_time + datetime.timedelta(hours=1)
            elif isinstance(end_time, str):
                end_time = self.parse_datetime(end_time)
            
            # Create event body
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': str(self.timezone),
                },
            }
            
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=calendar_id, 
                body=event
            ).execute()
            
            print(f"Event created: {created_event.get('htmlLink')}")
            return created_event
        
        except HttpError as e:
            print(f"HTTP Error creating event: {e}")
            return None
        except Exception as e:
            print(f"Error creating event: {e}")
            return None
    
    def get_events(self, time_min=None, time_max=None, max_results=10, 
                  calendar_id='primary'):
        """
        Retrieve events from calendar.
        
        Args:
            time_min (datetime or str): Minimum time for events
            time_max (datetime or str): Maximum time for events  
            max_results (int): Maximum number of events to return
            calendar_id (str): Calendar ID to search
        
        Returns:
            list: List of events
        """
        try:
            # Default to events from now
            if time_min is None:
                time_min = datetime.datetime.now(self.timezone)
            elif isinstance(time_min, str):
                time_min = self.parse_datetime(time_min)
            
            if time_max and isinstance(time_max, str):
                time_max = self.parse_datetime(time_max)
            
            # Format times for API
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat() if time_max else None,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        
        except HttpError as e:
            print(f"HTTP Error retrieving events: {e}")
            return []
        except Exception as e:
            print(f"Error retrieving events: {e}")
            return []
    
    def update_event(self, event_id, title=None, start_time=None, end_time=None,
                    description=None, location=None, calendar_id='primary'):
        """
        Update an existing event.
        
        Args:
            event_id (str): ID of event to update
            title (str): New title
            start_time (datetime or str): New start time
            end_time (datetime or str): New end time
            description (str): New description
            location (str): New location
            calendar_id (str): Calendar ID
        
        Returns:
            dict: Updated event information
        """
        try:
            # Get the existing event
            event = self.service.events().get(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if title:
                event['summary'] = title
            if start_time:
                if isinstance(start_time, str):
                    start_time = self.parse_datetime(start_time)
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': str(self.timezone),
                }
            if end_time:
                if isinstance(end_time, str):
                    end_time = self.parse_datetime(end_time)
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': str(self.timezone),
                }
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            print(f"Event updated: {updated_event.get('htmlLink')}")
            return updated_event
        
        except HttpError as e:
            print(f"HTTP Error updating event: {e}")
            return None
        except Exception as e:
            print(f"Error updating event: {e}")
            return None
    
    def delete_event(self, event_id, calendar_id='primary'):
        """
        Delete an event.
        
        Args:
            event_id (str): ID of event to delete
            calendar_id (str): Calendar ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            print(f"Event {event_id} deleted successfully")
            return True
        
        except HttpError as e:
            print(f"HTTP Error deleting event: {e}")
            return False
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False
    
    def find_free_time(self, duration_hours=1, search_days=7, 
                      start_hour=9, end_hour=17, calendar_id='primary'):
        """
        Find available time slots in the calendar.
        
        Args:
            duration_hours (float): Duration needed in hours
            search_days (int): Number of days to search ahead
            start_hour (int): Earliest hour to consider (24-hour format)
            end_hour (int): Latest hour to consider (24-hour format)
            calendar_id (str): Calendar ID to check
        
        Returns:
            list: List of available time slots
        """
        try:
            now = datetime.datetime.now(self.timezone)
            search_end = now + datetime.timedelta(days=search_days)
            
            # Get all events in the search period
            events = self.get_events(
                time_min=now,
                time_max=search_end,
                max_results=100,
                calendar_id=calendar_id
            )
            
            free_slots = []
            current_day = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            
            for day in range(search_days):
                day_start = current_day + datetime.timedelta(days=day)
                day_end = day_start.replace(hour=end_hour)
                
                # Skip weekends (optional)
                if day_start.weekday() >= 5:  # Saturday=5, Sunday=6
                    continue
                
                # Find busy periods for this day
                busy_periods = []
                for event in events:
                    event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                    event_end_str = event['end'].get('dateTime', event['end'].get('date'))
                    
                    event_start = parser.parse(event_start_str)
                    event_end = parser.parse(event_end_str)
                    
                    # Check if event overlaps with this day
                    if (event_start.date() == day_start.date() or 
                        event_end.date() == day_start.date()):
                        busy_periods.append((event_start, event_end))
                
                # Sort busy periods
                busy_periods.sort(key=lambda x: x[0])
                
                # Find free slots
                slot_start = day_start
                for busy_start, busy_end in busy_periods:
                    # Check if there's a free slot before this busy period
                    if slot_start + datetime.timedelta(hours=duration_hours) <= busy_start:
                        free_slots.append({
                            'start': slot_start,
                            'end': slot_start + datetime.timedelta(hours=duration_hours),
                            'duration': duration_hours
                        })
                    
                    slot_start = max(slot_start, busy_end)
                
                # Check if there's time at the end of the day
                if slot_start + datetime.timedelta(hours=duration_hours) <= day_end:
                    free_slots.append({
                        'start': slot_start,
                        'end': slot_start + datetime.timedelta(hours=duration_hours),
                        'duration': duration_hours
                    })
            
            return free_slots[:10]  # Return first 10 slots
        
        except Exception as e:
            print(f"Error finding free time: {e}")
            return []
    
    def find_free_time_in_range(self, duration_hours=1, start_date=None, end_date=None,
                               start_hour=10, end_hour=19, calendar_id='primary'):
        """
        Find available time slots within a specific date range.
        
        Args:
            duration_hours (float): Duration needed in hours
            start_date (date): Start date for search
            end_date (date): End date for search
            start_hour (int): Earliest hour to consider (24-hour format)
            end_hour (int): Latest hour to consider (24-hour format)
            calendar_id (str): Calendar ID to check
        
        Returns:
            list: List of available time slots
        """
        try:
            if not start_date or not end_date:
                raise ValueError("start_date and end_date are required")
            
            # Convert dates to datetime objects with timezone
            search_start = self.timezone.localize(
                datetime.datetime.combine(start_date, datetime.time(0, 0))
            )
            search_end = self.timezone.localize(
                datetime.datetime.combine(end_date, datetime.time(23, 59))
            )
            
            # Get all events in the search period
            events = self.get_events(
                time_min=search_start,
                time_max=search_end,
                max_results=100,
                calendar_id=calendar_id
            )
            
            free_slots = []
            current_date = start_date
            
            while current_date <= end_date:
                day_start = self.timezone.localize(
                    datetime.datetime.combine(current_date, datetime.time(start_hour, 0))
                )
                day_end = self.timezone.localize(
                    datetime.datetime.combine(current_date, datetime.time(end_hour, 0))
                )
                
                # Find busy periods for this day
                busy_periods = []
                for event in events:
                    event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                    event_end_str = event['end'].get('dateTime', event['end'].get('date'))
                    
                    if event_start_str and event_end_str:
                        try:
                            event_start = parser.parse(event_start_str)
                            event_end = parser.parse(event_end_str)
                            
                            # Convert to timezone if needed
                            if event_start.tzinfo is None:
                                event_start = self.timezone.localize(event_start)
                            elif event_start.tzinfo != self.timezone:
                                event_start = event_start.astimezone(self.timezone)
                                
                            if event_end.tzinfo is None:
                                event_end = self.timezone.localize(event_end)
                            elif event_end.tzinfo != self.timezone:
                                event_end = event_end.astimezone(self.timezone)
                            
                            # Check if event overlaps with this day
                            if (event_start.date() == current_date or 
                                event_end.date() == current_date or
                                (event_start.date() < current_date < event_end.date())):
                                busy_periods.append((event_start, event_end))
                        except Exception as e:
                            continue  # Skip problematic events
                
                # Sort busy periods
                busy_periods.sort(key=lambda x: x[0])
                
                # Find free slots for this day
                slot_start = day_start
                for busy_start, busy_end in busy_periods:
                    # Check if there's a free slot before this busy period
                    slot_end = slot_start + datetime.timedelta(hours=duration_hours)
                    if slot_end <= busy_start and slot_end <= day_end:
                        free_slots.append({
                            'start': slot_start,
                            'end': slot_end,
                            'duration': duration_hours
                        })
                        slot_start = slot_start + datetime.timedelta(hours=1)  # Move to next hour
                    
                    slot_start = max(slot_start, busy_end)
                
                # Fill remaining slots until end of day
                while slot_start + datetime.timedelta(hours=duration_hours) <= day_end:
                    slot_end = slot_start + datetime.timedelta(hours=duration_hours)
                    free_slots.append({
                        'start': slot_start,
                        'end': slot_end,
                        'duration': duration_hours
                    })
                    slot_start = slot_start + datetime.timedelta(hours=1)  # Move to next hour
                
                current_date += datetime.timedelta(days=1)
            
            return free_slots
        
        except Exception as e:
            print(f"Error finding free time in range: {e}")
            return []
    
    def format_event_summary(self, event):
        """
        Format an event for display.
        
        Args:
            event (dict): Event object from Google Calendar API
        
        Returns:
            str: Formatted event summary
        """
        title = event.get('summary', 'No Title')
        
        start_str = event['start'].get('dateTime', event['start'].get('date'))
        end_str = event['end'].get('dateTime', event['end'].get('date'))
        
        start_time = parser.parse(start_str)
        end_time = parser.parse(end_str)
        
        # Format date and time
        if start_time.date() == end_time.date():
            date_str = start_time.strftime('%Y-%m-%d')
            time_str = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
        else:
            date_str = f"{start_time.strftime('%Y-%m-%d')} - {end_time.strftime('%Y-%m-%d')}"
            time_str = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
        
        location = event.get('location', '')
        location_str = f" @ {location}" if location else ""
        
        return f"{title}\n  {date_str} {time_str}{location_str}"

if __name__ == "__main__":
    # Test the calendar functions
    try:
        calendar = CalendarManager()
        
        print("Testing calendar functions...")
        
        # Test getting events
        print("\nUpcoming events:")
        events = calendar.get_events(max_results=5)
        for event in events:
            print(f"  {calendar.format_event_summary(event)}")
        
        # Test finding free time
        print("\nFinding free time slots:")
        free_slots = calendar.find_free_time(duration_hours=1, search_days=3)
        for slot in free_slots[:3]:
            print(f"  {slot['start'].strftime('%Y-%m-%d %I:%M %p')} - {slot['end'].strftime('%I:%M %p')}")
        
    except Exception as e:
        print(f"Error testing calendar functions: {e}")