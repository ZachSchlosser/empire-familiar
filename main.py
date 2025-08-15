"""
Google Calendar Scheduler - Natural Language Interface

This is the main interface for the Google Calendar scheduler that Claude Code
can use to manage calendar events using natural language commands.
"""

import re
import datetime
from calendar_functions import CalendarManager

class CalendarScheduler:
    """Natural language interface for Google Calendar scheduling."""
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Initialize the CalendarScheduler.
        
        Args:
            credentials_file (str): Path to OAuth credentials file
        """
        self.calendar = CalendarManager(credentials_file)
        print("Calendar Scheduler initialized successfully!")
    
    def schedule_event(self, description):
        """
        Schedule an event from natural language description.
        
        Args:
            description (str): Natural language event description
                Examples:
                - "Schedule a team meeting tomorrow at 2 PM for 1 hour"
                - "Book a doctor appointment next Tuesday at 10:30 AM"
                - "Create a lunch meeting with John on Friday at noon"
        
        Returns:
            dict: Created event information or None if failed
        """
        print(f"Processing request: {description}")
        
        # Extract event components from description
        title = self._extract_title(description)
        start_time = self._extract_start_time(description)
        duration = self._extract_duration(description)
        location = self._extract_location(description)
        attendees = self._extract_attendees(description)
        recurrence = self.calendar.parse_recurrence_rule(description)
        
        if start_time is None:
            print("Could not determine start time from description")
            return None
        
        # Calculate end time
        end_time = start_time + datetime.timedelta(hours=duration)
        
        if recurrence:
            print(f"Creating recurring event: '{title}' from {start_time} to {end_time}")
            print(f"Recurrence rule: {recurrence}")
        else:
            print(f"Creating event: '{title}' from {start_time} to {end_time}")
        
        return self.calendar.create_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            location=location,
            attendees=attendees,
            recurrence=recurrence,
            enforce_boundaries=True  # Enforce 10am-7pm boundaries by default
        )
    
    def get_schedule(self, time_description="today"):
        """
        Get schedule for a specified time period.
        
        Args:
            time_description (str): Time period description
                Examples: "today", "tomorrow", "this week", "next week"
        
        Returns:
            list: List of events with formatted summaries
        """
        print(f"Getting schedule for: {time_description}")
        
        time_min, time_max = self._parse_time_range(time_description)
        events = self.calendar.get_events(time_min=time_min, time_max=time_max, max_results=20)
        
        if not events:
            print(f"No events found for {time_description}")
            return []
        
        formatted_events = []
        for event in events:
            formatted_events.append({
                'summary': self.calendar.format_event_summary(event),
                'id': event['id'],
                'raw': event
            })
        
        print(f"Found {len(formatted_events)} events for {time_description}")
        return formatted_events
    
    def find_available_time(self, duration_description="1 hour", when="this week"):
        """
        Find available time slots.
        
        Args:
            duration_description (str): Duration needed (e.g., "1 hour", "30 minutes", "2 hours")
            when (str): When to search (e.g., "this week", "next week", "today", "August 18-24, 2025")
        
        Returns:
            list: Available time slots
        """
        print(f"Finding {duration_description} slots for {when}")
        
        duration_hours = self._parse_duration(duration_description)
        search_info = self._parse_search_days(when)
        
        # Handle date range vs. relative days
        if isinstance(search_info, dict) and search_info.get('type') == 'date_range':
            # Use specific date range
            start_date = search_info['start_date']
            end_date = search_info['end_date']
            
            free_slots = self.calendar.find_free_time_in_range(
                duration_hours=duration_hours,
                start_date=start_date,
                end_date=end_date
            )
        else:
            # Use relative search from now
            free_slots = self.calendar.find_free_time(
                duration_hours=duration_hours,
                search_days=search_info
            )
        
        formatted_slots = []
        for slot in free_slots:
            formatted_slots.append({
                'start': slot['start'].strftime('%A, %B %d at %I:%M %p'),
                'end': slot['end'].strftime('%I:%M %p'),
                'datetime': slot['start'],
                'duration': slot['duration']
            })
        
        print(f"Found {len(formatted_slots)} available slots")
        return formatted_slots
    
    def cancel_event(self, event_identifier):
        """
        Cancel an event by title or ID.
        
        Args:
            event_identifier (str): Event title or ID to cancel
        
        Returns:
            bool: True if cancelled successfully
        """
        print(f"Attempting to cancel event: {event_identifier}")
        
        # If it looks like an event ID, use it directly
        if len(event_identifier) > 20 and '_' in event_identifier:
            return self.calendar.delete_event(event_identifier)
        
        # Otherwise, search for events with matching title
        events = self.calendar.get_events(max_results=50)
        for event in events:
            if event_identifier.lower() in event.get('summary', '').lower():
                print(f"Found matching event: {event.get('summary')}")
                return self.calendar.delete_event(event['id'])
        
        print(f"No event found matching: {event_identifier}")
        return False
    
    def reschedule_event(self, event_identifier, new_time_description):
        """
        Reschedule an existing event.
        
        Args:
            event_identifier (str): Event title or ID to reschedule
            new_time_description (str): New time description
        
        Returns:
            dict: Updated event information or None if failed
        """
        print(f"Rescheduling '{event_identifier}' to '{new_time_description}'")
        
        new_start_time = self._extract_start_time(new_time_description)
        if not new_start_time:
            print("Could not parse new time")
            return None
        
        # Find the event
        events = self.calendar.get_events(max_results=50)
        for event in events:
            if (event_identifier.lower() in event.get('summary', '').lower() or 
                event_identifier == event['id']):
                
                print(f"Found event to reschedule: {event.get('summary')}")
                
                # Calculate new end time (keep same duration)
                original_start = self.calendar.parse_datetime(
                    event['start'].get('dateTime', event['start'].get('date'))
                )
                original_end = self.calendar.parse_datetime(
                    event['end'].get('dateTime', event['end'].get('date'))
                )
                duration = original_end - original_start
                new_end_time = new_start_time + duration
                
                return self.calendar.update_event(
                    event_id=event['id'],
                    start_time=new_start_time,
                    end_time=new_end_time
                )
        
        print(f"No event found matching: {event_identifier}")
        return None
    
    def _extract_title(self, description):
        """Extract event title from description."""
        # Common patterns for event titles
        patterns = [
            r'schedule\s+(?:a\s+)?(.+?)\s+(?:at|on|for|tomorrow|today|next)',
            r'book\s+(?:a\s+)?(.+?)\s+(?:at|on|for|tomorrow|today|next)',
            r'create\s+(?:a\s+)?(.+?)\s+(?:at|on|for|tomorrow|today|next)',
            r'add\s+(?:a\s+)?(.+?)\s+(?:at|on|for|tomorrow|today|next)',
        ]
        
        description_lower = description.lower()
        
        for pattern in patterns:
            match = re.search(pattern, description_lower, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up the title
                title = re.sub(r'\s+', ' ', title)
                return title.title()
        
        # Fallback: use first few words
        words = description.split()
        if len(words) >= 3:
            return ' '.join(words[1:4]).title()
        
        return "New Event"
    
    def _extract_start_time(self, description):
        """Extract start time from description."""
        try:
            return self.calendar.parse_datetime(description)
        except:
            return None
    
    def _extract_duration(self, description):
        """Extract duration from description (returns hours as float)."""
        description_lower = description.lower()
        
        # Look for explicit duration
        hour_match = re.search(r'(\d+(?:\.\d+)?)\s*hours?', description_lower)
        if hour_match:
            return float(hour_match.group(1))
        
        minute_match = re.search(r'(\d+)\s*minutes?', description_lower)
        if minute_match:
            return float(minute_match.group(1)) / 60
        
        # Look for "for X hour" pattern
        for_pattern = re.search(r'for\s+(\d+(?:\.\d+)?)\s*hours?', description_lower)
        if for_pattern:
            return float(for_pattern.group(1))
        
        # Default duration
        return 1.0
    
    def _extract_location(self, description):
        """Extract location from description."""
        location_patterns = [
            r'at\s+([^,]+(?:room|office|building|street|avenue|drive|lane))',
            r'in\s+([^,]+(?:room|office|building|conference))',
            r'@\s+([^,\s]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_attendees(self, description):
        """Extract attendee emails from description."""
        # Look for email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, description)
        return emails if emails else None
    
    def _parse_time_range(self, time_description):
        """Parse time range from description."""
        now = datetime.datetime.now(self.calendar.timezone)
        
        if time_description.lower() == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + datetime.timedelta(days=1)
        elif time_description.lower() == "tomorrow":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            end = start + datetime.timedelta(days=1)
        elif "this week" in time_description.lower():
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=days_since_monday)
            end = start + datetime.timedelta(days=7)
        elif "next week" in time_description.lower():
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=days_since_monday) + datetime.timedelta(days=7)
            end = start + datetime.timedelta(days=7)
        else:
            # Default to next 7 days
            start = now
            end = now + datetime.timedelta(days=7)
        
        return start, end
    
    def _parse_duration(self, duration_description):
        """Parse duration from description and return hours."""
        description_lower = duration_description.lower()
        
        if "hour" in description_lower:
            match = re.search(r'(\d+(?:\.\d+)?)', description_lower)
            return float(match.group(1)) if match else 1.0
        elif "minute" in description_lower:
            match = re.search(r'(\d+)', description_lower)
            return float(match.group(1)) / 60 if match else 1.0
        
        return 1.0  # Default 1 hour
    
    def _parse_search_days(self, when_description):
        """Parse search period and return number of days or specific date range."""
        import re
        from dateutil import parser
        
        when_lower = when_description.lower()
        
        # Handle specific date ranges like "August 18-24, 2025" or "the week of August 18"
        if re.search(r'\b\d{4}\b', when_description) or re.search(r'august|september|october|november|december|january|february|march|april|may|june|july', when_lower):
            try:
                # Pattern for "August 18-24, 2025" or "August 18-24"
                date_range_match = re.search(r'(\w+)\s+(\d+)-(\d+),?\s*(\d{4})?', when_description)
                if date_range_match:
                    month_name, start_day, end_day, year = date_range_match.groups()
                    year = int(year) if year else datetime.datetime.now().year
                    
                    # Parse start and end dates
                    start_date_str = f"{month_name} {start_day}, {year}"
                    end_date_str = f"{month_name} {end_day}, {year}"
                    
                    start_date = parser.parse(start_date_str).date()
                    end_date = parser.parse(end_date_str).date()
                    
                    return {'type': 'date_range', 'start_date': start_date, 'end_date': end_date}
                
                # Pattern for "the week of August 18" 
                week_match = re.search(r'week of (\w+ \d+),?\s*(\d{4})?', when_description)
                if week_match:
                    date_part, year = week_match.groups()
                    year = int(year) if year else datetime.datetime.now().year
                    
                    # Parse the date and find the Monday of that week
                    ref_date = parser.parse(f"{date_part}, {year}").date()
                    monday = ref_date - datetime.timedelta(days=ref_date.weekday())
                    sunday = monday + datetime.timedelta(days=6)
                    
                    return {'type': 'date_range', 'start_date': monday, 'end_date': sunday}
                    
            except Exception as e:
                print(f"Error parsing date range '{when_description}': {e}")
                # Fall through to relative date logic
        
        # Handle relative dates
        if "today" in when_lower:
            return 1
        elif "this week" in when_lower:
            return 7
        elif "next week" in when_lower:
            return 7
        elif "month" in when_lower:
            return 30
        
        return 7  # Default 1 week

def main():
    """Main function for testing the scheduler directly."""
    try:
        scheduler = CalendarScheduler()
        
        print("\nGoogle Calendar Scheduler is ready!")
        print("You can now use natural language to manage your calendar.")
        print("\nExample commands:")
        print("- scheduler.schedule_event('Schedule a team meeting tomorrow at 2 PM')")
        print("- scheduler.get_schedule('today')")
        print("- scheduler.find_available_time('1 hour', 'this week')")
        
        return scheduler
        
    except FileNotFoundError:
        print("\nSetup required:")
        print("1. Download your OAuth credentials from Google Cloud Console")
        print("2. Save as 'credentials.json' in this directory")
        print("3. Run the scheduler again")
        return None
    except Exception as e:
        print(f"Error initializing scheduler: {e}")
        return None

if __name__ == "__main__":
    main()