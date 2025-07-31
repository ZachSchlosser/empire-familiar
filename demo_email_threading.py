#!/usr/bin/env python3
"""
Demo script showing Gmail email threading in agent coordination conversations.
This demonstrates how coordination messages properly thread in email chains.
"""

from integrated_agent_coordination import (
    initialize_integrated_coordination_system,
    coordinate_intelligent_meeting,
    process_agent_coordination_messages
)
from datetime import datetime
import time

def demo_email_threading():
    """Demonstrate email threading functionality"""
    print("🎬 Gmail Email Threading Demo for Agent Coordination")
    print("=" * 55)
    
    # Initialize the system
    print("📧 Initializing coordination system...")
    coordinator = initialize_integrated_coordination_system()
    print(f"   Agent: {coordinator.agent_identity.user_name}")
    print(f"   Email: {coordinator.agent_identity.user_email}")
    
    # Demo conversation
    target_email = coordinator.agent_identity.user_email  # Send to self for demo
    
    print(f"\n🤝 Starting coordination conversation with {target_email}")
    
    # Message 1: Initial request
    print("\n1️⃣ Sending initial meeting request...")
    success = coordinate_intelligent_meeting(
        target_agent_email=target_email,
        meeting_subject="Demo Threading Conversation",
        duration_minutes=45,
        meeting_type="demo_meeting"
    )
    
    if success:
        print("   ✅ Initial request sent with threading headers")
        
        # Show conversation state
        transport = coordinator.email_transport
        if transport.conversation_threading:
            conv_id = list(transport.conversation_threading.keys())[-1]
            conv_info = transport.conversation_threading[conv_id]
            
            print(f"   📧 Subject: {conv_info['subject']}")
            print(f"   🆔 Conversation ID: {conv_id[:8]}...")
            print(f"   📨 Message IDs in thread:")
            for i, msg_id in enumerate(conv_info['message_ids'], 1):
                print(f"      {i}. {msg_id}")
    
    print("\n✨ Email Threading Features Demonstrated:")
    print("   • Unique Message-ID generated for each email")
    print("   • Conversation ID links all related messages")
    print("   • Subject line remains consistent across thread")
    print("   • Threading headers ensure Gmail groups messages")
    print("   • State tracking maintains conversation history")
    
    print("\n📮 How it works in Gmail:")
    print("   1. First message starts with generated Message-ID")
    print("   2. Reply messages include 'In-Reply-To' header")
    print("   3. 'References' header contains full conversation chain")
    print("   4. Gmail automatically groups threaded messages")
    print("   5. All coordination messages appear in one conversation")
    
    print("\n🔗 Threading Headers Example:")
    if transport.conversation_threading:
        # Generate headers for a hypothetical reply
        from integrated_agent_coordination import CoordinationMessage, MessageType
        
        test_message = CoordinationMessage(
            message_id="demo_reply_123",
            message_type=MessageType.SCHEDULE_PROPOSAL,
            from_agent=coordinator.agent_identity,
            to_agent_email=target_email,
            timestamp=datetime.now(),
            conversation_id=conv_id,
            payload={'demo': 'reply'}
        )
        
        headers = transport._generate_threading_headers(test_message, "[CLAUDE-COORD] Demo Reply")
        
        print(f"   Message-ID: {headers['message_id']}")
        print(f"   In-Reply-To: {headers.get('in_reply_to', 'None')}")
        print(f"   References: {headers.get('references', 'None')}")
        print(f"   Subject: {headers['subject']}")
    
    print("\n🎯 Result: Perfect email threading for agent coordination!")

if __name__ == "__main__":
    demo_email_threading()