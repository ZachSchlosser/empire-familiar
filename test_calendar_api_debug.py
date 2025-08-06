#!/usr/bin/env python3
"""
Debug Calendar API calls to identify the exact issue
"""

import pytz
from datetime import datetime, timedelta
from calendar_functions import CalendarManager

def test_api_calls():
    """Test exact Calendar API calls that are failing"""
    
    print("=== Calendar API Debug Test ===\n")
    
    try:
        calendar_manager = CalendarManager()
        print("✅ Calendar manager initialized")
        
        # Test 1: Current timezone-aware datetime (should work)
        print("\n🧪 Test 1: Current timezone-aware datetime")
        now_tz = datetime.now(pytz.timezone('America/New_York'))
        end_tz = now_tz + timedelta(days=7)
        
        print(f"   now_tz: {now_tz}")
        print(f"   now_tz.isoformat(): {now_tz.isoformat()}")
        
        events = calendar_manager.get_events(time_min=now_tz, time_max=end_tz, max_results=50)
        print(f"   ✅ Success: {len(events)} events found")
        
        # Test 2: Simulating the exact problematic timestamp from log
        print("\n🧪 Test 2: Simulating problematic timestamp")
        # From log: timeMin=2025-08-06T17%3A44%3A01.429893
        problem_time_str = "2025-08-06T17:44:01.429893"
        problem_time = datetime.fromisoformat(problem_time_str)  # This creates naive datetime
        problem_end = problem_time + timedelta(days=7)
        
        print(f"   problem_time: {problem_time}")
        print(f"   problem_time.isoformat(): {problem_time.isoformat()}")
        print(f"   has timezone: {problem_time.tzinfo is not None}")
        
        events = calendar_manager.get_events(time_min=problem_time, time_max=problem_end, max_results=50)
        print(f"   Result: {len(events)} events")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_api_calls()