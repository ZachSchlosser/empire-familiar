#!/usr/bin/env python3
"""
Real-time Agent Email Monitor

This script continuously monitors for agent emails and auto-responds,
creating a near real-time communication system between Claude Code agents.
"""

import time
import schedule
from datetime import datetime
from integrated_agent_coordination import initialize_integrated_coordination_system, process_agent_coordination_messages

class AgentEmailMonitor:
    """Real-time monitor for agent email communications"""
    
    def __init__(self, check_interval_minutes=2):
        """
        Initialize the email monitor.
        
        Args:
            check_interval_minutes: How often to check for new emails
        """
        self.check_interval = check_interval_minutes
        self.coordinator = initialize_integrated_coordination_system()
        self.is_running = False
        self.message_count = 0
        
        print(f"🔄 Agent Email Monitor initialized")
        print(f"📧 Monitoring: {self.coordinator.agent_identity.user_email}")
        print(f"⏱️  Check interval: every {check_interval_minutes} minutes")
        print(f"🎯 Using [CLAUDE-COORD] protocol for coordination messages")
    
    def start_monitoring(self, duration_minutes=60):
        """
        Start monitoring for agent emails.
        
        Args:
            duration_minutes: How long to monitor (0 = indefinite)
        """
        print(f"\n🚀 Starting email monitoring...")
        print(f"Duration: {duration_minutes} minutes" if duration_minutes > 0 else "Duration: indefinite")
        print("=" * 50)
        
        self.is_running = True
        start_time = datetime.now()
        
        # Schedule regular checks
        schedule.every(self.check_interval).minutes.do(
            self._check_and_respond_job
        )
        
        # Initial check
        self._check_and_respond_job()
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds for scheduled jobs
                
                # Stop after duration if specified
                if duration_minutes > 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        self.stop_monitoring()
                        
        except KeyboardInterrupt:
            print("\\n⏹️  Monitoring stopped by user")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop the email monitoring"""
        self.is_running = False
        schedule.clear()
        print(f"\\n✅ Monitoring stopped after processing {self.message_count} coordination messages")
        print(f"🕐 Final check at: {datetime.now().strftime('%H:%M:%S')}")
    
    def _check_and_respond_job(self):
        """Job function for checking and responding to coordination messages"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\\n🔍 [{timestamp}] Checking for coordination messages...")
            
            results = process_agent_coordination_messages()
            
            processed_count = len(results)
            response_count = len([r for r in results if r.get('response_sent', False)])
            
            if processed_count > 0:
                print(f"📬 Found {processed_count} new coordination messages:")
                for result in results:
                    if result.get('processed', False):
                        msg_type = result.get('message_type', 'unknown')
                        from_agent = result.get('from_agent', 'unknown')
                        print(f"  • {msg_type} from {from_agent}")
                
                if response_count > 0:
                    print(f"🤖 Sent {response_count} auto-responses")
                
                self.message_count += processed_count
            else:
                print("📭 No new coordination messages")
                
        except Exception as e:
            print(f"❌ Error during coordination message check: {e}")
    
    def run_single_check(self):
        """Run a single check for coordination messages"""
        print("🔍 Running single coordination message check...")
        self._check_and_respond_job()

def start_agent_coordination_monitoring(duration_minutes=60, check_interval=2):
    """
    Start monitoring agent coordination messages.
    
    Args:
        duration_minutes: How long to monitor (0 = indefinite)
        check_interval: How often to check (in minutes)
    """
    monitor = AgentEmailMonitor(check_interval_minutes=check_interval)
    monitor.start_monitoring(duration_minutes=duration_minutes)

def quick_coordination_check():
    """Run a quick check for coordination messages"""
    monitor = AgentEmailMonitor()
    monitor.run_single_check()

if __name__ == "__main__":
    import sys
    
    print("🤖 Agent Coordination Monitor")
    print("=" * 35)
    print("🎯 Monitoring [CLAUDE-COORD] messages using integrated coordination system")
    print()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            # Quick check mode
            quick_coordination_check()
        elif sys.argv[1] == "monitor":
            # Continuous monitoring
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            start_agent_coordination_monitoring(duration_minutes=duration)
    else:
        # Default: 30 minute monitoring session
        start_agent_coordination_monitoring(duration_minutes=30)