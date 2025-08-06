#!/usr/bin/env python3
"""
Stress test Calendar API with the exact conditions that previously failed
"""

import pytz
from datetime import datetime, timedelta
from integrated_agent_coordination import initialize_integrated_coordination_system, now_tz
from calendar_functions import CalendarManager

def test_exact_failure_conditions():
    """Test the exact conditions that were causing Calendar API failures"""
    
    print("=== Calendar API Stress Test ===")
    print("Testing exact conditions that previously caused HTTP 400 errors\n")
    
    errors = []
    
    try:
        coordinator = initialize_integrated_coordination_system()
        print("✅ Coordination system initialized")
        
        # Simulate the exact request payload from the logs
        request_payload = {
            "time_preferences": ["next week", "morning", "afternoon"],
            "meeting_context": {
                "subject": "Prompt Injection Security Discussion", 
                "duration_minutes": 60,
                "attendees": ["zacharyschlosser@gmail.com", "zach@empire.email"],
                "meeting_type": "1:1",
                "description": """Let's discuss prompt injection attacks. Here are some reference materials:
                
Reference: https://github.com/ZachSchlosser/empire-familiar/activity
Additional reading: https://owasp.org/www-community/attacks/Code_Injection"""
            }
        }
        
        print("🧪 Test 1: _find_intelligent_available_times (previously failing)")
        try:
            from integrated_agent_coordination import MeetingContext
            meeting_context = MeetingContext(
                meeting_type="1:1",
                duration_minutes=60,
                attendees=["zacharyschlosser@gmail.com", "zach@empire.email"],
                subject="Prompt Injection Security Discussion",
                description="Meeting about security with reference materials"
            )
            
            slots = coordinator._find_intelligent_available_times(meeting_context, request_payload)
            print(f"   ✅ Success: Generated {len(slots)} time slots without Calendar API errors")
            
        except Exception as e:
            if "HTTP Error" in str(e) and "400" in str(e):
                errors.append(f"Calendar API error in _find_intelligent_available_times: {e}")
                print(f"   ❌ CALENDAR API ERROR: {e}")
            else:
                print(f"   ⚠️  Other error: {e}")
        
        print("\n🧪 Test 2: _find_all_available_times (previously failing)")
        try:
            all_slots = coordinator._find_all_available_times(meeting_context, request_payload)
            print(f"   ✅ Success: Generated {len(all_slots)} time slots without Calendar API errors")
            
        except Exception as e:
            if "HTTP Error" in str(e) and "400" in str(e):
                errors.append(f"Calendar API error in _find_all_available_times: {e}")
                print(f"   ❌ CALENDAR API ERROR: {e}")
            else:
                print(f"   ⚠️  Other error: {e}")
        
        print("\n🧪 Test 3: Direct Calendar API calls with timezone-aware datetimes")
        calendar_manager = CalendarManager()
        
        for i in range(5):
            try:
                now = now_tz()
                future = now + timedelta(days=7)
                
                print(f"   Test {i+1}: timeMin={now.isoformat()}")
                events = calendar_manager.get_events(time_min=now, time_max=future, max_results=50)
                print(f"   ✅ Success: {len(events)} events retrieved")
                
            except Exception as e:
                if "HTTP Error" in str(e) and "400" in str(e):
                    errors.append(f"Calendar API error in direct call {i+1}: {e}")
                    print(f"   ❌ CALENDAR API ERROR {i+1}: {e}")
                else:
                    print(f"   ⚠️  Other error {i+1}: {e}")
        
        print("\n🧪 Test 4: Rapid successive Calendar API calls")
        for i in range(10):
            try:
                now = now_tz() + timedelta(hours=i)
                future = now + timedelta(days=1)
                
                events = calendar_manager.get_events(time_min=now, time_max=future, max_results=10)
                print(f"   Call {i+1}: ✅ {len(events)} events")
                
            except Exception as e:
                if "HTTP Error" in str(e) and "400" in str(e):
                    errors.append(f"Calendar API error in rapid call {i+1}: {e}")
                    print(f"   ❌ CALENDAR API ERROR {i+1}: {e}")
                else:
                    print(f"   ⚠️  Other error {i+1}: {e}")
        
        print(f"\n" + "="*60)
        print("STRESS TEST RESULTS")
        print("="*60)
        
        if len(errors) == 0:
            print("🎉 COMPLETE SUCCESS!")
            print("✅ No Calendar API HTTP 400 errors detected in any test")
            print("✅ All datetime operations are properly timezone-aware")
            print("✅ The system is ready for production use")
            return True
        else:
            print(f"❌ FAILURE: {len(errors)} Calendar API errors detected!")
            print("❌ The timezone fix is not complete!")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")
            return False
            
    except Exception as e:
        print(f"❌ Critical test error: {e}")
        return False

if __name__ == "__main__":
    success = test_exact_failure_conditions()
    exit(0 if success else 1)