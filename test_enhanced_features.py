#!/usr/bin/env python3
"""
Test script to verify enhanced calendar features (Issues #4 and #15)
This tests:
- Enhanced title generation with participants and meeting type
- Link extraction from coordination messages
- Rich description with all sections
"""

import logging
from datetime import datetime, timedelta
from integrated_agent_coordination import IntegratedCoordinationProtocol, MessageType, CoordinationMessage, MeetingContext, TimeSlot, AgentIdentity, SchedulingPreferences
from dataclasses import dataclass

# Configure detailed logging to see all the new logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_enhanced_features():
    print("\n🧪 Testing Enhanced Calendar Features (Issues #4 and #15)\n")
    
    # Create test identity and preferences
    test_identity = AgentIdentity(
        agent_id="test_agent_001",
        user_name="Test User",
        user_email="test@example.com"
    )
    
    test_preferences = SchedulingPreferences(
        preferred_meeting_times=["morning", "early_afternoon"],
        max_meetings_per_day=6,
        min_meeting_gap_minutes=15,
        focus_time_protection=True,
        energy_level_optimization=True
    )
    
    # Initialize coordinator with identity and preferences
    coordinator = IntegratedCoordinationProtocol(test_identity, test_preferences)
    
    # Create a test conversation with links
    conversation_id = "test_conv_123"
    
    # Create initial request with links in description
    meeting_context = MeetingContext(
        subject="Project Planning Session",
        description="Let's review the design doc at https://docs.google.com/document/d/abc123 and check the GitHub issues at https://github.com/company/repo/issues",
        meeting_type="planning_meeting",
        duration_minutes=60,
        attendees=["alice@company.com", "bob@company.com"],
        requires_preparation=True
    )
    
    # Create test messages
    import uuid
    request_msg = CoordinationMessage(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.SCHEDULE_REQUEST,
        from_agent=test_identity,
        to_agent_email="alice@company.com",
        payload={
            "meeting_context": meeting_context.__dict__,
            "preferences": {
                "preferred_times": ["mornings", "early afternoon"],
                "time_constraints": "Avoid Fridays"
            }
        },
        conversation_id=conversation_id,
        timestamp=datetime.now()
    )
    
    # Add a proposal with more links
    proposal_msg = CoordinationMessage(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.SCHEDULE_PROPOSAL,
        from_agent=AgentIdentity("other_agent", "Alice", "alice@company.com"),
        to_agent_email=test_identity.user_email,
        payload={
            "proposed_times": [
                {
                    "start_time": (datetime.now() + timedelta(days=1, hours=10)).isoformat(),
                    "end_time": (datetime.now() + timedelta(days=1, hours=11)).isoformat()
                }
            ],
            "additional_info": "Also check the Zoom link: https://zoom.us/j/123456789"
        },
        conversation_id=conversation_id,
        timestamp=datetime.now()
    )
    
    # Store conversation
    coordinator.active_conversations[conversation_id] = [request_msg, proposal_msg]
    
    print("📊 Test Setup Complete")
    print(f"  - Meeting Subject: {meeting_context.subject}")
    print(f"  - Meeting Type: {meeting_context.meeting_type}")
    print(f"  - Attendees: {meeting_context.attendees}")
    print(f"  - Links in description: 2 (Google Doc, GitHub)")
    print(f"  - Links in proposal: 1 (Zoom)")
    
    # Test event details preparation
    print("\n🔧 Testing Event Details Preparation...")
    selected_time = TimeSlot(
        start_time=datetime.now() + timedelta(days=1, hours=10),
        end_time=datetime.now() + timedelta(days=1, hours=11),
        confidence_score=0.95
    )
    
    event_details = coordinator._prepare_calendar_event_details(proposal_msg, selected_time)
    
    print("\n✅ Event Details Generated:")
    print(f"  - Title: {event_details['summary']}")
    print(f"  - Description Length: {len(event_details['description'])} chars")
    print(f"  - Attendees: {event_details['attendees']}")
    
    # Check if links were extracted
    if "https://docs.google.com" in event_details['description']:
        print("  - ✅ Google Doc link found in description")
    else:
        print("  - ❌ Google Doc link NOT found in description")
        
    if "https://github.com" in event_details['description']:
        print("  - ✅ GitHub link found in description")
    else:
        print("  - ❌ GitHub link NOT found in description")
        
    if "https://zoom.us" in event_details['description']:
        print("  - ✅ Zoom link found in description")
    else:
        print("  - ❌ Zoom link NOT found in description")
    
    # Check enhanced title format
    if "|" in event_details['summary']:
        print(f"  - ✅ Enhanced title format detected (contains '|')")
    else:
        print(f"  - ❌ Enhanced title format NOT detected")
    
    print("\n📋 Full Description Preview:")
    print("-" * 50)
    print(event_details['description'][:1000])
    if len(event_details['description']) > 1000:
        print(f"... ({len(event_details['description']) - 1000} more chars)")
    print("-" * 50)
    
    return event_details

if __name__ == "__main__":
    try:
        event_details = test_enhanced_features()
        print("\n🎉 Test completed! Check the logs above for detailed information.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()