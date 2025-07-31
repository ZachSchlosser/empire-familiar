#!/usr/bin/env python3
"""
Coordination Helper Functions
Email-agnostic coordination functions for easy use
"""

from typing import Dict, Any, List, Optional
from integrated_agent_coordination import (
    initialize_integrated_coordination_system,
    coordinate_intelligent_meeting,
    process_agent_coordination_messages,
    get_coordination_system_status,
    update_coordination_context
)
from agent_config import get_agent_config, setup_agent_for_user

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
                               attendees: List[str] = None) -> Dict[str, Any]:
    """Schedule meeting with any agent by email address"""
    
    # Ensure system is initialized
    if _current_config is None:
        coordinator = initialize_integrated_coordination_system()
        current_user = coordinator.agent_identity.user_name
        current_email = coordinator.agent_identity.user_email
    else:
        coordinator = initialize_integrated_coordination_system(_current_config)
        current_user = _current_config["user_name"]
        current_email = _current_config["user_email"]
    
    success = coordinate_intelligent_meeting(
        target_agent_email=target_email,
        meeting_subject=meeting_subject,
        duration_minutes=duration_minutes,
        meeting_type=meeting_type,
        attendees=attendees
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