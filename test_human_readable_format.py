#!/usr/bin/env python3
"""
Test the new human-readable agent coordination format
"""

from integrated_agent_coordination import *
from datetime import datetime, timedelta

def test_human_readable_format():
    """Test the new human-readable coordination message format"""
    
    # Create test agent identity
    agent_identity = AgentIdentity(
        agent_id="test_agent_001",
        user_name="John Smith",
        user_email="john@example.com"
    )
    
    # Create test scheduling preferences
    preferences = SchedulingPreferences()
    
    # Create email transport layer (mock for testing)
    class MockEmailTransport:
        def __init__(self, agent_identity):
            self.agent_identity = agent_identity
            self.MESSAGE_SEPARATOR = "--- AGENT COORDINATION ---"
        
        def _generate_human_summary(self, message):
            return EmailTransportLayer(agent_identity)._generate_human_summary(message)
        
        def _create_coordination_email_body(self, message):
            return EmailTransportLayer(agent_identity)._create_coordination_email_body(message)
    
    transport = MockEmailTransport(agent_identity)
    
    print("🧪 Testing Human-Readable Agent Coordination Format\n")
    
    # Test 1: Schedule Request
    print("=" * 60)
    print("TEST 1: SCHEDULE REQUEST")
    print("=" * 60)
    
    meeting_context = MeetingContext(
        meeting_type="team_meeting",
        duration_minutes=60,
        attendees=["john@example.com", "sarah@example.com"],
        subject="Q1 Planning Session",
        description="Quarterly planning meeting to review goals and priorities",
        requires_preparation=True
    )
    
    schedule_request = CoordinationMessage(
        message_id="msg_001",
        message_type=MessageType.SCHEDULE_REQUEST,
        from_agent=agent_identity,
        to_agent_email="sarah@example.com",
        timestamp=datetime.now(),
        conversation_id="conv_001",
        payload={
            'meeting_context': {
                'subject': meeting_context.subject,
                'duration_minutes': meeting_context.duration_minutes,
                'attendees': meeting_context.attendees,
                'description': meeting_context.description,
                'meeting_type': meeting_context.meeting_type
            },
            'preferences': {
                'preferred_times': ['Tuesday mornings', 'Wednesday afternoons'],
                'time_constraints': 'No meetings after 4 PM'
            }
        },
        requires_response=True,
        expires_at=datetime.now() + timedelta(hours=24)
    )
    
    email_body = transport._create_coordination_email_body(schedule_request)
    print(email_body)
    print("\n")
    
    # Test 2: Schedule Proposal
    print("=" * 60)
    print("TEST 2: SCHEDULE PROPOSAL")
    print("=" * 60)
    
    schedule_proposal = CoordinationMessage(
        message_id="msg_002",
        message_type=MessageType.SCHEDULE_PROPOSAL,
        from_agent=agent_identity,
        to_agent_email="john@example.com",
        timestamp=datetime.now(),
        conversation_id="conv_001",
        payload={
            'proposed_times': [
                {
                    'start_time': (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0).isoformat(),
                    'end_time': (datetime.now() + timedelta(days=1)).replace(hour=11, minute=0).isoformat()
                },
                {
                    'start_time': (datetime.now() + timedelta(days=2)).replace(hour=14, minute=30).isoformat(),
                    'end_time': (datetime.now() + timedelta(days=2)).replace(hour=15, minute=30).isoformat()
                },
                {
                    'start_time': (datetime.now() + timedelta(days=3)).replace(hour=9, minute=0).isoformat(),
                    'end_time': (datetime.now() + timedelta(days=3)).replace(hour=10, minute=0).isoformat()
                }
            ],
            'context': {
                'workload_note': 'Light schedule this week, flexible with timing'
            }
        },
        requires_response=True
    )
    
    email_body = transport._create_coordination_email_body(schedule_proposal)
    print(email_body)
    print("\n")
    
    # Test 3: Schedule Confirmation
    print("=" * 60)
    print("TEST 3: SCHEDULE CONFIRMATION") 
    print("=" * 60)
    
    schedule_confirmation = CoordinationMessage(
        message_id="msg_003",
        message_type=MessageType.SCHEDULE_CONFIRMATION,
        from_agent=agent_identity,
        to_agent_email="sarah@example.com",
        timestamp=datetime.now(),
        conversation_id="conv_001",
        payload={
            'confirmed_time': {
                'start_time': (datetime.now() + timedelta(days=2)).replace(hour=14, minute=30).isoformat()
            },
            'meeting_details': {
                'location': 'Conference Room A',
                'meeting_link': 'https://meet.google.com/abc-defg-hij'
            }
        },
        requires_response=False
    )
    
    email_body = transport._create_coordination_email_body(schedule_confirmation)
    print(email_body)
    print("\n")
    
    # Test 4: Schedule Rejection
    print("=" * 60)
    print("TEST 4: SCHEDULE REJECTION")
    print("=" * 60)
    
    schedule_rejection = CoordinationMessage(
        message_id="msg_004",
        message_type=MessageType.SCHEDULE_REJECTION,
        from_agent=agent_identity,
        to_agent_email="john@example.com",  
        timestamp=datetime.now(),
        conversation_id="conv_001",
        payload={
            'reason': 'All proposed times conflict with existing meetings',
            'alternative_suggestion': 'Would Thursday morning or Friday afternoon work better?'
        },
        requires_response=True
    )
    
    email_body = transport._create_coordination_email_body(schedule_rejection)
    print(email_body)
    print("\n")
    
    print("🎉 All tests completed! The new format shows:")
    print("• Clear, structured English that humans can easily read")
    print("• All coordination details visible and understandable") 
    print("• Bullet-point format for easy scanning")
    print("• Minimal technical data at the bottom for agent processing")
    print("• Complete transparency in agent negotiations")

if __name__ == "__main__":
    test_human_readable_format()