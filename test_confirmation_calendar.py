#!/usr/bin/env python3
"""
Test script to verify calendar event creation with attendee invites
when processing schedule confirmations
"""

import sys
import json
from datetime import datetime, timedelta
from integrated_agent_coordination import (
    IntegratedCoordinationProtocol,
    AgentIdentity,
    SchedulingPreferences,
    CoordinationMessage,
    MessageType,
    Priority,
    TimeSlot
)

def test_schedule_confirmation_calendar():
    """Test that schedule confirmations create calendar events with attendees"""
    
    print("🧪 Testing Schedule Confirmation Calendar Event Creation")
    print("=" * 60)
    
    try:
        # Initialize test agent
        test_agent = AgentIdentity(
            agent_id="test_agent_1",
            user_name="Test Agent",
            user_email="testuser@example.com"
        )
        
        preferences = SchedulingPreferences(
            preferred_meeting_times=["morning", "afternoon"],
            max_meetings_per_day=5
        )
        
        coordinator = IntegratedCoordinationProtocol(test_agent, preferences)
        print(f"✅ Test coordinator initialized: {test_agent.agent_id}")
        
        # Create a mock confirmation message from another agent
        other_agent = AgentIdentity(
            agent_id="other_agent",
            user_name="Other Agent",
            user_email="otheragent@example.com"
        )
        
        # Create time slot for tomorrow at 2 PM
        tomorrow_2pm = datetime.now() + timedelta(days=1)
        tomorrow_2pm = tomorrow_2pm.replace(hour=14, minute=0, second=0, microsecond=0)
        tomorrow_3pm = tomorrow_2pm + timedelta(hours=1)
        
        confirmed_time_slot = TimeSlot(
            start_time=tomorrow_2pm,
            end_time=tomorrow_3pm,
            confidence_score=0.9
        )
        
        # Create confirmation message
        confirmation_message = CoordinationMessage(
            message_id="test_confirmation_123",
            message_type=MessageType.SCHEDULE_CONFIRMATION,
            from_agent=other_agent,
            to_agent_email=test_agent.user_email,
            timestamp=datetime.now(),
            conversation_id="test_conversation_456",
            priority=Priority.MEDIUM,
            payload={
                "selected_time": coordinator._serialize_timeslot(confirmed_time_slot),
                "calendar_event_details": {
                    "summary": "Test Agent Coordination Meeting",
                    "description": "Testing calendar event creation with attendees"
                }
            }
        )
        
        # Add this message to active conversations to simulate conversation history
        coordinator.active_conversations[confirmation_message.conversation_id] = [
            # Mock original request message
            CoordinationMessage(
                message_id="original_request_789",
                message_type=MessageType.SCHEDULE_REQUEST,
                from_agent=other_agent,
                to_agent_email=test_agent.user_email,
                timestamp=datetime.now() - timedelta(minutes=30),
                conversation_id="test_conversation_456",
                priority=Priority.MEDIUM,
                payload={
                    "meeting_context": {
                        "meeting_type": "test_meeting",
                        "urgency": "medium",
                        "duration_minutes": 60,
                        "attendees": ["testuser@example.com", "otheragent@example.com"],
                        "subject": "Test Agent Coordination Meeting",
                        "description": "Testing calendar event creation with attendees"
                    }
                }
            ),
            confirmation_message
        ]
        
        print(f"📅 Testing confirmation for: {tomorrow_2pm.strftime('%Y-%m-%d %H:%M')}")
        print(f"🤝 Agents involved: {test_agent.user_email} and {other_agent.user_email}")
        
        # Process the confirmation message
        response = coordinator._handle_schedule_confirmation(confirmation_message)
        
        if response:
            print(f"✅ Confirmation processed successfully")
            print(f"📧 Response type: {response.message_type.value}")
            print(f"📊 Calendar event created: {response.payload.get('calendar_event_created', False)}")
            
            if 'attendees_invited' in response.payload:
                attendees = response.payload['attendees_invited']
                print(f"👥 Attendees invited: {attendees}")
                
                # Verify both agents are included
                if test_agent.user_email in attendees and other_agent.user_email in attendees:
                    print("✅ Both agents correctly added as attendees")
                else:
                    print(f"❌ Missing attendees. Expected both {test_agent.user_email} and {other_agent.user_email}")
                    print(f"   Got: {attendees}")
            else:
                print("⚠️ No attendee information in response")
                
        else:
            print("❌ Confirmation processing failed - no response generated")
            
        print("\n🎯 Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_schedule_confirmation_calendar()
    sys.exit(0 if success else 1)