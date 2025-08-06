#!/usr/bin/env python3
"""
Test Calendar API fix for timezone-aware datetime issue
"""

import pytz
from datetime import datetime, timedelta
from calendar_functions import CalendarManager

def test_calendar_api():
    """Test that Calendar API works with timezone-aware datetime"""
    
    print("=== Calendar API Fix Test ===\n")
    
    try:
        # Initialize calendar manager
        calendar_manager = CalendarManager()
        print("✅ Calendar manager initialized")
        
        # Test with timezone-aware datetime (the fix)
        print("\n🧪 Testing with timezone-aware datetime...")
        now = datetime.now(pytz.timezone('America/New_York'))
        search_end = now + timedelta(days=7)
        
        print(f"   search_start: {now}")
        print(f"   search_end: {search_end}")
        print(f"   search_start.isoformat(): {now.isoformat()}")
        
        # Call get_events with timezone-aware datetimes
        events = calendar_manager.get_events(
            time_min=now,
            time_max=search_end,
            max_results=5
        )
        
        print(f"✅ Calendar API call succeeded! Found {len(events)} events")
        
        # Test with timezone-naive datetime (the bug)
        print("\n🧪 Testing with timezone-naive datetime...")
        naive_now = datetime.now()  # No timezone
        naive_end = naive_now + timedelta(days=7)
        
        print(f"   naive_start: {naive_now}")
        print(f"   naive_start.isoformat(): {naive_now.isoformat()}")
        
        try:
            events = calendar_manager.get_events(
                time_min=naive_now,
                time_max=naive_end,
                max_results=5
            )
            print(f"❓ Naive datetime worked unexpectedly: {len(events)} events")
        except Exception as e:
            print(f"❌ Naive datetime failed as expected: {e}")
            
    except Exception as e:
        print(f"❌ Calendar API test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_calendar_api()