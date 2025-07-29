#!/usr/bin/env python3
"""
DEPRECATED: Agent Email Communication Protocol

⚠️  WARNING: This file is DEPRECATED and should NOT be used.

Use integrated_agent_coordination.py instead, which provides:
- All functionality from this legacy system
- Enhanced intelligent scheduling 
- Better error handling and negotiation
- Counter-proposal and rejection handling
- Context-aware scheduling decisions

This file has been renamed to prevent accidental imports.
The new system uses [CLAUDE-COORD] prefix instead of [CLAUDE-AGENT].

This module enables Claude Code agents to communicate with each other
through structured email messages with auto-response capabilities.
"""

import json
import base64
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import re

from gmail_functions import GmailManager

# ==================== AGENT EMAIL PROTOCOL ====================

class AgentMessageType(Enum):
    """Types of agent-to-agent messages"""
    COORDINATION_REQUEST = "coordination_request"
    COORDINATION_RESPONSE = "coordination_response"
    SCHEDULE_PROPOSAL = "schedule_proposal"
    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    ACKNOWLEDGMENT = "acknowledgment"

@dataclass
class AgentIdentity:
    """Agent identification for email communication"""
    agent_id: str
    agent_name: str
    user_email: str
    agent_version: str = "1.0"
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["email_coordination", "scheduling", "task_management"]

@dataclass 
class AgentMessage:
    """Structured agent message for email communication"""
    message_id: str
    from_agent: AgentIdentity
    to_agent_email: str
    message_type: AgentMessageType
    timestamp: datetime
    payload: Dict[str, Any]
    requires_response: bool = True
    expires_at: Optional[datetime] = None
    thread_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = self._generate_message_id()
        if self.expires_at is None and self.requires_response:
            self.expires_at = self.timestamp + timedelta(hours=24)
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = str(int(time.time()))
        agent_id = self.from_agent.agent_id
        content_hash = hashlib.md5(json.dumps(self.payload).encode()).hexdigest()[:8]
        return f"agent_{agent_id}_{timestamp}_{content_hash}"

class AgentEmailProtocol:
    """Handles agent-to-agent email communication"""
    
    def __init__(self, agent_identity: AgentIdentity, credentials_file='credentials.json'):
        """
        Initialize agent email protocol.
        
        Args:
            agent_identity: This agent's identity
            credentials_file: OAuth credentials file
        """
        self.agent_identity = agent_identity
        self.gmail = GmailManager(credentials_file)
        
        # Protocol constants
        self.AGENT_SUBJECT_PREFIX = "[CLAUDE-AGENT]"
        self.PROTOCOL_VERSION = "claude_email_v1"
        self.MESSAGE_SEPARATOR = "=== AGENT MESSAGE ==="
        
        print(f"Agent email protocol initialized for {agent_identity.agent_id}")
    
    def send_agent_message(self, agent_message: AgentMessage) -> bool:
        """
        Send structured message to another agent.
        
        Args:
            agent_message: Agent message to send
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Create email subject
            subject = f"{self.AGENT_SUBJECT_PREFIX} {agent_message.message_type.value.title()}"
            
            # Create structured email body
            email_body = self._create_agent_email_body(agent_message)
            
            # Send via Gmail
            result = self.gmail.send_email(
                to_email=agent_message.to_agent_email,
                subject=subject,
                body=email_body
            )
            
            if result:
                print(f"✅ Agent message sent to {agent_message.to_agent_email}")
                return True
            else:
                print(f"❌ Failed to send agent message to {agent_message.to_agent_email}")
                return False
                
        except Exception as e:
            print(f"Error sending agent message: {e}")
            return False
    
    def check_for_agent_messages(self, max_messages=10) -> List[AgentMessage]:
        """
        Check for incoming agent messages.
        
        Args:
            max_messages: Maximum messages to retrieve
            
        Returns:
            List of parsed agent messages
        """
        try:
            # Search for agent emails
            query = f"subject:{self.AGENT_SUBJECT_PREFIX} is:unread"
            messages = self.gmail.get_messages(query=query, max_results=max_messages)
            
            agent_messages = []
            for message in messages:
                parsed_message = self._parse_agent_email(message)
                if parsed_message:
                    agent_messages.append(parsed_message)
                    # Mark as read after parsing
                    self.gmail.mark_as_read(message['id'])
            
            if agent_messages:
                print(f"📬 Found {len(agent_messages)} new agent messages")
            
            return agent_messages
            
        except Exception as e:
            print(f"Error checking for agent messages: {e}")
            return []
    
    def auto_respond_to_agents(self) -> List[Dict[str, Any]]:
        """
        Automatically respond to agent messages that require responses.
        
        Returns:
            List of response results
        """
        incoming_messages = self.check_for_agent_messages()
        responses = []
        
        for message in incoming_messages:
            if message.requires_response:
                response = self._generate_auto_response(message)
                if response:
                    success = self.send_agent_message(response)
                    responses.append({
                        'original_message_id': message.message_id,
                        'response_sent': success,
                        'response_type': response.message_type.value
                    })
        
        return responses
    
    def _create_agent_email_body(self, agent_message: AgentMessage) -> str:
        """Create structured email body for agent message"""
        
        # Human-readable header
        human_summary = self._generate_human_summary(agent_message)
        
        # Structured agent data
        agent_data = {
            'protocol': self.PROTOCOL_VERSION,
            'message_id': agent_message.message_id,
            'from_agent': asdict(agent_message.from_agent),
            'message_type': agent_message.message_type.value,
            'timestamp': agent_message.timestamp.isoformat(),
            'requires_response': agent_message.requires_response,
            'expires_at': agent_message.expires_at.isoformat() if agent_message.expires_at else None,
            'payload': agent_message.payload
        }
        
        # Encode agent data
        encoded_data = base64.b64encode(json.dumps(agent_data).encode()).decode()
        
        # Create email body
        email_body = f"""
{human_summary}

{self.MESSAGE_SEPARATOR}
AGENT_DATA_START
{encoded_data}
AGENT_DATA_END
{self.MESSAGE_SEPARATOR}

This is an automated message between Claude Code agents.
Protocol: {self.PROTOCOL_VERSION}
Agent: {self.agent_identity.agent_id}
"""
        
        return email_body.strip()
    
    def _parse_agent_email(self, gmail_message: Dict[str, Any]) -> Optional[AgentMessage]:
        """Parse Gmail message into AgentMessage"""
        try:
            # Get message body
            body = self.gmail.extract_message_body(gmail_message['payload'])
            
            # Extract agent data
            if self.MESSAGE_SEPARATOR not in body:
                return None
            
            # Find encoded data
            data_start = body.find("AGENT_DATA_START")
            data_end = body.find("AGENT_DATA_END")
            
            if data_start == -1 or data_end == -1:
                return None
            
            encoded_data = body[data_start + len("AGENT_DATA_START"):data_end].strip()
            
            # Decode agent data
            agent_data = json.loads(base64.b64decode(encoded_data).decode())
            
            # Create AgentMessage
            from_agent = AgentIdentity(**agent_data['from_agent'])
            
            return AgentMessage(
                message_id=agent_data['message_id'],
                from_agent=from_agent,
                to_agent_email=self.agent_identity.user_email,
                message_type=AgentMessageType(agent_data['message_type']),
                timestamp=datetime.fromisoformat(agent_data['timestamp']),
                payload=agent_data['payload'],
                requires_response=agent_data['requires_response'],
                expires_at=datetime.fromisoformat(agent_data['expires_at']) if agent_data['expires_at'] else None
            )
            
        except Exception as e:
            print(f"Error parsing agent email: {e}")
            return None
    
    def _generate_human_summary(self, agent_message: AgentMessage) -> str:
        """Generate human-readable summary of agent message"""
        
        message_type = agent_message.message_type.value.replace('_', ' ').title()
        from_agent = agent_message.from_agent.agent_name
        
        summary = f"Agent Communication: {message_type}\n"
        summary += f"From: {from_agent} ({agent_message.from_agent.agent_id})\n"
        summary += f"Time: {agent_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Add payload-specific summary
        if agent_message.message_type == AgentMessageType.COORDINATION_REQUEST:
            if 'meeting_subject' in agent_message.payload:
                summary += f"Subject: {agent_message.payload['meeting_subject']}\n"
        
        elif agent_message.message_type == AgentMessageType.TASK_ASSIGNMENT:
            if 'task_title' in agent_message.payload:
                summary += f"Task: {agent_message.payload['task_title']}\n"
        
        return summary
    
    def _generate_auto_response(self, incoming_message: AgentMessage) -> Optional[AgentMessage]:
        """Generate automatic response to agent message"""
        
        try:
            response_payload = {}
            response_type = AgentMessageType.ACKNOWLEDGMENT
            
            if incoming_message.message_type == AgentMessageType.COORDINATION_REQUEST:
                response_type = AgentMessageType.COORDINATION_RESPONSE
                response_payload = {
                    'original_message_id': incoming_message.message_id,
                    'status': 'received',
                    'processing': True,
                    'estimated_response_time': '15_minutes'
                }
            
            elif incoming_message.message_type == AgentMessageType.SCHEDULE_PROPOSAL:
                response_type = AgentMessageType.COORDINATION_RESPONSE
                response_payload = {
                    'original_message_id': incoming_message.message_id,
                    'proposal_status': 'reviewing',
                    'response_expected': 'within_1_hour'
                }
            
            elif incoming_message.message_type == AgentMessageType.TASK_ASSIGNMENT:
                response_type = AgentMessageType.ACKNOWLEDGMENT
                response_payload = {
                    'original_message_id': incoming_message.message_id,
                    'task_received': True,
                    'status': 'accepted'
                }
            
            # Extract sender's email from the from_agent
            sender_email = incoming_message.from_agent.user_email
            
            return AgentMessage(
                message_id="",  # Will be auto-generated
                from_agent=self.agent_identity,
                to_agent_email=sender_email,
                message_type=response_type,
                timestamp=datetime.now(),
                payload=response_payload,
                requires_response=False
            )
            
        except Exception as e:
            print(f"Error generating auto-response: {e}")
            return None

# ==================== AGENT COORDINATION FUNCTIONS ====================

class UniversalAgentEmailCoordinator:
    """Universal coordinator for any agent email communications"""
    
    def __init__(self, user_email=None, agent_name=None, credentials_file='credentials.json'):
        """Initialize universal agent email coordinator"""
        
        # Use provided details or detect from Gmail authentication
        if user_email is None:
            # Try to get from Gmail authentication
            try:
                from gmail_functions import GmailManager
                gmail = GmailManager()
                profile = gmail.service.users().getProfile(userId='me').execute()
                user_email = profile["emailAddress"]
            except:
                user_email = "agent@example.com"  # Fallback
        
        if agent_name is None:
            agent_name = user_email  # Just use email as the name
        
        # Generate agent ID from email
        email_prefix = user_email.split('@')[0]
        agent_id = f"{email_prefix}_claude_agent"
        
        # Define universal agent identity
        self.agent_identity = AgentIdentity(
            agent_id=agent_id,
            agent_name=agent_name,
            user_email=user_email,
            capabilities=["calendar_scheduling", "task_management", "email_coordination"]
        )
        
        # Initialize email protocol
        self.email_protocol = AgentEmailProtocol(self.agent_identity, credentials_file)
        
        print(f"Universal agent email coordinator initialized for {user_email}")
    
    def send_coordination_request(self, target_email: str, meeting_subject: str, 
                                  meeting_details: Dict[str, Any]) -> bool:
        """Send coordination request to any agent by email"""
        
        payload = {
            'meeting_subject': meeting_subject,
            'meeting_details': meeting_details,
            'coordination_type': 'schedule_meeting',
            'sender_preferences': {
                'preferred_times': ['morning', 'afternoon'],
                'duration_minutes': meeting_details.get('duration', 30),
                'urgency': meeting_details.get('urgency', 'medium')
            }
        }
        
        message = AgentMessage(
            message_id="",
            from_agent=self.agent_identity,
            to_agent_email=target_email,
            message_type=AgentMessageType.COORDINATION_REQUEST,
            timestamp=datetime.now(),
            payload=payload
        )
        
        return self.email_protocol.send_agent_message(message)
    
    def check_and_respond_to_agents(self) -> Dict[str, Any]:
        """Check for agent messages and auto-respond"""
        
        results = {
            'incoming_messages': [],
            'auto_responses': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Check for incoming messages
        incoming = self.email_protocol.check_for_agent_messages()
        results['incoming_messages'] = [
            {
                'from': msg.from_agent.agent_name,
                'type': msg.message_type.value,
                'timestamp': msg.timestamp.isoformat(),
                'requires_response': msg.requires_response
            }
            for msg in incoming
        ]
        
        # Auto-respond
        responses = self.email_protocol.auto_respond_to_agents()
        results['auto_responses'] = responses
        
        return results

# ==================== INTEGRATION FUNCTIONS ====================

# Global coordinator instance
_email_coordinator = None

def initialize_agent_email_coordinator(user_email=None, agent_name=None):
    """Initialize universal agent email coordinator (call once)"""
    global _email_coordinator
    if _email_coordinator is None:
        _email_coordinator = UniversalAgentEmailCoordinator(user_email, agent_name)
    return _email_coordinator

def send_agent_coordination_email(target_email: str, meeting_subject: str, meeting_details: Dict[str, Any]) -> bool:
    """Send coordination email to any agent by email"""
    coordinator = initialize_agent_email_coordinator()
    return coordinator.send_coordination_request(target_email, meeting_subject, meeting_details)

def check_agent_emails_and_respond() -> Dict[str, Any]:
    """Check for agent emails and auto-respond"""
    coordinator = initialize_agent_email_coordinator()
    return coordinator.check_and_respond_to_agents()

def get_agent_email_status() -> Dict[str, Any]:
    """Get agent email system status"""
    coordinator = initialize_agent_email_coordinator()
    return {
        'agent_id': coordinator.agent_identity.agent_id,
        'agent_email': coordinator.agent_identity.user_email,
        'protocol_version': coordinator.email_protocol.PROTOCOL_VERSION,
        'capabilities': coordinator.agent_identity.capabilities,
        'status': 'active'
    }

# ==================== TESTING FUNCTIONS ====================

def test_agent_email_protocol():
    """Test the agent email protocol"""
    print("🧪 Testing Agent Email Protocol")
    print("=" * 40)
    
    try:
        # Initialize coordinator
        coordinator = initialize_agent_email_coordinator()
        print(f"✅ Coordinator initialized: {coordinator.agent_identity.agent_id}")
        
        # Test sending message to Sarah
        meeting_details = {
            'duration': 30,
            'urgency': 'medium',
            'type': '1:1_sync'
        }
        
        result = send_agent_coordination_email("test@example.com", "Test Agent Coordination", meeting_details)
        print(f"✅ Test message sent: {result}")
        
        # Test checking for messages
        status = check_agent_emails_and_respond()
        print(f"✅ Message check complete: {len(status['incoming_messages'])} messages")
        
        # Get status
        system_status = get_agent_email_status()
        print(f"✅ System status: {system_status['status']}")
        
        print("\n🎯 Agent email protocol is ready!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_agent_email_protocol()