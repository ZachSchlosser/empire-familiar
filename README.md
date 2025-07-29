# Google Calendar Scheduler

A natural language interface for Google Calendar that allows Claude Code to schedule and manage calendar events using conversational commands.

## Features

- **Natural Language Scheduling**: Create events using natural language descriptions
- **Smart Time Parsing**: Understands relative dates like "tomorrow", "next Tuesday", "next week"
- **Event Management**: Create, view, update, and delete calendar events
- **Free Time Finding**: Automatically find available time slots in your calendar
- **Conflict Detection**: Avoid scheduling conflicts by checking existing events
- **Multiple Calendars**: Support for accessing multiple Google calendars

## Project Structure

```
google-calendar-scheduler/
├── main.py                 # Main natural language interface
├── calendar_functions.py   # Core calendar operations
├── auth.py                 # OAuth authentication handling
├── requirements.txt        # Python dependencies
├── credentials.json        # Your OAuth credentials (you provide)
├── token.json             # Generated OAuth token (auto-created)
└── README.md              # This file
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
cd google-calendar-scheduler
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

### Basic Setup

```python
from main import CalendarScheduler

# Initialize the scheduler
scheduler = CalendarScheduler()
```

### Scheduling Events

```python
# Schedule a meeting
event = scheduler.schedule_event("Schedule a team meeting tomorrow at 2 PM for 1 hour")

# Book an appointment
event = scheduler.schedule_event("Book a doctor appointment next Tuesday at 10:30 AM")

# Create a lunch meeting
event = scheduler.schedule_event("Create a lunch meeting with John on Friday at noon")
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

## Contributing

Feel free to improve the natural language parsing, add new features, or fix bugs. The codebase is modular and well-documented for easy modification.

## License

This project is for personal use. Make sure to comply with Google's API Terms of Service when using their Calendar API.