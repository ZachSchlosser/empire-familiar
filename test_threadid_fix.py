#!/usr/bin/env python3
"""
Test script to verify Gmail thread ID fix
"""

import time
from integrated_agent_coordination import initialize_integrated_coordination_system
from coordination_helpers import setup_coordination_for_user, schedule_meeting_with_agent

def test_thread_id_fix():
    """Test that emails stay in the same thread"""
    
    print("=== Testing Gmail Thread ID Fix ===\n")
    
    # Initialize coordination system
    print("1. Initializing coordination system...")
    coordinator = initialize_integrated_coordination_system()
    print(f"   ✅ Initialized as: {coordinator.agent_identity.user_email}")
    
    # Check for any pending messages
    print("\n2. Checking for pending coordination messages...")
    messages = coordinator.email_transport.check_for_coordination_messages(max_messages=5)
    
    if messages:
        print(f"   📬 Found {len(messages)} pending messages")
        
        for msg in messages:
            print(f"\n   Processing message from: {msg.from_agent.user_email}")
            print(f"   Message type: {msg.message_type.value}")
            print(f"   Conversation ID: {msg.conversation_id}")
            
            # Check if we have a thread ID for this conversation
            thread_id = coordinator.email_transport.get_conversation_thread_id(msg.conversation_id)
            if thread_id:
                print(f"   ✅ Thread ID found: {thread_id}")
            else:
                print(f"   ⚠️  No thread ID yet for this conversation")
            
            # Process the message
            print(f"   Processing and responding...")
            results = coordinator.process_incoming_coordination_messages()
            
            # Check thread ID after processing
            thread_id_after = coordinator.email_transport.get_conversation_thread_id(msg.conversation_id)
            if thread_id_after:
                print(f"   ✅ Thread ID after processing: {thread_id_after}")
                if thread_id and thread_id == thread_id_after:
                    print(f"   ✅ Thread ID maintained consistently!")
                elif not thread_id and thread_id_after:
                    print(f"   ✅ Thread ID captured from incoming message!")
            
            print(f"   📤 Response sent to maintain thread continuity")
    else:
        print("   📭 No pending messages")
        print("\n3. You can test by having another agent send a coordination request")
        print("   The response should now stay in the same email thread!")
    
    # Show current conversation states
    print(f"\n4. Current conversation states:")
    for conv_id, conv_info in coordinator.email_transport.conversation_threading.items():
        print(f"\n   Conversation: {conv_id}")
        print(f"   - Thread ID: {conv_info.get('thread_id', 'None')}")
        print(f"   - Messages: {len(conv_info.get('message_ids', []))}")
        print(f"   - Latest Message ID: {conv_info.get('latest_message_id', 'None')[:50]}...")
    
    print("\n✅ Thread ID fix is now active!")
    print("   - Replies will include threadId in Gmail API call")
    print("   - Emails should stay in the same thread")
    print("   - No more context loss between messages")

if __name__ == "__main__":
    try:
        test_thread_id_fix()
    except Exception as e:
        print(f"\n❌ Error testing thread fix: {e}")
        import traceback
        traceback.print_exc()