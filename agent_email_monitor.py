#!/usr/bin/env python3
"""
Real-time Agent Email Monitor

This script continuously monitors for agent emails and auto-responds,
creating a near real-time communication system between Claude Code agents.
"""

import time
import schedule
import logging
from datetime import datetime, timedelta
from integrated_agent_coordination import initialize_integrated_coordination_system, process_agent_coordination_messages

# Configure logging to show debug messages from coordination system
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Set specific loggers to appropriate levels
logging.getLogger('integrated_agent_coordination').setLevel(logging.DEBUG)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.WARNING)  # Reduce noise

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
        
        next_run_time = start_time.replace(second=0, microsecond=0) + timedelta(minutes=self.check_interval)
        print(f"📅 Scheduled email checks every {self.check_interval} minutes")
        print(f"📅 Next scheduled check: {next_run_time.strftime('%H:%M:%S')}")
        
        # Initial check
        print("🚀 Running initial email check...")
        self._check_and_respond_job()
        
        try:
            loop_count = 0
            while self.is_running:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds for scheduled jobs
                
                loop_count += 1
                # Log every 6 loops (1 minute) to show we're alive
                if loop_count % 6 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Monitor alive - {elapsed:.1f}min elapsed, {self.message_count} messages processed")
                    import sys
                    sys.stdout.flush()
                
                # Stop after duration if specified
                if duration_minutes > 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        self.stop_monitoring()
                        
        except KeyboardInterrupt:
            print("\\n⏹️  Monitoring stopped by user")
            self.stop_monitoring()
        except Exception as e:
            print(f"\\n❌ Monitoring loop error: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            import sys
            sys.stdout.flush()
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop the email monitoring"""
        self.is_running = False
        schedule.clear()
        print(f"\\n✅ Monitoring stopped after processing {self.message_count} coordination messages")
        print(f"🕐 Final check at: {datetime.now().strftime('%H:%M:%S')}")
    
    def _check_and_respond_job(self):
        """Job function for checking and responding to coordination messages"""
        import sys
        import traceback
        
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\\n🔍 [{timestamp}] Checking for coordination messages...")
            sys.stdout.flush()  # Force output to be written immediately
            
            results = process_agent_coordination_messages()
            
            # Separate successful and failed results
            successful_results = [r for r in results if r.get('processed', False) or r.get('response_sent', False)]
            failed_results = [r for r in results if r.get('error') == 'parse_failed']
            other_failures = [r for r in results if not r.get('processed', False) and r.get('error') != 'parse_failed']
            
            processed_count = len(successful_results)
            response_count = len([r for r in successful_results if r.get('response_sent', False)])
            failed_count = len(failed_results)
            
            if processed_count > 0:
                print(f"📬 Found {processed_count} new coordination messages:")
                for result in successful_results:
                    msg_type = result.get('message_type', 'unknown')
                    from_agent = result.get('from_agent', 'unknown')
                    print(f"  • {msg_type} from {from_agent}")
                
                if response_count > 0:
                    print(f"🤖 Sent {response_count} auto-responses")
                
                self.message_count += processed_count
                
            if failed_count > 0:
                print(f"⚠️  {failed_count} messages failed to parse:")
                for result in failed_results:
                    details = result.get('details', {})
                    print(f"  • Message {result['message_id'][:8]}...")
                    print(f"    From: {details.get('from_email', 'unknown')}")
                    print(f"    Has separator: {details.get('has_separator', 'unknown')}")
                    if details.get('body_preview'):
                        print(f"    Body: {details['body_preview'][:50]}...")
                        
            if other_failures:
                print(f"❌ {len(other_failures)} messages failed processing:")
                for result in other_failures:
                    print(f"  • {result.get('message_id', 'unknown')}: {result.get('error', 'unknown error')}")
                
            if processed_count == 0 and failed_count == 0 and len(other_failures) == 0:
                print("📭 No new coordination messages")
                
            sys.stdout.flush()  # Ensure all output is written
            
        except Exception as e:
            print(f"❌ Error during coordination message check: {e}")
            print(f"❌ Full traceback: {traceback.format_exc()}")
            sys.stdout.flush()
            # Re-raise to ensure the error is visible
            raise
    
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