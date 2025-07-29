#!/usr/bin/env python3
"""
Agent Configuration System
Makes the coordination system email-agnostic and easily configurable
"""

from typing import Dict, Any
import os

class AgentConfig:
    """Configuration management for agent coordination system"""
    
    @staticmethod
    def get_config_from_env() -> Dict[str, Any]:
        """Get agent configuration from environment variables"""
        return {
            "agent_id": os.getenv("AGENT_ID", "claude_agent_v2"),
            "user_name": os.getenv("USER_NAME", "Claude Agent User"),
            "user_email": os.getenv("USER_EMAIL", "user@example.com"),
            "preferences": {
                "preferred_meeting_times": os.getenv("PREFERRED_TIMES", "morning,afternoon").split(","),
                "max_meetings_per_day": int(os.getenv("MAX_MEETINGS_PER_DAY", "5")),
                "min_meeting_gap_minutes": int(os.getenv("MIN_MEETING_GAP", "15")),
                "focus_time_protection": os.getenv("FOCUS_TIME_PROTECTION", "true").lower() == "true",
                "negotiation_style": os.getenv("NEGOTIATION_STYLE", "collaborative"),
                "response_time_preference": os.getenv("RESPONSE_TIME", "immediate")
            }
        }
    
    @staticmethod
    def create_config(agent_id: str, user_name: str, user_email: str, **kwargs) -> Dict[str, Any]:
        """Create agent configuration programmatically"""
        config = {
            "agent_id": agent_id,
            "user_name": user_name,
            "user_email": user_email,
            "preferences": {
                "preferred_meeting_times": kwargs.get("preferred_meeting_times", ["morning", "afternoon"]),
                "max_meetings_per_day": kwargs.get("max_meetings_per_day", 5),
                "min_meeting_gap_minutes": kwargs.get("min_meeting_gap_minutes", 15),
                "focus_time_protection": kwargs.get("focus_time_protection", True),
                "negotiation_style": kwargs.get("negotiation_style", "collaborative"),
                "response_time_preference": kwargs.get("response_time_preference", "immediate")
            }
        }
        
        return config

# Pre-defined configurations for common setups
AGENT_CONFIGS = {
    "zach": {
        "agent_id": "zach_claude_agent_v2",
        "user_name": "Zach Miller",
        "user_email": "zach@empire.email",
        "preferences": {
            "preferred_meeting_times": ["morning", "afternoon"],
            "max_meetings_per_day": 5,
            "min_meeting_gap_minutes": 15,
            "focus_time_protection": True,
            "negotiation_style": "collaborative",
            "response_time_preference": "immediate"
        }
    },
    
    "sarah": {
        "agent_id": "sarah_claude_agent_v2", 
        "user_name": "Sarah Dawson",
        "user_email": "sarah@empire.email",
        "preferences": {
            "preferred_meeting_times": ["morning", "afternoon"],
            "max_meetings_per_day": 6,
            "min_meeting_gap_minutes": 15,
            "focus_time_protection": True,
            "negotiation_style": "collaborative",
            "response_time_preference": "within_hours"
        }
    },
    
    "generic": {
        "agent_id": "claude_agent_v2",
        "user_name": "Claude Agent User", 
        "user_email": "user@example.com",
        "preferences": {
            "preferred_meeting_times": ["morning", "afternoon"],
            "max_meetings_per_day": 5,
            "min_meeting_gap_minutes": 15,
            "focus_time_protection": True,
            "negotiation_style": "collaborative",
            "response_time_preference": "immediate"
        }
    }
}

def get_agent_config(config_name: str = None) -> Dict[str, Any]:
    """Get agent configuration by name or from environment"""
    
    if config_name and config_name in AGENT_CONFIGS:
        return AGENT_CONFIGS[config_name]
    
    # Try environment variables
    env_config = AgentConfig.get_config_from_env()
    if env_config["user_email"] != "user@example.com":  # Environment vars were set
        return env_config
    
    # Default to Zach's config (update this to your actual default)
    return AGENT_CONFIGS["zach"]

# Convenience functions for easy coordination
def setup_agent_for_user(user_name: str, user_email: str, agent_id: str = None) -> Dict[str, Any]:
    """Quick setup for a specific user"""
    
    if agent_id is None:
        # Generate agent ID from user info
        name_part = user_name.lower().replace(" ", "_")
        agent_id = f"{name_part}_claude_agent_v2"
    
    return AgentConfig.create_config(
        agent_id=agent_id,
        user_name=user_name,
        user_email=user_email
    )

if __name__ == "__main__":
    # Test configuration system
    print("🔧 Agent Configuration System")
    print("=" * 40)
    
    # Show available configs
    print("Available configurations:")
    for name, config in AGENT_CONFIGS.items():
        print(f"  • {name}: {config['user_name']} ({config['user_email']})")
    
    print(f"\nExample usage:")
    print("# Get Zach's configuration")
    print("config = get_agent_config('zach')")
    print("\n# Setup for any user")
    print("config = setup_agent_for_user('John Doe', 'john@company.com')")
    print("\n# Use environment variables")
    print("export USER_NAME='Jane Smith'")
    print("export USER_EMAIL='jane@company.com'")
    print("config = get_agent_config()")