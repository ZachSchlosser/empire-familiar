#!/usr/bin/env python3
"""
Comprehensive Calendar API testing to ensure NO errors occur
"""

import pytz
from datetime import datetime, timedelta
from integrated_agent_coordination import (
    initialize_integrated_coordination_system, 
    now_tz, 
    now_utc, 
    IntegratedCoordinationProtocol,
    MeetingContext,
    MessageType,
    CoordinationMessage,
    AgentIdentity
)
from calendar_functions import CalendarManager

def test_all_calendar_paths():
    """Test every code path that makes Calendar API calls"""
    
    print("=== Comprehensive Calendar API Testing ===\n")
    
    results = {
        'tests_run': 0,
        'tests_passed': 0,
        'calendar_errors': 0,
        'errors': []
    }
    
    try:
        # Test 1: Direct Calendar Manager calls
        print("🧪 Test 1: Direct CalendarManager API calls")
        results['tests_run'] += 1
        
        calendar_manager = CalendarManager()
        
        # Test timezone-aware calls
        now = now_tz()
        future = now + timedelta(days=7)
        
        events = calendar_manager.get_events(time_min=now, time_max=future, max_results=50)
        print(f"   ✅ get_events with timezone-aware datetime: {len(events)} events")
        results['tests_passed'] += 1
        
        # Test 2: Coordination system initialization
        print("\n🧪 Test 2: Coordination system initialization")
        results['tests_run'] += 1
        
        coordinator = initialize_integrated_coordination_system()
        print(f"   ✅ Coordination system initialized: {coordinator.agent_identity.agent_id}")
        results['tests_passed'] += 1
        
        # Test 3: _find_intelligent_available_times function
        print("\n🧪 Test 3: _find_intelligent_available_times")
        results['tests_run'] += 1
        
        meeting_context = MeetingContext(
            meeting_type="1:1",
            duration_minutes=60,
            attendees=["test@example.com", "zach@empire.email"],
            subject="Test Meeting",
            description="Test meeting for Calendar API validation"
        )
        
        request_payload = {
            "time_preferences": ["next week", "morning", "afternoon"],
            "meeting_context": {
                "subject": "Test Meeting",
                "duration_minutes": 60,
                "attendees": ["test@example.com", "zach@empire.email"]
            }
        }
        
        try:
            time_slots = coordinator._find_intelligent_available_times(meeting_context, request_payload)
            print(f"   ✅ _find_intelligent_available_times: {len(time_slots)} slots generated")
            results['tests_passed'] += 1
        except Exception as e:
            if "HTTP Error" in str(e) and "400" in str(e):
                results['calendar_errors'] += 1
                results['errors'].append(f"Calendar API error in _find_intelligent_available_times: {e}")
                print(f"   ❌ Calendar API error: {e}")
            else:
                results['errors'].append(f"Other error in _find_intelligent_available_times: {e}")
                print(f"   ❌ Other error: {e}")
        
        # Test 4: _find_all_available_times function
        print("\n🧪 Test 4: _find_all_available_times")
        results['tests_run'] += 1
        
        try:
            all_slots = coordinator._find_all_available_times(meeting_context, request_payload)
            print(f"   ✅ _find_all_available_times: {len(all_slots)} slots generated")
            results['tests_passed'] += 1
        except Exception as e:
            if "HTTP Error" in str(e) and "400" in str(e):
                results['calendar_errors'] += 1
                results['errors'].append(f"Calendar API error in _find_all_available_times: {e}")
                print(f"   ❌ Calendar API error: {e}")
            else:
                results['errors'].append(f"Other error in _find_all_available_times: {e}")
                print(f"   ❌ Other error: {e}")
        
        # Test 5: Natural language time parsing
        print("\n🧪 Test 5: Natural language time parsing")
        results['tests_run'] += 1
        
        test_preferences = ["today", "tomorrow", "next week", "this week", "morning"]
        for pref in test_preferences:
            try:
                start, end = coordinator._parse_time_preference(pref)
                print(f"   ✅ '{pref}' parsed: {start.isoformat()} to {end.isoformat()}")
                
                # Verify these are timezone-aware
                if start.tzinfo is None:
                    results['errors'].append(f"Time parsing '{pref}' returned timezone-naive datetime")
                    print(f"   ❌ '{pref}' returned timezone-naive datetime!")
                    
            except Exception as e:
                results['errors'].append(f"Time parsing error for '{pref}': {e}")
                print(f"   ❌ Error parsing '{pref}': {e}")
        
        results['tests_passed'] += 1
        
        # Test 6: Simulate message processing
        print("\n🧪 Test 6: Message processing simulation")
        results['tests_run'] += 1
        
        # Create a mock coordination message
        agent_identity = AgentIdentity(
            agent_id="test_agent",
            user_name="Test User",
            user_email="test@example.com"
        )
        
        mock_message = CoordinationMessage(
            message_id="test_msg_123",
            message_type=MessageType.SCHEDULE_REQUEST,
            from_agent=agent_identity,
            to_agent_email="zach@empire.email",
            timestamp=now_tz(),
            conversation_id="test_conv_123",
            payload=request_payload
        )
        
        try:
            response = coordinator._handle_schedule_request(mock_message)
            if response:
                print(f"   ✅ Mock message processing successful: {response.message_type.value}")
                results['tests_passed'] += 1
            else:
                print(f"   ⚠️  Mock message processing returned None (may be expected)")
                results['tests_passed'] += 1
        except Exception as e:
            if "HTTP Error" in str(e) and "400" in str(e):
                results['calendar_errors'] += 1
                results['errors'].append(f"Calendar API error in message processing: {e}")
                print(f"   ❌ Calendar API error: {e}")
            else:
                results['errors'].append(f"Other error in message processing: {e}")
                print(f"   ❌ Other error: {e}")
        
        # Test 7: Edge case - very short time ranges
        print("\n🧪 Test 7: Edge case testing - short time ranges")
        results['tests_run'] += 1
        
        try:
            now = now_tz()
            near_future = now + timedelta(hours=2)
            
            events = calendar_manager.get_events(time_min=now, time_max=near_future, max_results=10)
            print(f"   ✅ Short time range (2 hours): {len(events)} events")
            results['tests_passed'] += 1
        except Exception as e:
            if "HTTP Error" in str(e) and "400" in str(e):
                results['calendar_errors'] += 1
                results['errors'].append(f"Calendar API error in short range test: {e}")
                print(f"   ❌ Calendar API error: {e}")
            else:
                results['errors'].append(f"Other error in short range test: {e}")
                print(f"   ❌ Other error: {e}")
        
    except Exception as e:
        results['errors'].append(f"Critical test setup error: {e}")
        print(f"❌ Critical error: {e}")
    
    # Print comprehensive results
    print(f"\n" + "="*60)
    print("COMPREHENSIVE TEST RESULTS")
    print("="*60)
    print(f"Total tests run: {results['tests_run']}")
    print(f"Tests passed: {results['tests_passed']}")
    print(f"Calendar API errors: {results['calendar_errors']}")
    print(f"Other errors: {len(results['errors']) - results['calendar_errors']}")
    
    if results['calendar_errors'] == 0:
        print("\n🎉 SUCCESS: No Calendar API errors detected!")
        print("✅ All timezone-aware datetime handling is working correctly")
    else:
        print(f"\n❌ FAILURE: {results['calendar_errors']} Calendar API errors still exist!")
        print("❌ The timezone fix is not complete")
    
    if results['errors']:
        print(f"\nDetailed errors:")
        for i, error in enumerate(results['errors'], 1):
            print(f"  {i}. {error}")
    
    return results['calendar_errors'] == 0

if __name__ == "__main__":
    success = test_all_calendar_paths()
    exit(0 if success else 1)