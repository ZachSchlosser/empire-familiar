#!/usr/bin/env python3
"""
Test sending a reply with thread ID
"""

from coordination_helpers import check_and_respond_to_coordination

def test_reply_with_thread():
    """Test that replies include the thread ID"""
    
    print("=== Testing Reply with Thread ID ===\n")
    
    print("Checking for and responding to coordination messages...")
    print("This will show if threadId is being passed to Gmail API\n")
    
    # This will process messages and show the thread ID being used
    check_and_respond_to_coordination()
    
    print("\n✅ If you see '🧵 Replying to thread: ...' above, the fix is working!")

if __name__ == "__main__":
    test_reply_with_thread()