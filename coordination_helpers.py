#!/usr/bin/env python3
"""
Coordination Helper Functions
Email-agnostic coordination functions for easy use
"""

from typing import Dict, Any, List, Optional
import logging
import re
from datetime import datetime, timedelta
from integrated_agent_coordination import (
    initialize_integrated_coordination_system,
    coordinate_intelligent_meeting,
    process_agent_coordination_messages,
    get_coordination_system_status,
    update_coordination_context
)
from agent_config import get_agent_config, setup_agent_for_user

# Setup logging
logger = logging.getLogger(__name__)

def parse_natural_language_date_range(date_range: str) -> Optional[Dict[str, str]]:
    """
    Parse natural language date expressions into preferred_dates dictionary
    
    Args:
        date_range: Natural language date expression like "the week of August 18", "next week", etc.
        
    Returns:
        Dict with 'start_date' and 'end_date' keys in ISO format, or None if parsing fails
    """
    if not date_range or not isinstance(date_range, str):
        return None
    
    date_range = date_range.lower().strip()
    now = datetime.now()
    
    try:
        # Pattern: "the week of [date]" or "week of [date]"
        week_of_match = re.search(r'(?:the\s+)?week\s+of\s+(\w+\s+\d{1,2})', date_range)
        if week_of_match:
            date_str = week_of_match.group(1)
            # Parse "august 18" type expressions
            month_day_match = re.match(r'(\w+)\s+(\d{1,2})', date_str)
            if month_day_match:
                month_name = month_day_match.group(1)
                day = int(month_day_match.group(2))
                
                # Map month names to numbers
                months = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
                    'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                    'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                }
                
                if month_name in months:
                    # Use current year, or next year if the date has passed
                    year = now.year
                    target_date = datetime(year, months[month_name], day)
                    if target_date < now:
                        target_date = datetime(year + 1, months[month_name], day)
                    
                    # Find the Monday of that week
                    days_to_monday = target_date.weekday()  # 0=Monday, 6=Sunday
                    start_of_week = target_date - timedelta(days=days_to_monday)
                    end_of_week = start_of_week + timedelta(days=6)  # Sunday
                    
                    logger.info(f"Parsed '{date_range}' as week from {start_of_week.date()} to {end_of_week.date()}")
                    
                    return {
                        'start_date': start_of_week.strftime('%Y-%m-%d'),
                        'end_date': end_of_week.strftime('%Y-%m-%d')
                    }
        
        # Pattern: "next week"
        if 'next week' in date_range:
            # Find next Monday
            days_until_next_monday = 7 - now.weekday()
            if days_until_next_monday == 7:  # If today is Sunday
                days_until_next_monday = 1
            next_monday = now + timedelta(days=days_until_next_monday)
            next_sunday = next_monday + timedelta(days=6)
            
            logger.info(f"Parsed '{date_range}' as next week from {next_monday.date()} to {next_sunday.date()}")
            
            return {
                'start_date': next_monday.strftime('%Y-%m-%d'),
                'end_date': next_sunday.strftime('%Y-%m-%d')
            }
        
        # Pattern: "this week"
        if 'this week' in date_range:
            # Find this Monday
            days_since_monday = now.weekday()  # 0=Monday, 6=Sunday
            this_monday = now - timedelta(days=days_since_monday)
            this_sunday = this_monday + timedelta(days=6)
            
            logger.info(f"Parsed '{date_range}' as this week from {this_monday.date()} to {this_sunday.date()}")
            
            return {
                'start_date': this_monday.strftime('%Y-%m-%d'),
                'end_date': this_sunday.strftime('%Y-%m-%d')
            }
        
        # Pattern: "tomorrow"
        if 'tomorrow' in date_range:
            tomorrow = now + timedelta(days=1)
            logger.info(f"Parsed '{date_range}' as tomorrow: {tomorrow.date()}")
            
            return {
                'start_date': tomorrow.strftime('%Y-%m-%d'),
                'end_date': tomorrow.strftime('%Y-%m-%d')
            }
        
        # Pattern: "today"
        if 'today' in date_range:
            logger.info(f"Parsed '{date_range}' as today: {now.date()}")
            
            return {
                'start_date': now.strftime('%Y-%m-%d'),
                'end_date': now.strftime('%Y-%m-%d')
            }
        
        # If we can't parse it, log and return None
        logger.warning(f"Could not parse date range: '{date_range}'. Supported formats: 'the week of August 18', 'next week', 'this week', 'tomorrow', 'today'")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing date range '{date_range}': {e}")
        return None

# Global coordination system with config
_current_config = None

def setup_coordination_for_user(user_name: str, user_email: str, 
                               agent_id: str = None, config_name: str = None) -> Dict[str, Any]:
    """Setup coordination system for a specific user"""
    global _current_config
    
    if config_name:
        # Use predefined configuration
        _current_config = get_agent_config(config_name)
    else:
        # Create custom configuration
        _current_config = setup_agent_for_user(user_name, user_email, agent_id)
    
    # Initialize system with this config
    coordinator = initialize_integrated_coordination_system(_current_config)
    
    return {
        "setup_complete": True,
        "agent_id": coordinator.agent_identity.agent_id,
        "user_name": coordinator.agent_identity.user_name,
        "user_email": coordinator.agent_identity.user_email,
        "configuration": _current_config
    }

def schedule_meeting_with_agent(target_email: str, meeting_subject: str, 
                               duration_minutes: int = 30, meeting_type: str = "1:1", 
                               attendees: List[str] = None, time_preference: str = None,
                               description: str = None, date_range: str = None) -> Dict[str, Any]:
    """Schedule meeting with any agent by email address
    
    Args:
        target_email: Email address of target agent
        meeting_subject: Subject of the meeting
        duration_minutes: Duration in minutes (default: 30)
        meeting_type: Type of meeting (default: "1:1")
        attendees: List of attendee emails (default: sender and target)
        time_preference: Time of day preference like "morning", "afternoon"
        description: Meeting description (optional)
        date_range: Natural language date range like "the week of August 11" (optional)
    
    Note: For natural language date ranges (like "the week of August 11"), 
    the Claude agent should parse this into structured date information before
    calling this function. The date_range parameter is stored in the meeting
    context for reference but not automatically parsed by the system.
    """
    
    # Ensure system is initialized
    if _current_config is None:
        coordinator = initialize_integrated_coordination_system()
        current_user = coordinator.agent_identity.user_name
        current_email = coordinator.agent_identity.user_email
    else:
        coordinator = initialize_integrated_coordination_system(_current_config)
        current_user = _current_config["user_name"]
        current_email = _current_config["user_email"]
    
    # If date_range is provided, include it in the description for context
    enhanced_description = description or ""
    if date_range:
        if enhanced_description:
            enhanced_description = f"{enhanced_description}\n\nRequested timeframe: {date_range}"
        else:
            enhanced_description = f"Requested timeframe: {date_range}"
    
    # Parse natural language date range into structured preferred_dates
    preferred_dates = None
    if date_range:
        preferred_dates = parse_natural_language_date_range(date_range)
        if preferred_dates:
            logger.info(f"Successfully parsed date range '{date_range}' into preferred_dates: {preferred_dates}")
        else:
            logger.warning(f"Failed to parse date range '{date_range}', proceeding without date constraints")
    
    success = coordinate_intelligent_meeting(
        target_agent_email=target_email,
        meeting_subject=meeting_subject,
        duration_minutes=duration_minutes,
        meeting_type=meeting_type,
        attendees=attendees,
        time_preference=time_preference,
        description=enhanced_description,
        preferred_dates=preferred_dates
    )
    
    return {
        "coordination_initiated": success,
        "from_agent": current_user,
        "from_email": current_email,
        "to_email": target_email,
        "meeting_subject": meeting_subject,
        "duration_minutes": duration_minutes,
        "next_steps": [
            f"Coordination message sent to {target_email}",
            "Target agent will analyze request and respond",
            "Both agents will negotiate optimal meeting time",
            "Calendar event will be created when confirmed"
        ] if success else ["Failed to send coordination message"]
    }

def check_and_respond_to_coordination() -> Dict[str, Any]:
    """Check for and respond to incoming coordination messages"""
    
    # Ensure system is initialized
    if _current_config:
        initialize_integrated_coordination_system(_current_config)
    
    results = process_agent_coordination_messages()
    
    return {
        "messages_processed": len(results),
        "processing_results": results,
        "timestamp": None,  # Will be added by the function
        "auto_responses_sent": sum(1 for r in results if r.get("response_sent", False))
    }

def get_my_coordination_status() -> Dict[str, Any]:
    """Get current coordination system status"""
    
    # Ensure system is initialized
    if _current_config:
        initialize_integrated_coordination_system(_current_config)
    
    status = get_coordination_system_status()
    
    return {
        "system_status": status,
        "configuration": _current_config,
        "ready_for_coordination": True
    }

def update_my_context(workload: str = None, energy: str = None, 
                     meetings_today: int = None) -> Dict[str, Any]:
    """Update coordination context for better scheduling"""
    
    # Ensure system is initialized  
    if _current_config:
        initialize_integrated_coordination_system(_current_config)
    
    return update_coordination_context(workload, energy, meetings_today)

# Convenience functions for common scenarios
def schedule_with_sarah(meeting_subject: str, duration_minutes: int = 30) -> Dict[str, Any]:
    """Schedule meeting with Sarah (example)"""
    return schedule_meeting_with_agent(
        target_email="sarah@empire.email",
        meeting_subject=meeting_subject,
        duration_minutes=duration_minutes
    )

def schedule_with_team_member(email: str, meeting_subject: str, 
                             duration_minutes: int = 30) -> Dict[str, Any]:
    """Schedule meeting with any team member"""
    return schedule_meeting_with_agent(
        target_email=email,
        meeting_subject=meeting_subject,  
        duration_minutes=duration_minutes,
        meeting_type="team_meeting"
    )

def quick_15min_sync(email: str, subject: str = "Quick Sync") -> Dict[str, Any]:
    """Schedule quick 15-minute sync meeting"""
    return schedule_meeting_with_agent(
        target_email=email,
        meeting_subject=subject,
        duration_minutes=15,
        meeting_type="sync"
    )

def urgent_meeting(email: str, subject: str, duration_minutes: int = 30) -> Dict[str, Any]:
    """Schedule urgent meeting"""
    return schedule_meeting_with_agent(
        target_email=email,
        meeting_subject=subject,
        duration_minutes=duration_minutes,
        meeting_type="urgent_meeting"
    )

# Email contact directory (can be extended)
CONTACT_DIRECTORY = {
    "sarah": "sarah@empire.email",
    "zach": "zach@empire.email",
    # Add more contacts as needed
}

def schedule_with_contact(contact_name: str, meeting_subject: str, 
                         duration_minutes: int = 30) -> Dict[str, Any]:
    """Schedule meeting using contact name instead of email"""
    
    email = CONTACT_DIRECTORY.get(contact_name.lower())
    if not email:
        return {
            "coordination_initiated": False,
            "error": f"Contact '{contact_name}' not found in directory",
            "available_contacts": list(CONTACT_DIRECTORY.keys())
        }
    
    return schedule_meeting_with_agent(
        target_email=email,
        meeting_subject=meeting_subject,
        duration_minutes=duration_minutes
    )

if __name__ == "__main__":
    # Test the helper functions
    print("🤝 Coordination Helper System Test")
    print("=" * 45)
    
    # Setup for test user
    setup_result = setup_coordination_for_user(
        user_name="Test User",
        user_email="test@example.com"
    )
    print(f"✅ Setup complete: {setup_result['agent_id']}")
    
    # Test scheduling
    result = schedule_meeting_with_agent(
        target_email="colleague@example.com",
        meeting_subject="Test Meeting",
        duration_minutes=30
    )
    print(f"✅ Meeting coordination: {result['coordination_initiated']}")
    
    # Test status
    status = get_my_coordination_status()
    print(f"✅ System status: {status['system_status']['status']}")
    
    print("\n🎯 Helper system ready for use!")
    
    print("\nExample usage:")
    print("# Setup for your identity")
    print("setup_coordination_for_user('Your Name', 'your@email.com')")
    print("\n# Schedule with anyone") 
    print("schedule_meeting_with_agent('colleague@company.com', 'Project Sync')")
    print("\n# Use contact names")
    print("schedule_with_contact('sarah', 'Weekly Planning')")
    print("\n# Quick meetings")
    print("quick_15min_sync('team@company.com', 'Daily Standup')")