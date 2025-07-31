# Empire Familiar - Agent Calendar Coordination System

An intelligent agent-to-agent calendar coordination system that enables Claude Code agents to automatically negotiate and schedule meetings via email communication.

## ✅ Current Features

### **Agent Coordination Protocol**
- **Natural Language Negotiations**: Agents communicate in clear, human-readable English instead of machine code
- **Email Threading**: All coordination happens in Gmail reply threads for organized conversation flow
- **Automatic Archiving**: Coordination emails are automatically archived after successful meeting confirmation
- **3-Step Simplified Protocol**: Request → All availabilities → Mutual selection or counter-proposals
- **Intelligent Scheduling**: Calendar conflict detection, time preferences, and context-aware suggestions

### **Multi-Service Integration**
- **Google Calendar**: Full calendar management and event creation
- **Gmail**: Email-based coordination with threading and archiving
- **Google Docs**: Document creation and sharing capabilities
- **Google Tasks**: Task management and deadline tracking

### **Smart Coordination**
- **Conflict Detection**: Real-time calendar checking to avoid scheduling conflicts
- **Time Preferences**: Respects morning/afternoon preferences and constraints
- **Context Awareness**: Considers workload and meeting types
- **Multi-Round Negotiation**: Intelligent counter-proposals when initial times don't work
- **Graceful Error Handling**: Continues coordination even if some operations fail

## Project Structure

```
empire-familiar/
├── integrated_agent_coordination.py  # Core agent coordination system
├── gmail_functions.py               # Gmail operations with threading
├── calendar_functions.py            # Google Calendar API operations  
├── docs_functions.py                # Google Docs integration
├── tasks_functions.py               # Google Tasks management
├── coordination_helpers.py          # Easy-to-use helper functions
├── agent_email_monitor.py          # Background email monitoring
├── auth.py                         # OAuth authentication handling
├── main.py                         # Simple calendar interface
├── integrated_assistant.py         # Multi-service assistant
├── requirements.txt                # Python dependencies
├── credentials.json                # OAuth credentials (you provide)
├── token.json                     # Generated OAuth token (auto-created)
├── CLAUDE.md                      # Claude Code integration instructions
└── README.md                      # This file
```

## Setup Instructions

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### 2. Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in the required fields (app name, user support email, etc.)
   - Add your email to test users
4. For application type, choose "Desktop application"
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place it in the project directory

### 3. Install Dependencies

```bash
cd empire-familiar
source calendar_env/bin/activate  # Activate virtual environment
pip install -r requirements.txt
```

### 4. First-Time Authentication

Run the authentication test to authorize the application:

```bash
python auth.py
```

This will:
- Open a browser window for Google OAuth authentication
- Ask you to authorize the application
- Save the access token for future use

## Usage with Claude Code

### Agent Coordination Setup

```python
from integrated_agent_coordination import initialize_integrated_coordination_system
from coordination_helpers import setup_coordination_for_user, schedule_meeting_with_agent

# Setup your agent identity
setup_coordination_for_user("Your Name", "your@email.com")

# Initialize the coordination system
coordinator = initialize_integrated_coordination_system()
```

### Agent-to-Agent Meeting Coordination

```python
# Schedule meeting with another agent
from coordination_helpers import schedule_meeting_with_agent

result = schedule_meeting_with_agent(
    target_email="colleague@company.com",
    meeting_subject="Project Planning Meeting", 
    duration_minutes=60
)

# Quick 15-minute sync
from coordination_helpers import quick_15min_sync
quick_15min_sync("team@company.com", "Daily Standup")

# Urgent meeting
from coordination_helpers import urgent_meeting
urgent_meeting("manager@company.com", "Critical Issue", 45)
```

### Basic Calendar Operations

```python
from main import CalendarScheduler

# Initialize the simple scheduler
scheduler = CalendarScheduler()

# Schedule a meeting manually
event = scheduler.schedule_event("Schedule a team meeting tomorrow at 2 PM for 1 hour")
```

### Viewing Your Schedule

```python
# Get today's schedule
events = scheduler.get_schedule("today")
for event in events:
    print(event['summary'])

# Get this week's schedule
events = scheduler.get_schedule("this week")

# Get tomorrow's schedule
events = scheduler.get_schedule("tomorrow")
```

### Finding Available Time

```python
# Find 1-hour slots this week
slots = scheduler.find_available_time("1 hour", "this week")
for slot in slots:
    print(f"Available: {slot['start']} - {slot['end']}")

# Find 30-minute slots today
slots = scheduler.find_available_time("30 minutes", "today")
```

### Managing Events

```python
# Cancel an event by title
success = scheduler.cancel_event("team meeting")

# Reschedule an event
updated_event = scheduler.reschedule_event("doctor appointment", "Thursday at 3 PM")
```

## Natural Language Examples

The scheduler understands various natural language patterns:

### Time Expressions
- "tomorrow at 2 PM"
- "next Tuesday at 10:30 AM"
- "Friday at noon"
- "today at 3:45 PM"
- "next week Monday at 9 AM"

### Duration Expressions
- "for 1 hour"
- "for 30 minutes"
- "for 2.5 hours"

### Event Types
- "Schedule a team meeting..."
- "Book a doctor appointment..."
- "Create a lunch meeting..."
- "Add a conference call..."

## Advanced Features

### Setting Timezone

```python
scheduler.calendar.set_timezone('America/Los_Angeles')
```

### Working with Specific Calendars

```python
# Create event in a specific calendar
event = scheduler.calendar.create_event(
    title="Personal Event",
    start_time="tomorrow at 6 PM",
    calendar_id="your-calendar-id@gmail.com"
)
```

### Adding Event Details

```python
# Create detailed event
event = scheduler.calendar.create_event(
    title="Project Review",
    start_time="next Monday at 10 AM",
    end_time="next Monday at 11 AM",
    description="Quarterly project review meeting",
    location="Conference Room A",
    attendees=["colleague@example.com", "manager@example.com"]
)
```

## Error Handling

The scheduler includes robust error handling:

- **Authentication Errors**: Automatically handles token refresh
- **API Errors**: Graceful handling of Google Calendar API errors
- **Parsing Errors**: Fallback to default values for unparseable dates
- **Network Errors**: Retry mechanisms for temporary failures

## Security Notes

- **Credentials**: Keep your `credentials.json` file secure and never commit it to version control
- **Token Storage**: The `token.json` file contains your access token - keep it private
- **Scopes**: The application only requests calendar access (read/write) permissions

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**
   - Make sure `credentials.json` is in the project directory
   - Verify the file was downloaded correctly from Google Cloud Console

2. **"Authentication failed"**
   - Delete `token.json` and re-run authentication
   - Check that the Google Calendar API is enabled in your project

3. **"Access denied"**
   - Verify your OAuth consent screen is configured
   - Make sure your email is added as a test user

4. **"Invalid time format"**
   - The scheduler tries to parse natural language, but may need more specific time formats
   - Try using more explicit time descriptions

### Testing Authentication

```bash
# Test authentication
python auth.py

# Test calendar functions
python calendar_functions.py

# Test main interface
python main.py
```

## 🤖 Agent Coordination in Action

### Email Monitoring for Auto-Response

```bash
# Start monitoring for incoming coordination requests (continuous)
python3 agent_email_monitor.py monitor 0

# Monitor for 2 hours
python3 agent_email_monitor.py monitor 120

# Quick check for new messages
python3 agent_email_monitor.py quick
```

### Multi-Service Integration

```python
from integrated_assistant import IntegratedGoogleAssistant

# Initialize full service integration
assistant = IntegratedGoogleAssistant()

# Calendar operations
assistant.schedule_event("Team standup tomorrow at 9 AM")
assistant.get_schedule("today")

# Email operations
assistant.get_unread_emails(5)
assistant.send_email("colleague@company.com", "Meeting Follow-up", "Thanks for the meeting!")

# Document operations
assistant.create_document("Meeting Notes", "Discussion points...")

# Task management
assistant.create_task("Review project proposal", due_date="Friday")
```

## 🔄 How Agent Coordination Works

1. **Agent A** sends coordination request via email to **Agent B**
2. **Agent B** automatically processes request and responds with available times
3. **Negotiation** continues until mutual time is found or alternatives exhausted
4. **Calendar events** created automatically for both agents when confirmed
5. **Email thread** automatically archived to keep inboxes clean

All coordination happens in clear, human-readable language that can be easily followed and understood.

## Contributing

Feel free to improve the natural language parsing, add new features, or fix bugs. The codebase is modular and well-documented for easy modification. Please see our [Contributing Guidelines](CONTRIBUTING.md) for the best way to suggest features and contribute to the project.

## License

This project is for personal use. Make sure to comply with Google's API Terms of Service when using their Calendar API.