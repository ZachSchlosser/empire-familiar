#!/usr/bin/env python3
"""
Monitoring Manager for Agent Email Monitor

This utility provides robust process management for the agent_email_monitor.py
background process, replacing unreliable nohup scripts with proper PID tracking,
health checks, and automated restart capabilities.
"""

import os
import sys
import subprocess
import time
import argparse
import psutil
import logging

# Constants
PID_FILE = "monitor.pid"
LOG_FILE = "monitor.log"
MONITOR_SCRIPT = "agent_email_monitor.py"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_pid() -> int | None:
    """
    Read the PID from the PID file.
    
    Returns:
        The integer PID if the file exists and contains a valid number, None otherwise.
    """
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    return int(pid_str)
    except (IOError, ValueError) as e:
        logger.warning(f"Error reading PID file: {e}")
    return None


def is_running() -> bool:
    """
    Check if the monitor process is currently running.
    
    Returns:
        True if the process is alive and correct, False otherwise.
    """
    pid = get_pid()
    if pid is None:
        return False
    
    try:
        # Check if process exists
        if not psutil.pid_exists(pid):
            return False
        
        # Verify it's the correct process by checking command line
        process = psutil.Process(pid)
        cmdline = process.cmdline()
        
        # Check if the command line contains our monitor script
        if any(MONITOR_SCRIPT in arg for arg in cmdline):
            return True
        else:
            logger.warning(f"Process {pid} exists but is not our monitor script")
            return False
            
    except psutil.NoSuchProcess:
        return False
    except Exception as e:
        logger.error(f"Error checking process status: {e}")
        return False


def start(interval: int, duration: int):
    """
    Start the monitor process.
    
    Args:
        interval: Check interval in minutes
        duration: Duration to run in minutes (0 for indefinite)
    """
    if is_running():
        print("🟡 Monitor is already running")
        return
    
    # Construct the command
    command = [
        sys.executable,
        MONITOR_SCRIPT,
        "monitor",
        str(duration),
        str(interval)
    ]
    
    try:
        # Open log file in append mode
        with open(LOG_FILE, 'a') as log_file:
            # Write a start marker to the log
            log_file.write(f"\n{'='*50}\n")
            log_file.write(f"Monitor started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Command: {' '.join(command)}\n")
            log_file.write(f"{'='*50}\n")
            log_file.flush()
            
            # Set up environment to ensure proper Python path
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
            
            # Launch the monitor as a detached background process
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent session
                env=env,  # Pass environment variables
                cwd=os.path.dirname(os.path.abspath(__file__))  # Set working directory
            )
        
        # Write PID to file
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))
        
        print(f"🚀 Monitor started with PID {process.pid}. Logging to {LOG_FILE}.")
        logger.info(f"Started monitor process with PID {process.pid}")
        
    except Exception as e:
        print(f"❌ Failed to start monitor: {e}")
        logger.error(f"Failed to start monitor: {e}")


def stop():
    """Stop the monitor process."""
    pid = get_pid()
    if pid is None:
        print("🔴 Monitor is not running")
        return
    
    try:
        process = psutil.Process(pid)
        process.terminate()
        
        # Wait for process to terminate
        time.sleep(1)
        
        # Check if it's really gone
        if psutil.pid_exists(pid):
            print(f"⚠️  Process {pid} did not terminate gracefully, forcing...")
            try:
                process.kill()
                time.sleep(1)
            except psutil.NoSuchProcess:
                pass  # Already gone
        
        # Clean up PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        
        print(f"✅ Monitor with PID {pid} stopped.")
        logger.info(f"Stopped monitor process with PID {pid}")
        
    except psutil.NoSuchProcess:
        print(f"🟡 Process {pid} was not found (may have already stopped)")
        # Clean up stale PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as e:
        print(f"❌ Error stopping process: {e}")
        logger.error(f"Error stopping process: {e}")


def restart(interval: int, duration: int):
    """Restart the monitor process."""
    print("🔄 Restarting monitor...")
    stop()
    time.sleep(2)  # Give it a moment
    start(interval, duration)


def status():
    """Display the current status of the monitor."""
    if is_running():
        pid = get_pid()
        try:
            process = psutil.Process(pid)
            start_time = process.create_time()
            start_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
            elapsed = time.time() - start_time
            elapsed_str = f"{elapsed/3600:.1f}h" if elapsed > 3600 else f"{elapsed/60:.1f}m"
            
            print(f"🟢 Monitor is RUNNING with PID {pid}")
            print(f"   Started: {start_time_str}")
            print(f"   Runtime: {elapsed_str}")
            print(f"   Log file: {LOG_FILE}")
        except Exception as e:
            print(f"🟢 Monitor is RUNNING with PID {pid} (details unavailable: {e})")
    else:
        print("🔴 Monitor is STOPPED")
        
        # Check if log file exists and show last few lines
        if os.path.exists(LOG_FILE):
            print(f"   Log file: {LOG_FILE}")
            try:
                with open(LOG_FILE, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print("   Last log entries:")
                        for line in lines[-3:]:
                            print(f"     {line.rstrip()}")
            except Exception as e:
                print(f"   (Could not read log file: {e})")


def ensure_running(interval: int, duration: int):
    """
    Ensure the monitor is running. Start it if it's not.
    This is the core function for automated health checks (e.g., via cron).
    """
    if is_running():
        logger.debug("Monitor is running, no action needed")
        return
    
    logger.info("Monitor is not running, starting it")
    start(interval, duration)


def tail_log(lines: int = 20):
    """Show the last N lines of the log file."""
    if not os.path.exists(LOG_FILE):
        print(f"❌ Log file {LOG_FILE} does not exist")
        return
    
    try:
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
        print(f"📋 Last {len(last_lines)} lines from {LOG_FILE}:")
        print("-" * 50)
        for line in last_lines:
            print(line.rstrip())
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error reading log file: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Manage the Agent Email Monitor background process",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start --interval 2 --duration 0     # Start indefinite monitoring
  %(prog)s stop                                 # Stop monitoring
  %(prog)s status                               # Check status
  %(prog)s restart --interval 1 --duration 120 # Restart with new settings
  %(prog)s ensure-running --interval 2         # Start if not running (for cron)
  %(prog)s logs --lines 50                     # Show last 50 log lines
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'restart', 'status', 'ensure-running', 'logs'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=2,
        help='Check interval in minutes (default: 2)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=0,
        help='Duration to run in minutes, 0 for indefinite (default: 0)'
    )
    
    parser.add_argument(
        '--lines',
        type=int,
        default=20,
        help='Number of log lines to show (for logs command, default: 20)'
    )
    
    args = parser.parse_args()
    
    # Execute the requested command
    if args.command == 'start':
        start(args.interval, args.duration)
    elif args.command == 'stop':
        stop()
    elif args.command == 'restart':
        restart(args.interval, args.duration)
    elif args.command == 'status':
        status()
    elif args.command == 'ensure-running':
        ensure_running(args.interval, args.duration)
    elif args.command == 'logs':
        tail_log(args.lines)


if __name__ == "__main__":
    main()