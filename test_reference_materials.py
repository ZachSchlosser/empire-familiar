#!/usr/bin/env python3
"""
Test reference materials functionality
"""

from coordination_helpers import schedule_meeting_with_agent

def test_reference_materials():
    """Test that reference materials (links) are extracted and included"""
    
    print("=== Reference Materials Test ===\n")
    
    try:
        # Test scheduling with description containing links
        test_description = """Let's discuss prompt injection attacks. Here are some reference materials to review beforehand:

Reference: https://github.com/ZachSchlosser/empire-familiar/activity
Additional reading: https://owasp.org/www-community/attacks/Code_Injection

We should also look at the documentation: https://docs.example.com/security"""

        print("📋 Testing meeting coordination with reference links...")
        print(f"   Description contains: {test_description.count('http')} links")
        
        result = schedule_meeting_with_agent(
            target_email="test@example.com",  # Using test email to avoid sending
            meeting_subject="Prompt Injection Security Discussion",
            duration_minutes=60,
            description=test_description
        )
        
        print(f"✅ Coordination initiated: {result['coordination_initiated']}")
        print(f"   Subject: {result['meeting_subject']}")
        
        if result['coordination_initiated']:
            print("\n📎 Reference links should be extracted from the description")
            print("   Links should appear in:")
            print("   • Human-readable coordination message")
            print("   • Final calendar event when meeting is confirmed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_reference_materials()