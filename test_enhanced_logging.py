#!/usr/bin/env python3
"""
Test script to demonstrate enhanced thread logging
"""

import logging
from coordination_helpers import check_and_respond_to_coordination

# Configure logging to show INFO level
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simple format for cleaner output
)

def test_enhanced_logging():
    """Test the enhanced thread logging"""
    
    print("="*60)
    print("🔍 ENHANCED THREAD LOGGING TEST")
    print("="*60)
    print("\nThis test will show detailed thread tracking information:")
    print("- 🆕 New threads being created")
    print("- 🔗 Existing threads being continued") 
    print("- ✅ Thread consistency verification")
    print("- 📊 Thread summaries with message counts")
    print("- ⚠️  Any thread mismatches or issues")
    print("\n" + "="*60 + "\n")
    
    # Process coordination messages with enhanced logging
    check_and_respond_to_coordination()
    
    print("\n" + "="*60)
    print("✅ Enhanced logging test complete!")
    print("="*60)
    print("\nWhat to look for in the logs above:")
    print("1. Thread ID consistency across messages")
    print("2. Gmail API Request showing threadId=✓")
    print("3. Thread summaries showing message counts")
    print("4. Any warnings about thread changes")
    print("="*60)

if __name__ == "__main__":
    test_enhanced_logging()