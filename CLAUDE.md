# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Empire Familiar** is an intelligent agent-to-agent calendar coordination system that enables Claude Code agents to automatically negotiate and schedule meetings via email communication. The system integrates with multiple Google services and implements sophisticated coordination protocols.

**✅ Current Implemented Features:**
- 🤖 **Agent-to-Agent Coordination** - Automatic meeting negotiation between Claude agents
- 📧 **Gmail Email Threading** - Coordination conversations happen in organized email threads
- 📁 **Automatic Archiving** - Email threads archive automatically after successful scheduling
- 🎯 **3-Step Protocol** - Simplified coordination: Request → Availabilities → Selection
- 🧠 **Natural Language** - Human-readable coordination messages instead of machine code
- ⚡ **Real-time Processing** - Background email monitoring and auto-response

**Available Services:**
- 📅 **Google Calendar** - Schedule events, view calendar, find free time, conflict detection
- 📧 **Gmail** - Read emails, send messages, threading, archiving, search mail  
- 📄 **Google Docs** - Create documents, edit content, share docs
- ✅ **Google Tasks** - Create tasks, manage todo lists, track deadlines

## Development Environment Setup

### Virtual Environment
Always activate the virtual environment before running any Python commands:
```bash
source calendar_env/bin/activate
```

### Key Files
- `integrated_agent_coordination.py` - **Core agent coordination system** with email threading and protocols
- `coordination_helpers.py` - **Easy-to-use functions** for agent coordination 
- `agent_email_monitor.py` - **Background monitoring** for automatic email processing
- `gmail_functions.py` - Gmail operations with threading and archiving (GmailManager class)
- `integrated_assistant.py` - Multi-service interface with all Google services
- `calendar_functions.py` - Core Google Calendar API operations
- `docs_functions.py` - Google Docs operations (DocsManager class)  
- `tasks_functions.py` - Google Tasks operations
- `main.py` - Simple calendar-only interface (CalendarScheduler class)
- `auth.py` - OAuth authentication handling
- `credentials.json` - OAuth credentials (already configured)
- `token.json` - OAuth access token (auto-generated)

### Running Agent Coordination
```python
from coordination_helpers import setup_coordination_for_user, schedule_meeting_with_agent

# Setup your agent identity
setup_coordination_for_user("Your Name", "your@email.com")

# Schedule with another agent
schedule_meeting_with_agent("colleague@company.com", "Project Meeting", 60)
```

### Running the Integrated Assistant  
```python
from integrated_assistant import IntegratedGoogleAssistant
assistant = IntegratedGoogleAssistant()
```

## Natural Language Scheduling Rules

### Boundaries
1. **Morning Focus**: Do not allow the scheduler to schedule any events before 10 AM.
2. **Bedtime**: Do not allow the scheduler to schedule any events after 7 PM.
3. **Stranger**: Ask permission before allowing someone to schedule who has not scheduled with me before.

### Primary Functions

**🤖 Agent Coordination Operations:**
1. **Agent Setup**: `setup_coordination_for_user("Your Name", "your@email.com")`
2. **Schedule with Agent**: `schedule_meeting_with_agent(target_email, subject, duration_minutes)`
3. **Quick Sync**: `quick_15min_sync(email, subject)`
4. **Urgent Meeting**: `urgent_meeting(email, subject, duration_minutes)`
5. **Check Messages**: `check_and_respond_to_coordination()`
6. **Monitor Email**: `python3 agent_email_monitor.py monitor 120` (command line)

**📅 Calendar Operations:**
1. **Event Creation**: `assistant.schedule_event(description)`
2. **Schedule Viewing**: `assistant.get_schedule(time_period)`
3. **Free Time Finding**: `assistant.find_free_time(duration, when)`
4. **Event Management**: `assistant.cancel_event()`, `assistant.reschedule_event()`

**📧 Gmail Operations:**
1. **Read Emails**: `assistant.get_unread_emails(max_count)`
2. **Send Email**: `assistant.send_email(to_email, subject, body)`
3. **Reply to Email**: `assistant.reply_to_email(message_id, reply_text)`
4. **Search Emails**: `assistant.search_emails(search_query)`

**📄 Google Docs Operations:**
1. **Create Document**: `assistant.create_document(title, content)`
2. **Read Document**: `assistant.read_document(document_id)`
3. **Add to Document**: `assistant.add_to_document(document_id, text)`
4. **Share Document**: `assistant.share_document(document_id, email)`

**✅ Google Tasks Operations:**
1. **Create Task**: `assistant.create_task(title, notes, due_date)`
2. **Get Tasks**: `assistant.get_tasks(show_completed=False)`
3. **Complete Task**: `assistant.complete_task(task_id)`
4. **Search Tasks**: `assistant.search_tasks(search_query)`
5. **Get Due Today**: `assistant.get_tasks_due_today()`
6. **Get Overdue**: `assistant.get_overdue_tasks()`

### Natural Language Patterns
When processing user requests, recognize these patterns:

**Time Expressions**:
- "tomorrow at 2 PM"
- "next Tuesday at 10:30 AM" 
- "Friday at noon"
- "next week Monday at 9 AM"

**Duration Expressions**:
- "for 1 hour"
- "for 30 minutes" 
- "for 2.5 hours"

**Event Creation Patterns**:
- "Schedule a [event] [time]"
- "Book a [event] [time]"
- "Create a [event] [time]"
- "Add a [event] [time]"

## Usage Guidelines

### Event Scheduling
Always use natural language descriptions when creating events:
```python
# Good examples
scheduler.schedule_event("Schedule a team meeting tomorrow at 2 PM for 1 hour")
scheduler.schedule_event("Book a doctor appointment next Tuesday at 10:30 AM")
scheduler.schedule_event("Create a lunch meeting with Sarah on Friday at noon")
```

### Schedule Viewing
Use descriptive time periods:
```python
scheduler.get_schedule("today")
scheduler.get_schedule("tomorrow") 
scheduler.get_schedule("this week")
scheduler.get_schedule("next week")
```

### Finding Available Time
Specify duration and time frame:
```python
scheduler.find_available_time("1 hour", "this week")
scheduler.find_available_time("30 minutes", "today")
scheduler.find_available_time("2 hours", "next week")
```

## Response Patterns

### When User Asks to Schedule Something
1. Parse the natural language request
2. Use `scheduler.schedule_event()` with the full description
3. Confirm creation with event details
4. Show the calendar link if available

### When User Asks About Their Schedule
1. Use appropriate time period ("today", "tomorrow", "this week")
2. Format and present events clearly
3. Include times, titles, and locations

### When User Needs Available Time
1. Determine duration needed
2. Specify search period
3. Present options in user-friendly format
4. Offer to schedule if they choose a slot

## Error Handling

### Common Issues
- **Authentication errors**: Delete `token.json` and re-authenticate
- **Time parsing errors**: The system has fallbacks, but be explicit with times
- **API rate limits**: Implement delays between rapid requests

### Debugging
- Use `python auth.py` to test authentication
- Use `python calendar_functions.py` to test core functions
- Use `python example_usage.py` for full system test

## Security Guidelines

- Never expose or log the contents of `credentials.json` or `token.json`
- Don't commit authentication files to version control
- Keep OAuth tokens secure and don't share them

## Best Practices

### Conversational Flow
1. **Listen**: Parse user's natural language request
2. **Confirm**: Repeat back what you understood
3. **Execute**: Call appropriate scheduler function
4. **Report**: Confirm success and provide relevant details

### Time Zone Handling
- Default timezone is set to America/New_York
- Can be changed with `scheduler.calendar.set_timezone()`
- Always consider user's context when scheduling

### Event Details
- Extract titles, times, durations from natural language
- Look for location mentions (@, "in", "at")
- Check for attendee email addresses
- Add appropriate descriptions when helpful

## Example Interactions

### User: "Schedule a team meeting tomorrow at 2 PM"
```python
event = scheduler.schedule_event("Schedule a team meeting tomorrow at 2 PM")
if event:
    print(f"✅ Team meeting scheduled for tomorrow at 2 PM")
    print(f"Event link: {event.get('htmlLink', 'N/A')}")
```

### User: "What's on my calendar today?"
```python
events = scheduler.get_schedule("today")
if events:
    print(f"You have {len(events)} events today:")
    for event in events:
        print(f"  • {event['summary']}")
else:
    print("No events scheduled for today")
```

### User: "When am I free this week for a 1-hour meeting?"
```python
slots = scheduler.find_available_time("1 hour", "this week")
if slots:
    print("Available 1-hour slots this week:")
    for slot in slots[:5]:  # Show first 5
        print(f"  • {slot['start']} - {slot['end']}")
else:
    print("No 1-hour slots available this week")
```

## ✅ Agent-to-Agent Coordination (IMPLEMENTED)

### Current Implementation Status
The coordination system is **fully implemented and operational** with the following features:

**🎯 Core Features Complete:**
- ✅ **Natural Language Messages** - Human-readable coordination instead of machine code
- ✅ **Email Threading** - All coordination in Gmail reply threads  
- ✅ **Auto-Archiving** - Threads archived after successful meeting confirmation
- ✅ **3-Step Protocol** - Simplified coordination flow without artificial limits
- ✅ **Intelligent Scheduling** - Calendar conflicts, preferences, context awareness
- ✅ **Real-time Processing** - Background email monitoring and auto-response

### Universal Coordination System
The system supports **email-agnostic agent coordination** with any Claude Code agent:

**Setup your agent identity:**
```python
from coordination_helpers import setup_coordination_for_user

setup_coordination_for_user("Your Name", "your@email.com")
```

**Schedule with any agent:**
```python
from coordination_helpers import schedule_meeting_with_agent

# Coordinate with anyone by email
schedule_meeting_with_agent(
    target_email="colleague@company.com",
    meeting_subject="Project Planning", 
    duration_minutes=60
)
```

**Quick coordination functions:**
```python
from coordination_helpers import quick_15min_sync, urgent_meeting

quick_15min_sync("team@company.com", "Daily Standup")
urgent_meeting("manager@company.com", "Critical Issue", 45)
```

**Auto-respond to coordination requests:**
```bash
# Start email monitoring for auto-response
python3 agent_email_monitor.py monitor 120  # 2 hours
python3 agent_email_monitor.py monitor 0    # continuous
```

### Agent Coordination Commands
- "Schedule meeting with [email] using agent coordination"
- "Setup coordination for [name] with email [email]" 
- "Check for agent coordination messages"
- "Update my coordination context to heavy workload"

## Team Member Coordination Setup

### For Team Members Setting Up Coordination
If you're a team member setting up agent coordination with this system:

1. **See TEAM_MEMBER_SETUP.md** for complete setup instructions
2. **Required files to update:**
   - `integrated_agent_coordination.py` (critical bug fixes)
   - `agent_email_monitor.py` (monitoring system)
   - `coordination_helpers.py` (helper functions)

3. **Configure your agent identity:**
```python
from coordination_helpers import setup_coordination_for_user
setup_coordination_for_user("Your Name", "your@email.com")
```

4. **Test coordination:**
```python
from coordination_helpers import schedule_meeting_with_agent
schedule_meeting_with_agent("zach@empire.email", "Test Meeting", 30)
```

5. **Start monitoring:**
```bash
python3 agent_email_monitor.py monitor 60
```

### Coordination Protocol Flow
The full agent-to-agent coordination works as follows:
1. **Agent A** sends `SCHEDULE_REQUEST` to Agent B
2. **Agent B** checks calendar, responds with `SCHEDULE_PROPOSAL` (3 options)
3. **Agent A** evaluates and either confirms or sends `SCHEDULE_COUNTER_PROPOSAL`
4. **Negotiation continues** up to 4 rounds
5. **Final confirmation** creates calendar events on both sides

## Development Commands

### Testing
```bash
# Test authentication
python auth.py

# Test calendar functions  
python calendar_functions.py

# Test full system
python example_usage.py

# Test agent coordination
python integrated_agent_coordination.py

# Test helper functions
python coordination_helpers.py
```

### Virtual Environment Management
```bash
# Activate environment
source calendar_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

Remember: This system is designed to make Claude Code act as a natural, conversational calendar assistant. Always prioritize user-friendly interactions and clear confirmations of calendar actions.