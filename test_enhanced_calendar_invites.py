#!/usr/bin/env python3
"""
Test the enhanced meeting invites functionality
"""

from integrated_agent_coordination import *
from datetime import datetime, timedelta
import uuid

def test_enhanced_calendar_invites():
    """Test enhanced title generation and rich descriptions"""
    
    print("🧪 Testing Enhanced Calendar Invites")
    print("=" * 60)
    
    # Create test agent identity
    agent_identity = AgentIdentity(
        agent_id="test_enhanced_agent",
        user_name="John Smith",
        user_email="john.smith@company.com"
    )
    
    # Create coordination protocol
    coordinator = IntegratedCoordinationProtocol(
        agent_identity=agent_identity,
        scheduling_preferences=SchedulingPreferences(),
        current_context=ContextualFactors()
    )
    
    print("✅ Coordination system initialized")
    
    # Test 1: Enhanced Title Generation
    print("\n" + "=" * 40)
    print("TEST 1: Enhanced Title Generation")
    print("=" * 40)
    
    # Create test meeting context
    meeting_context = MeetingContext(
        meeting_type="project_planning",
        duration_minutes=60,
        attendees=["john.smith@company.com", "sarah.chen@company.com", "mike.johnson@company.com"],
        subject="Q1 Strategy Review",
        description="Quarterly planning meeting to review goals, discuss project roadmaps, and plan for Q1 deliverables. Agenda: Review Q4 performance, discuss new initiatives, plan resource allocation.",
        requires_preparation=True
    )
    
    # Test title generation
    enhanced_title = coordinator._generate_enhanced_title(
        meeting_context, 
        meeting_context.attendees, 
        []  # Empty conversation for this test
    )
    
    print(f"📝 Original title: {meeting_context.subject}")
    print(f"✨ Enhanced title: {enhanced_title}")
    
    expected_parts = ["Q1 Strategy Review", "Sarah Chen & Mike Johnson", "Project Planning"]
    success = all(part in enhanced_title for part in ["Q1 Strategy Review", "Sarah Chen"])
    print(f"{'✅' if success else '❌'} Title enhancement: {'Working' if success else 'Failed'}")
    
    # Test 2: Rich Description Generation
    print("\n" + "=" * 40)
    print("TEST 2: Rich Description Generation")
    print("=" * 40)
    
    # Create mock conversation with document links
    conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
    
    # Mock conversation with document links and agenda items
    mock_conversation = [
        CoordinationMessage(
            message_id="msg_001",
            message_type=MessageType.SCHEDULE_REQUEST,
            from_agent=agent_identity,
            to_agent_email="sarah.chen@company.com",
            timestamp=datetime.now(),
            conversation_id=conversation_id,
            payload={
                'meeting_context': {
                    'subject': meeting_context.subject,
                    'description': meeting_context.description + " Please review https://docs.google.com/document/d/abc123/strategy-doc",
                    'duration_minutes': meeting_context.duration_minutes,
                    'attendees': meeting_context.attendees,
                    'meeting_type': meeting_context.meeting_type
                }
            },
            requires_response=True
        )
    ]
    
    # Create test time slot
    test_time = TimeSlot(
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        confidence_score=0.9,
        conflicts=[],
        context_score={}
    )
    
    # Generate enhanced description
    enhanced_description = coordinator._generate_enhanced_description(
        meeting_context,
        meeting_context.attendees,
        mock_conversation,
        test_time
    )
    
    print("📄 Enhanced Description:")
    print("-" * 30)
    print(enhanced_description)
    print("-" * 30)
    
    # Verify description components
    required_sections = [
        "📋 MEETING DETAILS",
        "👥 PARTICIPANTS", 
        "📅 COORDINATION SUMMARY",
        "📎 RELEVANT LINKS & RESOURCES",
        "🎯 NEXT STEPS"
    ]
    
    sections_found = sum(1 for section in required_sections if section in enhanced_description)
    print(f"✅ Description sections: {sections_found}/{len(required_sections)} found")
    
    # Test 3: Document Link Extraction
    print("\n" + "=" * 40)
    print("TEST 3: Document Link Extraction")
    print("=" * 40)
    
    extracted_links = coordinator._extract_document_links(mock_conversation)
    print(f"🔗 Extracted links: {len(extracted_links)}")
    for link in extracted_links:
        print(f"   • {link}")
    
    expected_link = "https://docs.google.com/document/d/abc123/strategy-doc"
    link_found = any(expected_link in link for link in extracted_links)
    print(f"{'✅' if link_found else '❌'} Link extraction: {'Working' if link_found else 'Failed'}")
    
    # Test 4: Project Context Detection
    print("\n" + "=" * 40)
    print("TEST 4: Project Context Detection")
    print("=" * 40)
    
    project_context = coordinator._detect_project_context(mock_conversation)
    print(f"🎯 Project context: '{project_context}'")
    
    context_found = len(project_context) > 0
    print(f"{'✅' if context_found else '❌'} Context detection: {'Working' if context_found else 'Failed'}")
    
    # Test 5: Agenda Item Extraction
    print("\n" + "=" * 40)
    print("TEST 5: Agenda Item Extraction")
    print("=" * 40)
    
    agenda_items = coordinator._extract_agenda_items(mock_conversation)
    print(f"📋 Agenda items: {len(agenda_items)}")
    for item in agenda_items:
        print(f"   • {item}")
    
    agenda_found = len(agenda_items) > 0
    print(f"{'✅' if agenda_found else '❌'} Agenda extraction: {'Working' if agenda_found else 'Failed'}")
    
    # Test 6: Preparation Items Suggestion
    print("\n" + "=" * 40)
    print("TEST 6: Preparation Items Suggestion")
    print("=" * 40)
    
    preparation_items = coordinator._suggest_preparation_items(meeting_context)
    print(f"📝 Preparation suggestions: {len(preparation_items)}")
    for item in preparation_items:
        print(f"   • {item}")
    
    prep_found = len(preparation_items) > 0
    print(f"{'✅' if prep_found else '❌'} Preparation suggestions: {'Working' if prep_found else 'Failed'}")
    
    # Test 7: Integration Test - Full Event Details
    print("\n" + "=" * 40)
    print("TEST 7: Complete Event Details Generation")
    print("=" * 40)
    
    # Mock proposal message for complete test
    proposal_message = CoordinationMessage(
        message_id="msg_002",
        message_type=MessageType.SCHEDULE_PROPOSAL,
        from_agent=AgentIdentity(
            agent_id="sarah_agent",
            user_name="Sarah Chen", 
            user_email="sarah.chen@company.com"
        ),
        to_agent_email="john.smith@company.com",
        timestamp=datetime.now(),
        conversation_id=conversation_id,
        payload={},
        requires_response=False
    )
    
    # Add conversation to coordinator
    coordinator.active_conversations[conversation_id] = mock_conversation
    
    # Generate complete event details
    event_details = coordinator._prepare_calendar_event_details(proposal_message, test_time)
    
    print("📅 Complete Event Details:")
    print("-" * 30)
    print(f"Title: {event_details['summary']}")
    print(f"Attendees: {len(event_details['attendees'])} people")
    print("\nDescription Preview:")
    print(event_details['description'][:200] + "..." if len(event_details['description']) > 200 else event_details['description'])
    print("-" * 30)
    
    # Verify enhanced event has all components
    has_enhanced_title = "|" in event_details['summary']
    has_rich_description = "📋 MEETING DETAILS" in event_details['description']
    
    print(f"{'✅' if has_enhanced_title else '❌'} Enhanced title: {'Generated' if has_enhanced_title else 'Failed'}")
    print(f"{'✅' if has_rich_description else '❌'} Rich description: {'Generated' if has_rich_description else 'Failed'}")
    
    print("\n" + "🎯 SUMMARY")
    print("=" * 60)
    
    all_tests = [success, sections_found == len(required_sections), link_found, 
                context_found, agenda_found, prep_found, has_enhanced_title, has_rich_description]
    passed_tests = sum(all_tests)
    total_tests = len(all_tests)
    
    print(f"✅ Tests passed: {passed_tests}/{total_tests} ({int(passed_tests/total_tests*100)}%)")
    
    if passed_tests == total_tests:
        print("🎉 All enhanced calendar invite features working correctly!")
        print("   ✨ Smart title generation with participants and meeting type")
        print("   📋 Rich contextual descriptions with multiple sections")
        print("   🔗 Automatic document link extraction")
        print("   🎯 Project context detection")
        print("   📝 Agenda item extraction from coordination messages")
        print("   💡 Intelligent preparation suggestions")
        print("\n🚀 Ready for production use!")
    else:
        print("⚠️ Some features need attention - check failed tests above")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    test_enhanced_calendar_invites()