#!/usr/bin/env python3
"""
Test script to verify email threading fix
"""

import time
from integrated_agent_coordination import initialize_integrated_coordination_system
from coordination_helpers import setup_coordination_for_user, schedule_meeting_with_agent

def test_threading():
    """Test that Agent B replies in the same thread as Agent A"""
    
    print("=== Email Threading Fix Test ===\n")
    
    # Initialize coordination system
    print("1. Initializing coordination system...")
    coordinator = initialize_integrated_coordination_system()
    
    # Display current agent info
    print(f"   Agent: {coordinator.agent_identity.user_name}")
    print(f"   Email: {coordinator.agent_identity.user_email}")
    
    # Check recent coordination messages
    print("\n2. Checking for recent coordination messages...")
    messages = coordinator.email_transport.check_for_coordination_messages(max_messages=5)
    
    if messages:
        print(f"   Found {len(messages)} coordination messages")
        for msg in messages:
            print(f"   - {msg.message_type.value} from {msg.from_agent.user_email}")
            print(f"     Conversation ID: {msg.conversation_id}")
            
            # Check threading state
            conv_info = coordinator.email_transport.conversation_threading.get(msg.conversation_id)
            if conv_info:
                print(f"     Latest Message-ID: {conv_info.get('latest_message_id', 'None')}")
                print(f"     Thread has {len(conv_info.get('message_ids', []))} messages")
    else:
        print("   No recent coordination messages found")
    
    print("\n3. Threading state summary:")
    for conv_id, conv_info in coordinator.email_transport.conversation_threading.items():
        print(f"   Conversation: {conv_id}")
        print(f"   - Latest Message-ID: {conv_info.get('latest_message_id', 'None')}")
        print(f"   - Messages in thread: {len(conv_info.get('message_ids', []))}")
        print(f"   - Gmail Thread ID: {conv_info.get('thread_id', 'None')}")
    
    print("\nTest complete. Check Gmail to verify threading behavior.")
    print("When Agent B responds, it should now reply in the same thread as Agent A's email.")

if __name__ == "__main__":
    test_threading()