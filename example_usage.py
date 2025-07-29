"""
Example usage of the Google Calendar Scheduler

This file demonstrates how Claude Code can use the calendar scheduler
to manage events with natural language commands.
"""

from main import CalendarScheduler

def demonstrate_scheduler():
    """Demonstrate the calendar scheduler functionality."""
    
    print("Google Calendar Scheduler - Example Usage")
    print("=" * 50)
    
    try:
        # Initialize the scheduler
        print("Initializing scheduler...")
        scheduler = CalendarScheduler()
        
        print("\n1. SCHEDULING EVENTS")
        print("-" * 30)
        
        # Example 1: Schedule a team meeting
        print("Scheduling: 'Schedule a team meeting tomorrow at 2 PM'")
        # event = scheduler.schedule_event("Schedule a team meeting tomorrow at 2 PM")
        # Commented out to avoid creating actual events during demo
        
        # Example 2: Book an appointment  
        print("Scheduling: 'Book a doctor appointment next Tuesday at 10:30 AM'")
        # event = scheduler.schedule_event("Book a doctor appointment next Tuesday at 10:30 AM")
        
        print("\n2. VIEWING SCHEDULE")
        print("-" * 30)
        
        # Get today's schedule
        print("Getting today's schedule...")
        events = scheduler.get_schedule("today")
        print(f"Found {len(events)} events for today")
        
        for event in events[:3]:  # Show first 3 events
            print(f"  • {event['summary']}")
        
        print("\n3. FINDING AVAILABLE TIME")
        print("-" * 30)
        
        # Find available slots
        print("Finding 1-hour slots this week...")
        slots = scheduler.find_available_time("1 hour", "this week")
        print(f"Found {len(slots)} available slots")
        
        for slot in slots[:3]:  # Show first 3 slots
            print(f"  • {slot['start']} - {slot['end']}")
        
        print("\n4. NATURAL LANGUAGE EXAMPLES")
        print("-" * 30)
        
        examples = [
            "Schedule a team standup tomorrow at 9 AM for 30 minutes",
            "Book a client call next Friday at 3 PM",
            "Create a lunch meeting with Sarah on Thursday at noon",
            "Add a project review next Monday at 10 AM for 2 hours",
            "Schedule a doctor appointment next week Wednesday at 2:30 PM"
        ]
        
        print("Example commands you can use:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. scheduler.schedule_event('{example}')")
        
        print("\n✅ Scheduler is ready for use!")
        return scheduler
        
    except FileNotFoundError:
        print("\n❌ Setup Required:")
        print("1. Download OAuth credentials from Google Cloud Console")
        print("2. Save as 'credentials.json' in this directory")
        print("3. Run: pip install -r requirements.txt")
        print("4. Run this example again")
        return None
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Check the README.md for troubleshooting steps")
        return None

def quick_test_commands():
    """Show quick test commands for Claude Code to use."""
    
    print("\nQUICK TEST COMMANDS FOR CLAUDE CODE:")
    print("=" * 50)
    
    commands = [
        "# Import the scheduler",
        "from main import CalendarScheduler",
        "scheduler = CalendarScheduler()",
        "",
        "# Schedule events",
        "scheduler.schedule_event('Schedule a team meeting tomorrow at 2 PM')",
        "scheduler.schedule_event('Book lunch with John next Friday at noon')",
        "",
        "# View schedule", 
        "events = scheduler.get_schedule('today')",
        "for event in events: print(event['summary'])",
        "",
        "# Find free time",
        "slots = scheduler.find_available_time('1 hour', 'this week')",
        "for slot in slots[:3]: print(slot['start'])",
        "",
        "# Cancel/reschedule",
        "scheduler.cancel_event('team meeting')",
        "scheduler.reschedule_event('lunch', 'next Monday at 1 PM')"
    ]
    
    for command in commands:
        print(command)

if __name__ == "__main__":
    # Run the demonstration
    scheduler = demonstrate_scheduler()
    
    if scheduler:
        print("\n" + "=" * 50)
        quick_test_commands()
    
    print(f"\n📁 Project location: /Users/home/google-calendar-scheduler")
    print("📖 See README.md for complete setup instructions")