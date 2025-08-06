#!/usr/bin/env python3
"""
Integrated Agent Coordination System
Combines email communication protocol with sophisticated agent coordination
Compatible with Sarah's Google Daemon Phase 2 system
"""

import json
import uuid
import logging
import base64
import hashlib
import time
import re
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import dateutil.parser
except ImportError:
    logger.warning("dateutil not available, falling back to basic time parsing")

from gmail_functions import GmailManager
from calendar_functions import CalendarManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ENHANCED PROTOCOL CLASSES ====================

class MessageType(Enum):
    """Agent coordination message types"""
    SCHEDULE_REQUEST = "schedule_request"
    SCHEDULE_PROPOSAL = "schedule_proposal"
    SCHEDULE_COUNTER_PROPOSAL = "schedule_counter_proposal"
    SCHEDULE_CONFIRMATION = "schedule_confirmation"
    SCHEDULE_REJECTION = "schedule_rejection"
    AVAILABILITY_QUERY = "availability_query"
    AVAILABILITY_RESPONSE = "availability_response"
    CONTEXT_UPDATE = "context_update"
    COORDINATION_ACK = "coordination_ack"


class NegotiationStrategy(Enum):
    """Negotiation strategies for scheduling coordination"""
    COLLABORATIVE = "collaborative"  # Optimize for mutual benefit (recommended)
    ASSERTIVE = "assertive"          # Prioritize your preferences
    ACCOMMODATING = "accommodating"   # Flexible to other's needs
    ADAPTIVE = "adaptive"            # Adapt strategy based on context

class WorkloadLevel(Enum):
    """Workload intensity levels"""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    CRITICAL = "critical"

class EnergyLevel(Enum):
    """Energy levels throughout the day"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class AgentIdentity:
    """Enhanced agent identity for coordination system"""
    agent_id: str
    user_name: str
    user_email: str
    agent_version: str = "2.0"
    capabilities: List[str] = None
    timezone: str = "America/New_York"
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = [
                "calendar_access", 
                "scheduling_coordination", 
                "multi_agent_communication",
                "email_coordination",
                "context_awareness"
            ]

@dataclass
class MeetingContext:
    """Context for meeting scheduling requests"""
    meeting_type: str  # "1:1", "team_meeting", "client_call", etc.
    duration_minutes: int
    attendees: List[str]
    subject: str
    description: Optional[str] = None
    energy_requirement: str = "medium"  # "low", "medium", "high"
    requires_preparation: bool = False

@dataclass
class TimeSlot:
    """Represents a proposed meeting time slot"""
    start_time: datetime
    end_time: datetime
    confidence_score: float  # 0.0-1.0 how good this slot is
    conflicts: List[str] = None
    context_score: Dict[str, float] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []
        if self.context_score is None:
            self.context_score = {}

@dataclass
class SchedulingPreferences:
    """Agent's scheduling preferences and constraints"""
    preferred_meeting_times: List[str]  # ["morning", "afternoon", "evening"]
    max_meetings_per_day: int = 6
    min_meeting_gap_minutes: int = 15
    focus_time_protection: bool = True
    energy_level_optimization: bool = True
    negotiation_style: str = "collaborative"
    response_time_preference: str = "within_hours"  # "immediate", "within_hours"

@dataclass
class ContextualFactors:
    """Contextual factors affecting scheduling decisions"""
    current_workload: WorkloadLevel
    energy_level: EnergyLevel
    deadline_pressure: str = "medium"  # "low", "medium", "high"
    meetings_today: int = 3
    focus_time_remaining: int = 240  # minutes

@dataclass
class CoordinationMessage:
    """Enhanced coordination message structure with email transport"""
    message_id: str
    message_type: MessageType
    from_agent: AgentIdentity
    to_agent_email: str
    timestamp: datetime
    conversation_id: str
    payload: Dict[str, Any]
    expires_at: Optional[datetime] = None
    requires_response: bool = True
    transport_method: str = "email"  # "email", "calendar", "document"
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = self._generate_message_id()
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())
        if self.expires_at is None and self.requires_response:
            self.expires_at = self.timestamp + timedelta(hours=24)
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = str(int(time.time()))
        agent_id = self.from_agent.agent_id
        content_hash = hashlib.md5(json.dumps(self.payload).encode()).hexdigest()[:8]
        return f"coord_{agent_id}_{timestamp}_{content_hash}"

# ==================== EMAIL TRANSPORT LAYER ====================

class EmailTransportLayer:
    """Handles email-based agent communication transport with threading support"""
    
    def __init__(self, agent_identity: AgentIdentity, credentials_file='credentials.json'):
        """Initialize email transport layer"""
        self.agent_identity = agent_identity
        self.gmail = GmailManager(credentials_file)
        
        # Email protocol constants
        self.AGENT_SUBJECT_PREFIX = "[CLAUDE-COORD]"
        self.PROTOCOL_VERSION = "agent_coord_v2"
        self.MESSAGE_SEPARATOR = "=== AGENT COORDINATION ==="
        
        # Threading state for conversation continuity
        self.conversation_threading: Dict[str, Dict[str, Any]] = {}
        
        # Message tracking to prevent duplicate processing
        self.processed_messages_file = "processed_messages.json"
        self.processed_message_ids: set = set()
        self._load_processed_message_ids()
        # conversation_id -> {
        #   'message_ids': [list of message IDs in order],
        #   'subject': 'conversation subject',
        #   'participants': [list of email addresses],
        #   'thread_id': 'gmail thread ID for archiving'
        # }
        
        logger.info(f"Email transport initialized for {agent_identity.agent_id}")
    
    def send_coordination_message(self, message: CoordinationMessage) -> bool:
        """Send coordination message via email with proper threading"""
        try:
            # CRITICAL: Prevent self-email bug - never send coordination messages to ourselves
            if message.to_agent_email == self.agent_identity.user_email:
                logger.error(f"Self-email prevented: attempted to send coordination message to self ({message.to_agent_email})")
                logger.error(f"Message type: {message.message_type.value}, Conversation: {message.conversation_id}")
                return False
            
            # Validate recipient email
            if not message.to_agent_email or '@' not in message.to_agent_email:
                logger.error(f"Invalid recipient email: {message.to_agent_email}")
                return False
            
            # Create email subject with conversation context
            base_subject = f"{self.AGENT_SUBJECT_PREFIX} {message.message_type.value.replace('_', ' ').title()}"
            
            # Generate threading headers for conversation continuity
            threading_headers = self._generate_threading_headers(message, base_subject)
            
            # Create structured email body
            email_body = self._create_coordination_email_body(message)
            
            # Send via Gmail with threading headers
            result = self.gmail.send_email(
                to_email=message.to_agent_email,
                subject=threading_headers['subject'],
                body=email_body,
                threading_headers={
                    'message_id': threading_headers['message_id'],
                    'in_reply_to': threading_headers.get('in_reply_to'),
                    'references': threading_headers.get('references')
                }
            )
            
            if result:
                # Fetch the sent message to get Gmail's actual Message-ID
                gmail_message_id = None
                try:
                    sent_message = self.gmail.service.users().messages().get(
                        userId='me',
                        id=result['id']
                    ).execute()
                    
                    # Extract the actual Message-ID that Gmail assigned
                    headers = sent_message['payload'].get('headers', [])
                    for header in headers:
                        if header['name'].lower() == 'message-id':
                            gmail_message_id = header['value']
                            break
                    
                    if gmail_message_id:
                        logger.info(f"Gmail assigned Message-ID: {gmail_message_id}")
                    else:
                        logger.warning("Could not extract Gmail Message-ID from sent message")
                        
                except Exception as e:
                    logger.error(f"Error fetching sent message for Message-ID: {e}")
                
                # Update conversation threading state with Gmail's actual Message-ID
                self._update_conversation_threading(
                    message, 
                    gmail_message_id or threading_headers['message_id'],  # Fallback to custom if Gmail ID not found
                    result.get('threadId')
                )
                
                logger.info(f"Coordination message sent to {message.to_agent_email} (threaded)")
                logger.info(f"  Conversation: {message.conversation_id}")
                logger.info(f"  Custom Message-ID: {threading_headers['message_id']}")
                if gmail_message_id:
                    logger.info(f"  Gmail Message-ID: {gmail_message_id}")
                if result.get('threadId'):
                    logger.info(f"  Thread-ID: {result['threadId']}")
                return True
            else:
                logger.error(f"Failed to send coordination message to {message.to_agent_email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending coordination message: {e}")
            return False
    
    def check_for_coordination_messages(self, max_messages=10) -> List[CoordinationMessage]:
        """Check for incoming coordination messages"""
        try:
            # Use time-based query instead of read status to prevent issues when humans open emails
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
            query = f"subject:{self.AGENT_SUBJECT_PREFIX} after:{yesterday}"
            messages = self.gmail.get_messages(query=query, max_results=max_messages)
            
            coordination_messages = []
            for message in messages:
                # Skip messages we've already processed
                message_id = message['id']
                if message_id in self.processed_message_ids:
                    continue
                    
                parsed_message = self._parse_coordination_email(message)
                if parsed_message:
                    # CRITICAL: Skip messages from ourselves to prevent processing our own coordination messages
                    if parsed_message.from_agent.user_email == self.agent_identity.user_email:
                        logger.debug(f"Skipping self-sent message from {parsed_message.from_agent.user_email}")
                        # Track as processed to prevent re-checking
                        self.processed_message_ids.add(message_id)
                        continue
                    
                    coordination_messages.append(parsed_message)
                    # Track as processed to prevent duplicate handling
                    self.processed_message_ids.add(message_id)
                    # Still mark as read for user convenience
                    self.gmail.mark_as_read(message_id)
            
            if coordination_messages:
                logger.info(f"Found {len(coordination_messages)} new coordination messages")
                # Save processed message IDs to persistent storage
                self._save_processed_message_ids()
            
            return coordination_messages
            
        except Exception as e:
            logger.error(f"Error checking for coordination messages: {e}")
            return []
    
    def _create_coordination_email_body(self, message: CoordinationMessage) -> str:
        """Create structured email body for coordination message"""
        
        # Human-readable header
        human_summary = self._generate_human_summary(message)
        
        # Generate comprehensive human-readable content
        
        # Create structured payload data for machine processing
        structured_payload = self._create_structured_payload_data(message)
        
        # Create email body - human readable summary + complete technical data
        email_body = f"""
{human_summary}

{self.MESSAGE_SEPARATOR}
Message ID: {message.message_id}
Conversation: {message.conversation_id}
From Agent: {self.agent_identity.agent_id}
Message Type: {message.message_type.value}
Protocol: {self.PROTOCOL_VERSION}
{structured_payload}
"""
        
        return email_body.strip()
    
    def _create_structured_payload_data(self, message: CoordinationMessage) -> str:
        """Create structured technical data section for complete payload transmission"""
        import json
        
        structured_lines = []
        
        # Debug logging
        logger.info(f"Creating structured payload for message type: {message.message_type}")
        logger.info(f"Payload keys available: {list(message.payload.keys())}")
        
        # Add structured payload data based on message type
        if message.message_type == MessageType.SCHEDULE_PROPOSAL:
            if 'proposed_times' in message.payload:
                # Include ALL proposed time slots in structured format
                proposed_times = message.payload['proposed_times']
                logger.info(f"Found proposed_times with {len(proposed_times)} slots")
                structured_lines.append(f"Proposed Times Count: {len(proposed_times)}")
                structured_lines.append("Proposed Times Data: " + json.dumps(proposed_times, default=str))
            else:
                logger.warning("No 'proposed_times' found in SCHEDULE_PROPOSAL payload")
                
            if 'proposal_confidence' in message.payload:
                structured_lines.append(f"Proposal Confidence: {message.payload['proposal_confidence']}")
                
        elif message.message_type == MessageType.SCHEDULE_REQUEST:
            if 'meeting_context' in message.payload:
                meeting_context = message.payload['meeting_context']
                structured_lines.append("Meeting Context: " + json.dumps(meeting_context, default=str))
                
            if 'time_preferences' in message.payload:
                structured_lines.append("Time Preferences: " + json.dumps(message.payload['time_preferences']))
                
        elif message.message_type == MessageType.SCHEDULE_CONFIRMATION:
            if 'selected_time' in message.payload:
                selected_time = message.payload['selected_time']
                structured_lines.append("Selected Time: " + json.dumps(selected_time, default=str))
                
        elif message.message_type == MessageType.SCHEDULE_REJECTION:
            if 'rejection_reason' in message.payload:
                structured_lines.append(f"Rejection Reason: {message.payload['rejection_reason']}")
        
        # Return formatted structured data section
        if structured_lines:
            result = "\n" + "\n".join(structured_lines)
            logger.info(f"Generated structured data with {len(result)} characters")
            return result
        else:
            logger.warning("No structured data generated - returning empty string")
            return ""
    
    def _parse_coordination_email(self, gmail_message: Dict[str, Any]) -> Optional[CoordinationMessage]:
        """Parse Gmail message into CoordinationMessage from human-readable format"""
        try:
            # Get message body
            body = self.gmail.extract_message_body(gmail_message['payload'])
            
            # Extract coordination data from technical identifiers
            if self.MESSAGE_SEPARATOR not in body:
                return None
            
            # Split body to get technical section
            parts = body.split(self.MESSAGE_SEPARATOR)
            if len(parts) < 2:
                return None
            
            human_content = parts[0].strip()
            technical_section = parts[1].strip()
            
            # Extract technical identifiers
            tech_data = {}
            for line in technical_section.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    tech_data[key.strip()] = value.strip()
            
            # Extract payload from structured technical data first, fallback to human-readable content
            payload = self._extract_payload_from_technical_data(tech_data, tech_data.get('Message Type', ''))
            
            # If no structured payload found, fallback to human-readable parsing
            if not payload or not self._is_payload_complete(payload, tech_data.get('Message Type', '')):
                logger.debug("Using fallback human-readable payload extraction")
                human_payload = self._extract_payload_from_human_content(human_content, tech_data.get('Message Type', ''))
                # Merge payloads, prioritizing technical data
                for key, value in human_payload.items():
                    if key not in payload:
                        payload[key] = value
            
            # Parse from email headers for additional info
            headers = gmail_message['payload'].get('headers', [])
            from_email = None
            subject = None
            for header in headers:
                if header['name'].lower() == 'from':
                    from_email = header['value']
                elif header['name'].lower() == 'subject':
                    subject = header['value']
            
            # Validate sender email - reject if missing or invalid
            if not from_email or '@' not in from_email or 'example.com' in from_email:
                logger.warning(f"Invalid sender email in coordination message: {from_email}")
                return None
            
            # Create simplified agent identity (we may not have full details)
            from_agent = AgentIdentity(
                agent_id=tech_data.get('From Agent', 'unknown_agent'),
                user_name=from_email.split('@')[0] if from_email else 'Unknown User',
                user_email=from_email
            )
            
            
            # Determine if response is needed
            requires_response = 'Response Needed:' in human_content
            
            # Extract Message-ID from email for threading
            received_message_id = self._extract_message_id_from_email(gmail_message)
            conversation_id = tech_data.get('Conversation', str(uuid.uuid4()))
            
            # Update conversation threading state with received message
            if received_message_id and conversation_id:
                self._update_received_message_threading(conversation_id, received_message_id, from_email)
            
            return CoordinationMessage(
                message_id=tech_data.get('Message ID', str(uuid.uuid4())),
                message_type=MessageType(tech_data.get('Message Type', 'coordination_ack')),
                from_agent=from_agent,
                to_agent_email=self.agent_identity.user_email,
                timestamp=datetime.now(),  # Use current time as fallback
                conversation_id=conversation_id,
                payload=payload,
                requires_response=requires_response,
                expires_at=None  # Could be extracted from human content if needed
            )
            
        except Exception as e:
            logger.error(f"Error parsing coordination email: {e}")
            return None
    
    def _extract_payload_from_human_content(self, human_content: str, message_type: str) -> Dict[str, Any]:
        """Extract payload data from human-readable content"""
        payload = {}
        
        try:
            lines = human_content.split('\n')
            
            # Extract different information based on message type
            if message_type == 'schedule_request':
                meeting_context = {}
                for line in lines:
                    if line.startswith('• Meeting:'):
                        meeting_context['subject'] = line.split(':', 1)[1].strip()
                    elif line.startswith('• Duration:'):
                        duration_text = line.split(':', 1)[1].strip()
                        # Extract number from "60 minutes"
                        duration_match = re.search(r'(\d+)', duration_text)
                        if duration_match:
                            meeting_context['duration_minutes'] = int(duration_match.group(1))
                    elif line.startswith('• Participants:'):
                        participants = line.split(':', 1)[1].strip()
                        meeting_context['attendees'] = [p.strip() for p in participants.split(',')]
                    elif line.startswith('• Description:'):
                        meeting_context['description'] = line.split(':', 1)[1].strip()
                    elif line.startswith('• Type:'):
                        meeting_context['meeting_type'] = line.split(':', 1)[1].strip()
                
                if meeting_context:
                    payload['meeting_context'] = meeting_context
            
            elif message_type == 'schedule_proposal':
                proposed_times = []
                for line in lines:
                    if line.strip().startswith('Option '):
                        # Extract time from "Option 1: Tuesday, January 30 at 10:00 AM - 11:00 AM"
                        time_part = line.split(':', 1)[1].strip()
                        if ' - ' in time_part:
                            start_time, end_time = time_part.split(' - ', 1)
                            proposed_times.append({
                                'start_time': start_time.strip(),
                                'end_time': end_time.strip(),
                                'confidence_score': 0.8,  # Default confidence for human-parsed times
                                'conflicts': [],
                                'context_score': {}
                            })
                
                if proposed_times:
                    payload['proposed_times'] = proposed_times
            
            elif message_type == 'schedule_confirmation':
                for line in lines:
                    if line.startswith('• Confirmed Time:'):
                        confirmed_time = line.split(':', 1)[1].strip()
                        payload['confirmed_time'] = {
                            'start_time': confirmed_time,
                            'confidence_score': 0.9,  # High confidence for confirmed times
                            'conflicts': [],
                            'context_score': {}
                        }
                    elif line.startswith('• Location:'):
                        payload.setdefault('meeting_details', {})['location'] = line.split(':', 1)[1].strip()
                    elif line.startswith('• Meeting Link:'):
                        payload.setdefault('meeting_details', {})['meeting_link'] = line.split(':', 1)[1].strip()
            
            elif message_type == 'schedule_rejection':
                for line in lines:
                    if line.startswith('• Reason:'):
                        payload['reason'] = line.split(':', 1)[1].strip()
                    elif line.startswith('• Suggestion:'):
                        payload['alternative_suggestion'] = line.split(':', 1)[1].strip()
        
        except Exception as e:
            logger.error(f"Error extracting payload from human content: {e}")
        
        return payload
    
    def _extract_payload_from_technical_data(self, tech_data: Dict[str, str], message_type: str) -> Dict[str, Any]:
        """Extract payload data from structured technical data section with enhanced error handling"""
        import json
        payload = {}
        
        if not tech_data or not isinstance(tech_data, dict):
            logger.warning("Technical data is empty or invalid")
            return payload
        
        try:
            if message_type == 'schedule_proposal':
                # Extract structured proposed times data
                if 'Proposed Times Data' in tech_data:
                    try:
                        proposed_times_json = tech_data['Proposed Times Data']
                        if proposed_times_json and proposed_times_json.strip():
                            proposed_times = json.loads(proposed_times_json)
                            if isinstance(proposed_times, list) and len(proposed_times) > 0:
                                # Validate each time slot has required fields
                                valid_times = []
                                for i, time_slot in enumerate(proposed_times):
                                    if isinstance(time_slot, dict) and 'start_time' in time_slot and 'end_time' in time_slot:
                                        # Ensure required fields with defaults
                                        time_slot.setdefault('confidence_score', 0.8)
                                        time_slot.setdefault('conflicts', [])
                                        time_slot.setdefault('context_score', {})
                                        valid_times.append(time_slot)
                                    else:
                                        logger.warning(f"Invalid time slot at index {i}: {time_slot}")
                                
                                if valid_times:
                                    payload['proposed_times'] = valid_times
                                    logger.info(f"Extracted {len(valid_times)} valid time slots from structured data")
                                else:
                                    logger.warning("No valid time slots found in structured data")
                            else:
                                logger.warning("Proposed times JSON is not a valid list")
                        else:
                            logger.warning("Proposed Times Data is empty")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse proposed times JSON: {e}")
                    except Exception as e:
                        logger.error(f"Error processing proposed times data: {e}")
                
                if 'Proposal Confidence' in tech_data:
                    try:
                        confidence_value = tech_data['Proposal Confidence']
                        if confidence_value and confidence_value.strip():
                            payload['proposal_confidence'] = float(confidence_value)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid proposal confidence value: {e}")
                        
            elif message_type == 'schedule_request':
                if 'Meeting Context' in tech_data:
                    try:
                        meeting_context_json = tech_data['Meeting Context']
                        if meeting_context_json and meeting_context_json.strip():
                            meeting_context = json.loads(meeting_context_json)
                            if isinstance(meeting_context, dict):
                                payload['meeting_context'] = meeting_context
                            else:
                                logger.warning("Meeting context JSON is not a valid object")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse meeting context JSON: {e}")
                    except Exception as e:
                        logger.error(f"Error processing meeting context: {e}")
                
                if 'Time Preferences' in tech_data:
                    try:
                        time_prefs_json = tech_data['Time Preferences']
                        if time_prefs_json and time_prefs_json.strip():
                            time_preferences = json.loads(time_prefs_json)
                            if isinstance(time_preferences, dict):
                                payload['time_preferences'] = time_preferences
                            else:
                                logger.warning("Time preferences JSON is not a valid object")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse time preferences JSON: {e}")
                    except Exception as e:
                        logger.error(f"Error processing time preferences: {e}")
                        
            elif message_type == 'schedule_confirmation':
                if 'Selected Time' in tech_data:
                    try:
                        selected_time_json = tech_data['Selected Time']
                        if selected_time_json and selected_time_json.strip():
                            selected_time = json.loads(selected_time_json)
                            if isinstance(selected_time, dict) and 'start_time' in selected_time and 'end_time' in selected_time:
                                # Ensure required fields with defaults
                                selected_time.setdefault('confidence_score', 0.9)
                                selected_time.setdefault('conflicts', [])
                                selected_time.setdefault('context_score', {})
                                payload['selected_time'] = selected_time
                            else:
                                logger.warning("Selected time JSON is not a valid time slot object")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse selected time JSON: {e}")
                    except Exception as e:
                        logger.error(f"Error processing selected time: {e}")
                        
            elif message_type == 'schedule_rejection':
                if 'Rejection Reason' in tech_data:
                    reason = tech_data['Rejection Reason']
                    if reason and reason.strip():
                        payload['rejection_reason'] = reason.strip()
            
        except Exception as e:
            logger.error(f"Critical error extracting payload from technical data: {e}")
            logger.error(f"Tech data: {tech_data}")
        
        return payload
    
    def _is_payload_complete(self, payload: Dict[str, Any], message_type: str) -> bool:
        """Check if payload contains the essential data for the message type with enhanced validation"""
        try:
            if not payload or not isinstance(payload, dict):
                logger.debug(f"Payload is empty or invalid for {message_type}")
                return False
            
            if message_type == 'schedule_proposal':
                # Check for proposed_times
                if 'proposed_times' not in payload:
                    logger.debug("Missing proposed_times in schedule_proposal payload")
                    return False
                
                proposed_times = payload['proposed_times']
                if not isinstance(proposed_times, list) or len(proposed_times) == 0:
                    logger.debug("proposed_times is not a valid list or is empty")
                    return False
                
                # Validate each time slot has the minimum required fields
                for i, time_slot in enumerate(proposed_times):
                    if not isinstance(time_slot, dict):
                        logger.debug(f"Time slot {i} is not a dictionary")
                        return False
                    if 'start_time' not in time_slot or 'end_time' not in time_slot:
                        logger.debug(f"Time slot {i} missing start_time or end_time")
                        return False
                
                return True
                
            elif message_type == 'schedule_request':
                if 'meeting_context' not in payload:
                    logger.debug("Missing meeting_context in schedule_request payload")
                    return False
                
                meeting_context = payload['meeting_context']
                if not isinstance(meeting_context, dict):
                    logger.debug("meeting_context is not a dictionary")
                    return False
                
                return True
                
            elif message_type == 'schedule_confirmation':
                if 'selected_time' not in payload:
                    logger.debug("Missing selected_time in schedule_confirmation payload")
                    return False
                
                selected_time = payload['selected_time']
                if not isinstance(selected_time, dict):
                    logger.debug("selected_time is not a dictionary")
                    return False
                
                if 'start_time' not in selected_time or 'end_time' not in selected_time:
                    logger.debug("selected_time missing start_time or end_time")
                    return False
                
                return True
                
            elif message_type == 'schedule_rejection':
                if 'rejection_reason' not in payload:
                    logger.debug("Missing rejection_reason in schedule_rejection payload")
                    return False
                
                reason = payload['rejection_reason']
                if not isinstance(reason, str) or not reason.strip():
                    logger.debug("rejection_reason is not a valid string")
                    return False
                
                return True
                
            elif message_type == 'schedule_counter_proposal':
                if 'counter_proposals' not in payload:
                    logger.debug("Missing counter_proposals in schedule_counter_proposal payload")
                    return False
                
                counter_proposals = payload['counter_proposals']
                if not isinstance(counter_proposals, list) or len(counter_proposals) == 0:
                    logger.debug("counter_proposals is not a valid list or is empty")
                    return False
                
                # Validate each counter-proposal
                for i, time_slot in enumerate(counter_proposals):
                    if not isinstance(time_slot, dict):
                        logger.debug(f"Counter-proposal {i} is not a dictionary")
                        return False
                    if 'start_time' not in time_slot or 'end_time' not in time_slot:
                        logger.debug(f"Counter-proposal {i} missing start_time or end_time")
                        return False
                
                return True
            
            # For other message types, assume complete but log
            logger.debug(f"Unknown message type {message_type}, assuming payload is complete")
            return True
            
        except Exception as e:
            logger.error(f"Error validating payload completeness for {message_type}: {e}")
            return False
    
    def _generate_human_summary(self, message: CoordinationMessage) -> str:
        """Generate comprehensive human-readable coordination message"""
        
        # Header with clear message type
        if message.message_type == MessageType.SCHEDULE_REQUEST:
            header = "MEETING REQUEST"
        elif message.message_type == MessageType.SCHEDULE_PROPOSAL:
            header = "MEETING PROPOSAL"
        elif message.message_type == MessageType.SCHEDULE_COUNTER_PROPOSAL:
            header = "ALTERNATIVE PROPOSAL"
        elif message.message_type == MessageType.SCHEDULE_CONFIRMATION:
            header = "MEETING CONFIRMED"
        elif message.message_type == MessageType.SCHEDULE_REJECTION:
            header = "REQUEST DECLINED"
        elif message.message_type == MessageType.AVAILABILITY_QUERY:
            header = "AVAILABILITY CHECK"
        elif message.message_type == MessageType.AVAILABILITY_RESPONSE:
            header = "AVAILABILITY RESPONSE"
        else:
            header = message.message_type.value.replace('_', ' ').upper()
        
        summary = f"{header}\n"
        summary += f"• From: {message.from_agent.user_name}'s Assistant\n"
        summary += f"• Sent: {message.timestamp.strftime('%B %d, %Y at %I:%M %p')}\n"
        
        # Add detailed payload information based on message type
        if message.message_type == MessageType.SCHEDULE_REQUEST:
            if 'meeting_context' in message.payload:
                ctx = message.payload['meeting_context']
                summary += f"• Meeting: {ctx.get('subject', 'Meeting')}\n"
                summary += f"• Duration: {ctx.get('duration_minutes', 30)} minutes\n"
                if 'attendees' in ctx:
                    attendees = ', '.join(ctx['attendees'])
                    summary += f"• Participants: {attendees}\n"
                if 'description' in ctx and ctx['description']:
                    summary += f"• Description: {ctx['description']}\n"
                if 'meeting_type' in ctx:
                    summary += f"• Type: {ctx['meeting_type']}\n"
            
            if 'preferences' in message.payload:
                prefs = message.payload['preferences']
                if 'preferred_times' in prefs:
                    summary += f"• Preferred Times: {', '.join(prefs['preferred_times'])}\n"
                if 'time_constraints' in prefs:
                    summary += f"• Constraints: {prefs['time_constraints']}\n"
        
        elif message.message_type == MessageType.SCHEDULE_PROPOSAL:
            if 'proposed_times' in message.payload:
                times = message.payload['proposed_times']
                summary += f"• Available Options: {len(times)} time slots\n"
                for i, time_slot in enumerate(times[:3], 1):  # Show first 3 options
                    if isinstance(time_slot, dict):
                        start = time_slot.get('start_time', 'N/A')
                        end = time_slot.get('end_time', 'N/A')
                        if start != 'N/A' and end != 'N/A':
                            try:
                                start_dt = datetime.fromisoformat(start) if isinstance(start, str) else start
                                end_dt = datetime.fromisoformat(end) if isinstance(end, str) else end
                                summary += f"  Option {i}: {start_dt.strftime('%A, %B %d at %I:%M %p')} - {end_dt.strftime('%I:%M %p')}\n"
                            except:
                                summary += f"  Option {i}: {start} - {end}\n"
                if len(times) > 3:
                    summary += f"  ... and {len(times) - 3} more options\n"
            
            if 'context' in message.payload:
                ctx = message.payload['context']
                if 'workload_note' in ctx:
                    summary += f"• Schedule Note: {ctx['workload_note']}\n"
        
        elif message.message_type == MessageType.SCHEDULE_COUNTER_PROPOSAL:
            if 'counter_times' in message.payload:
                times = message.payload['counter_times']
                summary += f"• Alternative Options: {len(times)} time slots\n"
                for i, time_slot in enumerate(times[:3], 1):
                    if isinstance(time_slot, dict):
                        start = time_slot.get('start_time', 'N/A')
                        if start != 'N/A':
                            try:
                                start_dt = datetime.fromisoformat(start) if isinstance(start, str) else start
                                summary += f"  Option {i}: {start_dt.strftime('%A, %B %d at %I:%M %p')}\n"
                            except:
                                summary += f"  Option {i}: {start}\n"
            
            if 'reason' in message.payload:
                summary += f"• Reason: {message.payload['reason']}\n"
        
        elif message.message_type == MessageType.SCHEDULE_CONFIRMATION:
            if 'confirmed_time' in message.payload:
                time_info = message.payload['confirmed_time']
                if isinstance(time_info, dict):
                    start = time_info.get('start_time', 'N/A')
                    if start != 'N/A':
                        try:
                            start_dt = datetime.fromisoformat(start) if isinstance(start, str) else start
                            summary += f"• Confirmed Time: {start_dt.strftime('%A, %B %d at %I:%M %p')}\n"
                        except:
                            summary += f"• Confirmed Time: {start}\n"
            
            if 'meeting_details' in message.payload:
                details = message.payload['meeting_details']
                if 'location' in details:
                    summary += f"• Location: {details['location']}\n"
                if 'meeting_link' in details:
                    summary += f"• Meeting Link: {details['meeting_link']}\n"
            
            summary += "• Status: Calendar invite will be sent\n"
        
        elif message.message_type == MessageType.SCHEDULE_REJECTION:
            # Always show rejection reason with proper validation
            reason = message.payload.get('rejection_reason') or message.payload.get('reason')
            if reason and reason.strip() and not reason.strip().lower() in ["no reason provided", "none", "n/a"]:
                summary += f"• Reason: {reason}\n"
            else:
                # This should never happen with proper validation, but handle gracefully
                summary += "• Reason: [ERROR] Rejection received without meaningful reason - protocol violation\n"
            if 'alternative_suggestion' in message.payload:
                summary += f"• Suggestion: {message.payload['alternative_suggestion']}\n"
            elif 'alternative_suggestions' in message.payload:
                suggestions = message.payload['alternative_suggestions']
                if suggestions and len(suggestions) > 0:
                    summary += f"• Suggestions: {', '.join(suggestions[:2])}\n"
        
        elif message.message_type == MessageType.AVAILABILITY_QUERY:
            if 'query_period' in message.payload:
                summary += f"• Time Period: {message.payload['query_period']}\n"
            if 'duration_needed' in message.payload:
                summary += f"• Duration Needed: {message.payload['duration_needed']} minutes\n"
        
        elif message.message_type == MessageType.AVAILABILITY_RESPONSE:
            if 'available_slots' in message.payload:
                slots = message.payload['available_slots']
                summary += f"• Available Slots: {len(slots)} options found\n"
                for i, slot in enumerate(slots[:3], 1):
                    if isinstance(slot, dict) and 'start_time' in slot:
                        start = slot['start_time']
                        try:
                            start_dt = datetime.fromisoformat(start) if isinstance(start, str) else start
                            summary += f"  Slot {i}: {start_dt.strftime('%A, %B %d at %I:%M %p')}\n"
                        except:
                            summary += f"  Slot {i}: {start}\n"
        
        # Add conversation context if available
        if hasattr(message, 'conversation_id') and message.conversation_id:
            summary += f"• Conversation ID: {message.conversation_id}\n"
        
        # Add response requirement
        if message.requires_response:
            if hasattr(message, 'expires_at') and message.expires_at:
                expire_time = message.expires_at.strftime('%B %d at %I:%M %p')
                summary += f"• Response Needed: By {expire_time}\n"
            else:
                summary += "• Response Needed: Yes\n"
        
        return summary.strip()
    
    def _generate_threading_headers(self, message: CoordinationMessage, base_subject: str) -> Dict[str, str]:
        """Generate email threading headers for proper Gmail conversation threading"""
        import socket
        import time
        
        # Generate unique Message-ID for this message
        timestamp = str(int(time.time() * 1000))  # milliseconds for uniqueness
        hostname = socket.gethostname() or "localhost"
        message_id = f"<coord-{message.conversation_id}-{message.message_id}-{timestamp}@{hostname}>"
        
        threading_headers = {
            'message_id': message_id,
            'subject': base_subject
        }
        
        conv_id = message.conversation_id
        
        # Create consistent subject based on conversation content
        if hasattr(message, 'payload') and message.payload:
            if 'meeting_context' in message.payload:
                ctx = message.payload['meeting_context']
                if isinstance(ctx, dict) and 'subject' in ctx:
                    meeting_subject = ctx['subject']
                    threading_headers['subject'] = f"{self.AGENT_SUBJECT_PREFIX} {meeting_subject}"
        
        # Initialize conversation threading info if not exists
        if conv_id not in self.conversation_threading:
            self.conversation_threading[conv_id] = {
                'message_ids': [],
                'subject': threading_headers['subject'],
                'participants': [self.agent_identity.user_email, message.to_agent_email],
                'thread_id': None,
                'latest_message_id': None  # Track latest actual Gmail message ID for proper threading
            }
        
        # For replies in existing conversations, use ACTUAL Gmail message IDs for proper threading
        conv_info = self.conversation_threading[conv_id]
        
        # Use threading whenever we have a prior message to reply to (regardless of message type)
        if conv_info.get('latest_message_id'):
            # Extract the actual Message-ID header from Gmail format
            latest_msg_id = conv_info['latest_message_id']
            threading_headers['in_reply_to'] = latest_msg_id
            
            # Build References chain with all previous message IDs
            if conv_info['message_ids']:
                # Use actual Gmail message IDs for References header
                references = ' '.join(conv_info['message_ids'][-5:])  # Last 5 for manageability
                if latest_msg_id not in references:
                    references += f' {latest_msg_id}'
                threading_headers['references'] = references
            else:
                threading_headers['references'] = latest_msg_id
                
            logger.debug(f"Threading reply to latest message: {latest_msg_id}")
        else:
            logger.warning(f"No latest message ID found for conversation {conv_id}, this may create a new thread")
        
        # Use consistent subject for replies
        threading_headers['subject'] = conv_info['subject']
        
        return threading_headers
    
    def _update_conversation_threading(self, message: CoordinationMessage, message_id: str, thread_id: str = None) -> None:
        """Update conversation threading state with new message"""
        conv_id = message.conversation_id
        
        if conv_id not in self.conversation_threading:
            # Initialize if somehow missing
            self.conversation_threading[conv_id] = {
                'message_ids': [],
                'subject': f"{self.AGENT_SUBJECT_PREFIX} Coordination",
                'participants': [self.agent_identity.user_email, message.to_agent_email],
                'thread_id': None,
                'latest_message_id': None
            }
        
        # Add this message to the conversation thread
        conv_info = self.conversation_threading[conv_id] 
        conv_info['message_ids'].append(message_id)
        
        # CRITICAL: Update latest_message_id to the ACTUAL Message-ID header for proper threading
        conv_info['latest_message_id'] = message_id
        logger.debug(f"Updated latest message ID for conversation {conv_id}: {message_id}")
        
        # Store thread_id when we get it (first message in conversation)
        if thread_id and not conv_info['thread_id']:
            conv_info['thread_id'] = thread_id
            logger.info(f"Thread ID {thread_id} assigned to conversation {conv_id}")
        
        # Ensure participants are tracked
        if message.to_agent_email not in conv_info['participants']:
            conv_info['participants'].append(message.to_agent_email)
        if self.agent_identity.user_email not in conv_info['participants']:
            conv_info['participants'].append(self.agent_identity.user_email)
        
        # Keep threading history manageable (limit to last 10 messages)
        if len(conv_info['message_ids']) > 10:
            conv_info['message_ids'] = conv_info['message_ids'][-10:]
        
        logger.debug(f"Updated conversation {conv_id}: {len(conv_info['message_ids'])} messages")
    
    def _extract_message_id_from_email(self, gmail_message: Dict[str, Any]) -> Optional[str]:
        """Extract Message-ID from received Gmail message for threading"""
        try:
            headers = gmail_message['payload'].get('headers', [])
            for header in headers:
                if header['name'].lower() == 'message-id':
                    return header['value']
        except Exception as e:
            logger.warning(f"Could not extract Message-ID from email: {e}")
        return None
    
    def _update_received_message_threading(self, conversation_id: str, message_id: str, from_email: str) -> None:
        """Update conversation threading state when receiving a message"""
        if conversation_id not in self.conversation_threading:
            # Initialize new conversation thread
            self.conversation_threading[conversation_id] = {
                'message_ids': [],
                'subject': f"{self.AGENT_SUBJECT_PREFIX} Coordination", 
                'participants': [self.agent_identity.user_email],
                'thread_id': None,
                'latest_message_id': None
            }
        
        conv_info = self.conversation_threading[conversation_id]
        
        # Add the received message ID to the conversation thread
        if message_id not in conv_info['message_ids']:
            conv_info['message_ids'].append(message_id)
            
        # CRITICAL: Update latest_message_id when receiving messages for proper reply threading
        conv_info['latest_message_id'] = message_id
        logger.debug(f"Updated latest received message ID for conversation {conversation_id}: {message_id}")
        
        # Add sender to participants if not already included
        if from_email and from_email not in conv_info['participants']:
            conv_info['participants'].append(from_email)
        
        # Keep threading history manageable
        if len(conv_info['message_ids']) > 10:
            conv_info['message_ids'] = conv_info['message_ids'][-10:]
        
        logger.debug(f"Updated conversation {conversation_id} with received message: {len(conv_info['message_ids'])} total")
    
    def get_conversation_thread_id(self, conversation_id: str) -> Optional[str]:
        """Get Gmail thread ID for a conversation"""
        conv_info = self.conversation_threading.get(conversation_id)
        return conv_info['thread_id'] if conv_info else None
    
    def archive_conversation_thread(self, conversation_id: str) -> bool:
        """Archive the Gmail thread for this conversation"""
        thread_id = self.get_conversation_thread_id(conversation_id)
        if not thread_id:
            logger.warning(f"No thread ID found for conversation {conversation_id}")
            return False
        
        try:
            return self.gmail.archive_thread(thread_id)
        except Exception as e:
            logger.error(f"Error archiving conversation thread {conversation_id}: {e}")
            return False
    
    def _load_processed_message_ids(self):
        """Load processed message IDs from persistent JSON storage"""
        import json
        import os
        from datetime import datetime, timedelta
        
        try:
            if os.path.exists(self.processed_messages_file):
                with open(self.processed_messages_file, 'r') as f:
                    data = json.load(f)
                
                processed_messages = data.get('processed_messages', {})
                
                # Load message IDs that aren't too old (within 30 days)
                cutoff_date = datetime.now() - timedelta(days=30)
                current_ids = set()
                
                for message_id, timestamp_str in processed_messages.items():
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if timestamp > cutoff_date:
                            current_ids.add(message_id)
                    except (ValueError, AttributeError):
                        # Skip entries with invalid timestamps
                        continue
                
                self.processed_message_ids = current_ids
                logger.info(f"Loaded {len(current_ids)} processed message IDs from storage")
                
                # Cleanup old entries if needed
                if len(current_ids) != len(processed_messages):
                    self._save_processed_message_ids()
                    logger.info(f"Cleaned up {len(processed_messages) - len(current_ids)} old message IDs")
            else:
                logger.info("No processed messages file found - starting with empty set")
                
        except Exception as e:
            logger.error(f"Error loading processed message IDs: {e}")
            # Fallback to empty set if loading fails
            self.processed_message_ids = set()
    
    def _save_processed_message_ids(self):
        """Save processed message IDs to persistent JSON storage"""
        import json
        from datetime import datetime
        
        try:
            # Create data structure with timestamps
            processed_messages = {}
            current_time = datetime.now().isoformat() + 'Z'
            
            for message_id in self.processed_message_ids:
                processed_messages[message_id] = current_time
            
            data = {
                'processed_messages': processed_messages,
                'last_updated': current_time,
                'last_cleanup': current_time
            }
            
            with open(self.processed_messages_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.processed_message_ids)} processed message IDs to storage")
            
        except Exception as e:
            logger.error(f"Error saving processed message IDs: {e}")

# ==================== INTELLIGENT COORDINATION PROTOCOL ====================

class IntegratedCoordinationProtocol:
    """Enhanced coordination protocol with email transport and intelligent scheduling"""
    
    def __init__(self, agent_identity: AgentIdentity, preferences: SchedulingPreferences,
                 credentials_file='credentials.json'):
        """Initialize integrated coordination protocol"""
        
        self.agent_identity = agent_identity
        self.preferences = preferences
        self.email_transport = EmailTransportLayer(agent_identity, credentials_file)
        self.calendar_manager = CalendarManager(credentials_file)
        
        # Coordination state
        self.active_conversations: Dict[str, List[CoordinationMessage]] = {}
        
        # Message tracking to prevent duplicate processing
        self.processed_messages_file = "processed_messages.json"
        self.processed_message_ids: set = set()
        self._load_processed_message_ids()
        self.current_context = ContextualFactors(
            current_workload=WorkloadLevel.MODERATE,
            energy_level=EnergyLevel.HIGH
        )
        
        # Intelligence weights for scoring
        self.intelligence_weights = {
            "workload_impact": 0.25,
            "energy_optimization": 0.25,
            "time_preference": 0.30,
            "conflict_avoidance": 0.20
        }
        
        logger.info(f"Integrated coordination protocol initialized for {agent_identity.agent_id}")
    
    def _parse_time_preference(self, time_preference: str) -> Tuple[datetime, datetime]:
        """Parse natural language time preference into date range.
        
        Args:
            time_preference: Natural language like 'next week', 'this week', 'tomorrow', etc.
            
        Returns:
            Tuple of (start_date, end_date) for the time range
        """
        if not time_preference:
            # Default: next 7 days from now
            now = datetime.now()
            return now, now + timedelta(days=7)
            
        now = datetime.now()
        time_pref_lower = time_preference.lower()
        
        if time_pref_lower == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif time_pref_lower == "tomorrow":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            end = start + timedelta(days=1)
        elif "this week" in time_pref_lower:
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
            end = start + timedelta(days=7)
        elif "next week" in time_pref_lower:
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday) + timedelta(days=7)
            end = start + timedelta(days=7)
        elif "this afternoon" in time_pref_lower:
            start = now.replace(hour=13, minute=0, second=0, microsecond=0)  # 1 PM
            end = now.replace(hour=17, minute=0, second=0, microsecond=0)    # 5 PM
        elif "tomorrow morning" in time_pref_lower:
            tomorrow = now + timedelta(days=1)
            start = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)   # 9 AM
            end = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)    # 12 PM
        elif "tomorrow afternoon" in time_pref_lower:
            tomorrow = now + timedelta(days=1)
            start = tomorrow.replace(hour=13, minute=0, second=0, microsecond=0)  # 1 PM
            end = tomorrow.replace(hour=17, minute=0, second=0, microsecond=0)    # 5 PM
        else:
            # Default to next 7 days
            start = now
            end = now + timedelta(days=7)
        
        return start, end
    
    def send_schedule_request(self, target_agent_email: str, meeting_context: MeetingContext,
                            time_preferences: List[str] = None) -> bool:
        """Send scheduling request to target agent"""
        
        payload = {
            'meeting_context': self._serialize_meeting_context(meeting_context),
            'time_preferences': time_preferences or ["morning", "afternoon"],
            'sender_preferences': self._serialize_preferences(self.preferences),
            'context_factors': self._serialize_context(self.current_context),
            'requested_options': 3
        }
        
        message = CoordinationMessage(
            message_id="",
            message_type=MessageType.SCHEDULE_REQUEST,
            from_agent=self.agent_identity,
            to_agent_email=target_agent_email,
            timestamp=datetime.now(),
            conversation_id="",
            payload=payload
        )
        
        success = self.email_transport.send_coordination_message(message)
        
        if success:
            # Store in active conversations
            conv_id = message.conversation_id
            if conv_id not in self.active_conversations:
                self.active_conversations[conv_id] = []
            self.active_conversations[conv_id].append(message)
        
        return success
    
    def process_incoming_coordination_messages(self) -> List[Dict[str, Any]]:
        """Process incoming coordination messages and generate responses"""
        
        incoming_messages = self.email_transport.check_for_coordination_messages()
        processing_results = []
        
        for message in incoming_messages:
            try:
                # Add to conversation history
                conv_id = message.conversation_id
                if conv_id not in self.active_conversations:
                    self.active_conversations[conv_id] = []
                self.active_conversations[conv_id].append(message)
                
                # Process based on message type
                response = self._process_coordination_message(message)
                
                result = {
                    'message_id': message.message_id,
                    'from_agent': message.from_agent.agent_id,
                    'message_type': message.message_type.value,
                    'processed': True,
                    'response_sent': False
                }
                
                if response:
                    response_sent = self.email_transport.send_coordination_message(response)
                    result['response_sent'] = response_sent
                    
                    if response_sent:
                        self.active_conversations[conv_id].append(response)
                
                processing_results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing coordination message: {e}")
                processing_results.append({
                    'message_id': message.message_id,
                    'processed': False,
                    'error': str(e)
                })
        
        # Save processed message IDs to persistent storage after batch processing
        if len(processing_results) > 0:
            self._save_processed_message_ids()
        
        return processing_results
    
    def _process_coordination_message(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Process individual coordination message and generate response"""
        
        if message.message_type == MessageType.SCHEDULE_REQUEST:
            return self._handle_schedule_request(message)
        elif message.message_type == MessageType.SCHEDULE_PROPOSAL:
            return self._handle_schedule_proposal(message)
        elif message.message_type == MessageType.SCHEDULE_COUNTER_PROPOSAL:
            return self._handle_schedule_counter_proposal(message)
        elif message.message_type == MessageType.SCHEDULE_CONFIRMATION:
            return self._handle_schedule_confirmation(message)
        elif message.message_type == MessageType.SCHEDULE_REJECTION:
            return self._handle_schedule_rejection(message)
        
        return None
    
    def _handle_schedule_request(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Handle incoming schedule request - Step 2: Agent B replies with ALL available times"""
        
        logger.info(f"Processing schedule request from {message.from_agent.agent_id}")
        
        try:
            # Parse meeting context with proper enum handling
            context_data = message.payload["meeting_context"].copy()
            
            # Filter context_data to only include valid MeetingContext fields
            valid_fields = {'meeting_type', 'duration_minutes', 'attendees', 'subject', 'description', 'energy_requirement', 'requires_preparation'}
            filtered_context = {k: v for k, v in context_data.items() if k in valid_fields}
            
            # Set defaults for required fields if missing
            if 'attendees' not in filtered_context:
                filtered_context['attendees'] = [message.from_agent.user_email, self.agent_identity.user_email]
            
            logger.info(f"Creating MeetingContext with fields: {list(filtered_context.keys())}")
            meeting_context = MeetingContext(**filtered_context)
            time_preferences = message.payload.get("time_preferences", ["morning", "afternoon"])
            
            # Find ALL available times that match criteria (Step 2 of 3-step protocol)
            proposed_times = self._find_all_available_times(meeting_context, message.payload)
            
            if proposed_times:
                payload = {
                    'original_request_id': message.message_id,
                    'proposed_times': [self._serialize_timeslot(slot) for slot in proposed_times],
                    'proposal_confidence': max(slot.confidence_score for slot in proposed_times),
                    'sender_constraints': self._get_current_constraints(),
                    'context_analysis': self._analyze_scheduling_context(meeting_context)
                }
                
                return CoordinationMessage(
                    message_id="",
                    message_type=MessageType.SCHEDULE_PROPOSAL,
                    from_agent=self.agent_identity,
                    to_agent_email=message.from_agent.user_email,
                    timestamp=datetime.now(),
                    conversation_id=message.conversation_id,
                    payload=payload
                )
            else:
                # Send rejection with detailed reason and alternatives
                meeting_duration = meeting_context.duration_minutes
                date_range = f"{meeting_context.preferred_start_date} to {meeting_context.preferred_end_date}"
                time_prefs = ", ".join(time_preferences) if time_preferences else "any time"
                
                detailed_reason = (f"Unable to find any available {meeting_duration}-minute slots "
                                 f"between {date_range} during preferred times ({time_prefs}). "
                                 f"My calendar appears fully booked during those periods.")
                
                # Use the standardized rejection message creation with validation
                return self._create_rejection_message(message, detailed_reason)
                
        except Exception as e:
            logger.error(f"Error handling schedule request: {e}")
            return None
    
    def _handle_schedule_proposal(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Handle incoming schedule proposal with 3-step protocol
        
        Step 2: Agent B replies with ALL available times that match
        Step 3: Agent A evaluates:
          - One mutual time → Schedule + confirmation email
          - Multiple mutual times → Propose one (may trigger counter-proposals)
          - No mutual times → "No mutual window found" email
        """
        
        logger.info(f"Processing schedule proposal from {message.from_agent.agent_id}")
        
        try:
            # Validate payload structure first
            if not message.payload or "proposed_times" not in message.payload:
                logger.error("Schedule proposal missing proposed_times in payload")
                return self._create_rejection_message(message, "Invalid proposal format - missing time options")
            
            proposed_times_data = message.payload["proposed_times"]
            if not isinstance(proposed_times_data, list) or len(proposed_times_data) == 0:
                logger.error("Schedule proposal has invalid or empty proposed_times")
                return self._create_rejection_message(message, "Invalid proposal format - no time options provided")
            
            # Deserialize time slots with individual error handling
            proposed_times = []
            for i, slot_data in enumerate(proposed_times_data):
                try:
                    if slot_data is None:
                        logger.warning(f"Skipping null time slot at index {i}")
                        continue
                    
                    timeslot = self._deserialize_timeslot(slot_data)
                    if timeslot:  # Only add valid timeslots
                        proposed_times.append(timeslot)
                        logger.debug(f"Successfully parsed time slot {i}: {timeslot.start_time} - {timeslot.end_time}")
                    else:
                        logger.warning(f"Failed to deserialize time slot at index {i}: {slot_data}")
                        
                except Exception as e:
                    logger.error(f"Error deserializing time slot {i} from {slot_data}: {e}")
                    # Continue with other slots instead of failing completely
                    continue
            
            if not proposed_times:
                logger.error("No valid time slots could be parsed from proposal")
                return self._create_rejection_message(message, "Unable to parse any valid time options from your proposal")
            
            # Get original request context for finding ALL our available times
            conversation = self.active_conversations.get(message.conversation_id, [])
            original_request = self._find_original_request_in_conversation(conversation)
            
            if not original_request:
                logger.warning("No original request found - handling as reverse-initiated proposal")
                return self._handle_reverse_proposal(message, proposed_times)
            
            meeting_context = MeetingContext(**original_request.payload["meeting_context"])
            
            # Find ALL our available times that match criteria
            our_available_times = self._find_all_available_times(meeting_context, original_request.payload)
            
            # Find mutual times (intersection of their proposal and our availability)
            mutual_times = self._find_mutual_availability(proposed_times, our_available_times)
            
            if len(mutual_times) == 0:
                # No mutual times → "No mutual window found" email
                logger.info("No mutual availability found")
                return self._create_no_mutual_time_message(message, proposed_times, our_available_times)
            
            elif len(mutual_times) == 1:
                # One mutual time → Schedule + confirmation email  
                logger.info("Found exactly one mutual time - scheduling directly")
                best_time = mutual_times[0]
                payload = {
                    'proposal_message_id': message.message_id,
                    'selected_time': self._serialize_timeslot(best_time),
                    'confidence_score': best_time.confidence_score,
                    'calendar_event_details': self._prepare_calendar_event_details(message, best_time),
                    'mutual_times_found': 1
                }
                
                return CoordinationMessage(
                    message_id="",
                    message_type=MessageType.SCHEDULE_CONFIRMATION,
                    from_agent=self.agent_identity,
                    to_agent_email=message.from_agent.user_email,
                    timestamp=datetime.now(),
                    conversation_id=message.conversation_id,
                    payload=payload,
                    requires_response=False
                )
            
            else:
                # Multiple mutual times → Propose the best one (may trigger counter-proposals)
                logger.info(f"Found {len(mutual_times)} mutual times - proposing best option")
                best_time = max(mutual_times, key=lambda t: t.confidence_score)
                
                payload = {
                    'proposal_message_id': message.message_id,
                    'selected_time': self._serialize_timeslot(best_time),
                    'confidence_score': best_time.confidence_score,
                    'calendar_event_details': self._prepare_calendar_event_details(message, best_time),
                    'mutual_times_found': len(mutual_times),
                    'alternative_times': [self._serialize_timeslot(t) for t in mutual_times[1:3]]  # Include 2 alternatives
                }
                
                return CoordinationMessage(
                    message_id="",
                    message_type=MessageType.SCHEDULE_CONFIRMATION,
                    from_agent=self.agent_identity,
                    to_agent_email=message.from_agent.user_email,
                    timestamp=datetime.now(),
                    conversation_id=message.conversation_id,
                    payload=payload,
                    requires_response=False
                )
                
        except Exception as e:
            logger.error(f"Error handling schedule proposal: {e}")
            error_detail = str(e) if str(e).strip() else "Unknown system error occurred"
            return self._create_rejection_message(message, f"Unable to process meeting proposal due to technical issue: {error_detail}")
            
        return None
    
    def _handle_schedule_confirmation(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Handle schedule confirmation and create calendar event with attendee invites"""
        
        logger.info(f"Processing schedule confirmation from {message.from_agent.agent_id}")
        
        try:
            # Validate message payload
            if not message.payload or "selected_time" not in message.payload:
                logger.error("Schedule confirmation missing selected_time in payload")
                return None
            
            selected_time_data = message.payload["selected_time"]
            if not selected_time_data:
                logger.error("Schedule confirmation has null selected_time")
                return None
            
            try:
                confirmed_time = self._deserialize_timeslot(selected_time_data)
                if not confirmed_time:
                    logger.error("Failed to deserialize confirmed time from selected_time data")
                    return None
            except Exception as e:
                logger.error(f"Error deserializing confirmed time: {e}")
                return None
            logger.info(f"Confirmed meeting time: {confirmed_time.start_time} - {confirmed_time.end_time}")
            
            # Prepare proper event details with both agents as attendees
            event_details = self._prepare_calendar_event_details(message, confirmed_time)
            logger.info(f"Event details prepared with {len(event_details.get('attendees', []))} attendees")
            
            # Create calendar event with proper attendee list
            event_created = self._create_confirmed_calendar_event(confirmed_time, event_details)
            
            if event_created:
                logger.info(f"✅ Calendar event created successfully for {confirmed_time.start_time}")
                logger.info(f"📧 Invites sent to: {event_details.get('attendees', [])}")
                
                # Archive the coordination email thread now that meeting is confirmed
                try:
                    archived = self.email_transport.archive_conversation_thread(message.conversation_id)
                    if archived:
                        logger.info(f"📁 Coordination thread archived for conversation {message.conversation_id}")
                    else:
                        logger.warning(f"⚠️ Could not archive coordination thread for conversation {message.conversation_id}")
                except Exception as archive_error:
                    logger.warning(f"⚠️ Archive failed but continuing: {archive_error}")
                
                # Send acknowledgment
                payload = {
                    'confirmation_id': message.message_id,
                    'calendar_event_created': True,
                    'event_time': self._serialize_timeslot(confirmed_time),
                    'coordination_complete': True,
                    'attendees_invited': event_details.get('attendees', [])
                }
                
                return CoordinationMessage(
                    message_id="",
                    message_type=MessageType.COORDINATION_ACK,
                    from_agent=self.agent_identity,
                    to_agent_email=message.from_agent.user_email,
                    timestamp=datetime.now(),
                    conversation_id=message.conversation_id,
                    payload=payload,
                    requires_response=False
                )
            else:
                logger.warning("⚠️ Calendar event creation failed, but coordination continues")
                
                # Send acknowledgment even if calendar creation failed
                payload = {
                    'confirmation_id': message.message_id,
                    'calendar_event_created': False,
                    'event_time': self._serialize_timeslot(confirmed_time),
                    'coordination_complete': True,
                    'error': 'Calendar event creation failed'
                }
                
                return CoordinationMessage(
                    message_id="",
                    message_type=MessageType.COORDINATION_ACK,
                    from_agent=self.agent_identity,
                    to_agent_email=message.from_agent.user_email,
                    timestamp=datetime.now(),
                    conversation_id=message.conversation_id,
                    payload=payload,
                    requires_response=False
                )
            
        except KeyError as e:
            logger.error(f"Missing required data in schedule confirmation: {e}")
            return None
        except Exception as e:
            logger.error(f"Error handling schedule confirmation: {e}")
            return None
    
    def _handle_schedule_counter_proposal(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Handle incoming schedule counter-proposal"""
        
        logger.info(f"Processing schedule counter-proposal from {message.from_agent.agent_id}")
        
        try:
            # Validate payload structure first
            if not message.payload or "counter_proposals" not in message.payload:
                logger.error("Schedule counter-proposal missing counter_proposals in payload")
                return self._create_rejection_message(message, "Invalid counter-proposal format - missing time options")
            
            counter_proposals_data = message.payload["counter_proposals"]
            if not isinstance(counter_proposals_data, list) or len(counter_proposals_data) == 0:
                logger.error("Schedule counter-proposal has invalid or empty counter_proposals")
                return self._create_rejection_message(message, "Invalid counter-proposal format - no time options provided")
            
            # Deserialize counter-proposals with individual error handling
            counter_proposals = []
            for i, slot_data in enumerate(counter_proposals_data):
                try:
                    if slot_data is None:
                        logger.warning(f"Skipping null counter-proposal slot at index {i}")
                        continue
                    
                    timeslot = self._deserialize_timeslot(slot_data)
                    if timeslot:  # Only add valid timeslots
                        counter_proposals.append(timeslot)
                        logger.debug(f"Successfully parsed counter-proposal slot {i}: {timeslot.start_time} - {timeslot.end_time}")
                    else:
                        logger.warning(f"Failed to deserialize counter-proposal slot at index {i}: {slot_data}")
                        
                except Exception as e:
                    logger.error(f"Error deserializing counter-proposal slot {i} from {slot_data}: {e}")
                    # Continue with other slots instead of failing completely
                    continue
            
            if not counter_proposals:
                logger.error("No valid counter-proposal time slots could be parsed")
                return self._create_rejection_message(message, "Unable to parse any valid time options from your counter-proposal")
            
            # Evaluate counter-proposals with contextual intelligence
            best_option = self._evaluate_proposals_intelligently(counter_proposals)
            
            # Get conversation history to check for negotiation rounds
            conversation = self.active_conversations.get(message.conversation_id, [])
            negotiation_rounds = len([msg for msg in conversation 
                                    if msg.message_type in [MessageType.SCHEDULE_PROPOSAL, 
                                                          MessageType.SCHEDULE_COUNTER_PROPOSAL]])
            
            # Remove hardcoded negotiation limit - let natural termination handle it
            # The system will naturally terminate when no more alternatives can be found
            
            # Normal counter-proposal evaluation
            if best_option and best_option.confidence_score > 0.6:  # Lower threshold for counter-proposals
                # Accept the counter-proposal
                payload = {
                    'proposal_message_id': message.message_id,
                    'selected_time': self._serialize_timeslot(best_option),
                    'confidence_score': best_option.confidence_score,
                    'calendar_event_details': self._prepare_calendar_event_details(message, best_option)
                }
                
                return CoordinationMessage(
                    message_id="",
                    message_type=MessageType.SCHEDULE_CONFIRMATION,
                    from_agent=self.agent_identity,
                    to_agent_email=message.from_agent.user_email,
                    timestamp=datetime.now(),
                    conversation_id=message.conversation_id,
                    payload=payload,
                    requires_response=False
                )
            else:
                # Generate new counter-proposals based on our calendar
                original_request = self._find_original_request_in_conversation(conversation)
                if original_request:
                    meeting_context = MeetingContext(**original_request.payload["meeting_context"])
                    new_proposals = self._find_intelligent_available_times(meeting_context, original_request.payload)
                    
                    if new_proposals:
                        payload = {
                            'original_counter_proposal_id': message.message_id,
                            'counter_proposals': [self._serialize_timeslot(slot) for slot in new_proposals],
                            'reasoning': 'Suggesting new alternatives based on updated availability',
                            'negotiation_round': negotiation_rounds + 1
                        }
                        
                        return CoordinationMessage(
                            message_id="",
                            message_type=MessageType.SCHEDULE_COUNTER_PROPOSAL,
                            from_agent=self.agent_identity,
                            to_agent_email=message.from_agent.user_email,
                            timestamp=datetime.now(),
                            conversation_id=message.conversation_id,
                                    payload=payload
                        )
                
                # If we can't find alternatives, reject
                return self._create_rejection_message(message, "After analyzing all proposed times and our calendar constraints, we cannot find any mutually available slots that work for both schedules")
                
        except Exception as e:
            logger.error(f"Error handling schedule counter-proposal: {e}")
            error_detail = str(e) if str(e).strip() else "Unknown system error occurred"
            return self._create_rejection_message(message, f"Unable to process counter-proposal due to technical issue: {error_detail}")
    
    def _handle_schedule_rejection(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Handle incoming schedule rejection"""
        
        logger.info(f"Processing schedule rejection from {message.from_agent.agent_id}")
        
        try:
            rejection_reason = message.payload.get("rejection_reason")
            if not rejection_reason or rejection_reason.strip() == "":
                logger.error("Received rejection message without proper reason - this should not happen")
                # This should not occur if the other agent is using the proper rejection creation methods
                rejection_reason = "Technical error: Rejection received without proper reason (possible bug in coordination protocol)"
            
            # Additional validation to ensure meaningful rejection reasons
            if rejection_reason.strip().lower() in ["no reason provided", "none", "n/a", "unknown"]:
                logger.error(f"Received meaningless rejection reason: {rejection_reason}")
                rejection_reason = f"Invalid rejection reason received: '{rejection_reason}' - this indicates a protocol violation"
            
            logger.info(f"Meeting rejected: {rejection_reason}")
            
            # Send acknowledgment that rejection was received
            payload = {
                'rejection_id': message.message_id,
                'rejection_acknowledged': True,
                'coordination_complete': False,
                'reason': rejection_reason
            }
            
            return CoordinationMessage(
                message_id="",
                message_type=MessageType.COORDINATION_ACK,
                from_agent=self.agent_identity,
                to_agent_email=message.from_agent.user_email,
                timestamp=datetime.now(),
                conversation_id=message.conversation_id,
                payload=payload,
                requires_response=False
            )
            
        except Exception as e:
            logger.error(f"Error handling schedule rejection: {e}")
            return None
    
    def _find_intelligent_available_times(self, meeting_context: MeetingContext, 
                                        request_payload: Dict[str, Any]) -> List[TimeSlot]:
        """Find available times with intelligent scheduling"""
        
        try:
            # Parse time preferences for dynamic date range
            now = datetime.now()
            time_preferences = request_payload.get("time_preferences", ["morning", "afternoon"])
            
            # Check if time_preferences contains natural language time expressions
            search_start = now
            search_end = now + timedelta(days=7)  # Default: 7 days
            
            if time_preferences and isinstance(time_preferences, list) and time_preferences:
                # Check if first preference is a natural language expression
                first_pref = time_preferences[0]
                if any(expr in first_pref.lower() for expr in ['next week', 'this week', 'tomorrow', 'today', 'afternoon', 'morning']):
                    # This is a natural language time preference
                    search_start, search_end = self._parse_time_preference(first_pref)
                    # Remove the natural language preference, keep only time-of-day preferences
                    time_preferences = [pref for pref in time_preferences[1:] if pref in ['morning', 'afternoon', 'evening']] or ['morning', 'afternoon']
            
            # Use try-catch for calendar API to handle errors gracefully
            existing_events = []
            try:
                existing_events = self.calendar_manager.get_events(
                    time_min=search_start,
                    time_max=search_end,
                    max_results=50
                )
            except Exception as calendar_error:
                logger.warning(f"Calendar API error (using empty events list): {calendar_error}")
                existing_events = []
            
            # Generate intelligent time slots within the parsed date range
            slots = []
            current_date = search_start.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = search_end.replace(hour=0, minute=0, second=0, microsecond=0)
            
            while current_date < end_date:
                # Skip weekends unless explicitly requested
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                
                # Only generate slots for dates that are today or in the future
                if current_date.date() >= now.date():
                    # Generate slots based on preferences and context
                    daily_slots = self._generate_intelligent_daily_slots(
                        current_date, meeting_context, time_preferences, existing_events
                    )
                    slots.extend(daily_slots)
                
                current_date += timedelta(days=1)
            
            # Score and rank slots
            scored_slots = []
            for slot in slots:
                score = self._calculate_contextual_score(slot, meeting_context)
                slot.confidence_score = score
                scored_slots.append(slot)
            
            # Return top 3 slots for backwards compatibility
            scored_slots.sort(key=lambda x: x.confidence_score, reverse=True)
            return scored_slots[:3]
            
        except Exception as e:
            logger.error(f"Error finding intelligent available times: {e}")
            return []
    
    def _find_all_available_times(self, meeting_context: MeetingContext, 
                                request_payload: Dict[str, Any]) -> List[TimeSlot]:
        """Find ALL available times that match criteria for 3-step protocol"""
        
        try:
            # Parse time preferences for dynamic date range
            now = datetime.now()
            time_preferences = request_payload.get("time_preferences", ["morning", "afternoon"])
            
            # Check if time_preferences contains natural language time expressions
            search_start = now
            search_end = now + timedelta(days=7)  # Default: 7 days
            
            if time_preferences and isinstance(time_preferences, list) and time_preferences:
                # Check if first preference is a natural language expression
                first_pref = time_preferences[0]
                if any(expr in first_pref.lower() for expr in ['next week', 'this week', 'tomorrow', 'today', 'afternoon', 'morning']):
                    # This is a natural language time preference
                    search_start, search_end = self._parse_time_preference(first_pref)
                    # Remove the natural language preference, keep only time-of-day preferences
                    time_preferences = [pref for pref in time_preferences[1:] if pref in ['morning', 'afternoon', 'evening']] or ['morning', 'afternoon']
            
            # Use try-catch for calendar API to handle errors gracefully
            existing_events = []
            try:
                existing_events = self.calendar_manager.get_events(
                    time_min=search_start,
                    time_max=search_end,
                    max_results=50
                )
            except Exception as calendar_error:
                logger.warning(f"Calendar API error (using empty events list): {calendar_error}")
                existing_events = []
            
            # Generate ALL time slots that match criteria within the parsed date range
            slots = []
            current_date = search_start.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = search_end.replace(hour=0, minute=0, second=0, microsecond=0)
            
            while current_date < end_date:
                # Skip weekends unless explicitly requested
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                
                # Only generate slots for dates that are today or in the future
                if current_date.date() >= now.date():
                    # Generate slots based on preferences and context
                    daily_slots = self._generate_intelligent_daily_slots(
                        current_date, meeting_context, time_preferences, existing_events
                    )
                    slots.extend(daily_slots)
                
                current_date += timedelta(days=1)
            
            # Score and rank ALL slots
            scored_slots = []
            for slot in slots:
                score = self._calculate_contextual_score(slot, meeting_context)
                slot.confidence_score = score
                scored_slots.append(slot)
            
            # Return ALL available slots, sorted by score
            scored_slots.sort(key=lambda x: x.confidence_score, reverse=True)
            return scored_slots
            
        except Exception as e:
            logger.error(f"Error finding all available times: {e}")
            return []
    
    def _generate_intelligent_daily_slots(self, target_date: datetime, meeting_context: MeetingContext,
                                        time_preferences: List[str], existing_events: List[Dict[str, Any]]) -> List[TimeSlot]:
        """Generate intelligent time slots for a specific day"""
        
        slots = []
        
        # Generate comprehensive time slots based on preferences with 30-minute intervals
        time_ranges = []
        if "morning" in time_preferences:
            # Morning: 8 AM to 12 PM (8:00, 8:30, 9:00, 9:30, 10:00, 10:30, 11:00, 11:30)
            time_ranges.extend([(8, 0), (8, 30), (9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30)])
        if "afternoon" in time_preferences:
            # Afternoon: 1 PM to 6 PM (13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30)
            time_ranges.extend([(13, 0), (13, 30), (14, 0), (14, 30), (15, 0), (15, 30), (16, 0), (16, 30), (17, 0), (17, 30)])
        if "evening" in time_preferences:
            # Evening: 6 PM to 8 PM (18:00, 18:30, 19:00, 19:30)
            time_ranges.extend([(18, 0), (18, 30), (19, 0), (19, 30)])
        
        # If no specific preferences, use all time ranges (business hours)
        if not time_ranges:
            time_ranges.extend([
                # Full business day coverage
                (9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30),
                (13, 0), (13, 30), (14, 0), (14, 30), (15, 0), (15, 30), (16, 0), (16, 30)
            ])
        
        for hour, minute in time_ranges:
            start_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Ensure timezone consistency - use the agent's configured timezone
            if start_time.tzinfo is None:
                # Get timezone from preferences or default to Eastern
                tz_str = getattr(self.preferences, 'timezone', 'America/New_York')
                tz = pytz.timezone(tz_str)
                start_time = tz.localize(start_time)
            
            end_time = start_time + timedelta(minutes=meeting_context.duration_minutes)
            
            # Check for conflicts
            conflicts = self._check_for_conflicts(start_time, end_time, existing_events)
            
            if not conflicts:  # No conflicts found
                slot = TimeSlot(
                    start_time=start_time,
                    end_time=end_time,
                    confidence_score=0.0,  # Will be calculated later
                    conflicts=[],
                    context_score={}
                )
                slots.append(slot)
        
        return slots
    
    def _check_for_conflicts(self, start_time: datetime, end_time: datetime, 
                           existing_events: List[Dict[str, Any]]) -> List[str]:
        """Check for scheduling conflicts"""
        
        conflicts = []
        
        for event in existing_events:
            try:
                from dateutil import parser
                
                event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                event_end_str = event['end'].get('dateTime', event['end'].get('date'))
                
                event_start = parser.parse(event_start_str)
                event_end = parser.parse(event_end_str)
                
                # Check for overlap
                if (start_time < event_end and end_time > event_start):
                    conflicts.append(event.get('summary', 'Existing Event'))
                    
            except Exception as e:
                logger.warning(f"Error checking conflict for event: {e}")
                continue
        
        return conflicts
    
    def _calculate_contextual_score(self, slot: TimeSlot, meeting_context: MeetingContext) -> float:
        """Calculate contextual score for a time slot"""
        
        scores = {
            "workload_impact": self._score_workload_impact(slot, meeting_context),
            "energy_optimization": self._score_energy_optimization(slot, meeting_context),
            "time_preference": self._score_time_preference(slot),
            "conflict_avoidance": 1.0 if not slot.conflicts else 0.5
        }
        
        # Calculate weighted composite score
        composite_score = sum(
            scores[factor] * self.intelligence_weights[factor]
            for factor in scores
        )
        
        return min(1.0, max(0.0, composite_score))
    
    def _score_workload_impact(self, slot: TimeSlot, meeting_context: MeetingContext) -> float:
        """Score based on current workload impact"""
        base_score = 0.7
        
        if self.current_context.current_workload == WorkloadLevel.LIGHT:
            base_score = 0.9
        elif self.current_context.current_workload == WorkloadLevel.HEAVY:
            base_score = 0.5
            if meeting_context.duration_minutes <= 30:
                base_score += 0.2  # Prefer shorter meetings when busy
        
        return base_score
    
    def _score_energy_optimization(self, slot: TimeSlot, meeting_context: MeetingContext) -> float:
        """Score based on energy level optimization"""
        hour = slot.start_time.hour
        base_score = 0.7
        
        # Match meeting energy requirements with time of day
        if meeting_context.energy_requirement == "high":
            if 9 <= hour <= 11:  # Morning high energy
                base_score = 0.9
            elif 14 <= hour <= 16:  # Afternoon peak
                base_score = 0.8
        
        # Adjust for current energy level
        if self.current_context.energy_level == EnergyLevel.HIGH:
            if meeting_context.energy_requirement == "high":
                base_score += 0.1
        elif self.current_context.energy_level == EnergyLevel.LOW:
            if meeting_context.energy_requirement == "high":
                base_score -= 0.3
        
        return base_score
    
    def _score_time_preference(self, slot: TimeSlot) -> float:
        """Score based on general time preferences"""
        hour = slot.start_time.hour
        
        # General preference for mid-morning and mid-afternoon
        if 10 <= hour <= 11 or 14 <= hour <= 15:
            return 0.9
        elif 9 <= hour <= 12 or 13 <= hour <= 17:
            return 0.8
        else:
            return 0.5
    
    def _evaluate_proposals_intelligently(self, proposed_times: List[TimeSlot]) -> Optional[TimeSlot]:
        """Evaluate proposed meeting times with intelligent scoring"""
        if not proposed_times:
            return None
        
        # Score each proposal
        for slot in proposed_times:
            slot.confidence_score = self._calculate_contextual_score(slot, MeetingContext(
                meeting_type="proposed_meeting",
                duration_minutes=60,
                attendees=[],
                subject="Evaluation"
            ))
        
        # Return highest scoring slot
        return max(proposed_times, key=lambda slot: slot.confidence_score)
    
    def _serialize_timeslot(self, slot: TimeSlot) -> Dict[str, Any]:
        """Serialize TimeSlot for message transmission"""
        return {
            "start_time": slot.start_time.isoformat(),
            "end_time": slot.end_time.isoformat(),
            "confidence_score": slot.confidence_score,
            "conflicts": slot.conflicts,
            "context_score": slot.context_score
        }
    
    def _parse_time_string(self, time_str: Union[str, datetime]) -> datetime:
        """Parse time string from either ISO format or human-readable format with timezone handling"""
        if isinstance(time_str, datetime):
            # If already a datetime, ensure it has timezone info
            if time_str.tzinfo is None:
                # Default to agent's timezone
                tz_str = getattr(self.preferences, 'timezone', 'America/New_York')
                tz = pytz.timezone(tz_str)
                time_str = tz.localize(time_str)
            return time_str
        
        if isinstance(time_str, str):
            # Try ISO format first
            try:
                parsed_time = datetime.fromisoformat(time_str)
                # Ensure timezone info is preserved/added
                if parsed_time.tzinfo is None:
                    tz_str = getattr(self.preferences, 'timezone', 'America/New_York')
                    tz = pytz.timezone(tz_str)
                    parsed_time = tz.localize(parsed_time)
                return parsed_time
            except ValueError:
                pass
            
            # Try human-readable formats with dateutil if available
            try:
                parsed_time = dateutil.parser.parse(time_str)
                # Ensure timezone info
                if parsed_time.tzinfo is None:
                    tz_str = getattr(self.preferences, 'timezone', 'America/New_York')
                    tz = pytz.timezone(tz_str)
                    parsed_time = tz.localize(parsed_time)
                return parsed_time
            except (NameError, Exception) as e:
                # dateutil not available or parsing failed
                logger.error(f"Unable to parse time string '{time_str}': {e}")
                # Fallback to a reasonable default (tomorrow at 10 AM with timezone)
                fallback = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
                tz_str = getattr(self.preferences, 'timezone', 'America/New_York')
                tz = pytz.timezone(tz_str)
                return tz.localize(fallback)
        
        logger.error(f"Invalid time format: {time_str}")
        fallback = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        tz_str = getattr(self.preferences, 'timezone', 'America/New_York')
        tz = pytz.timezone(tz_str)
        return tz.localize(fallback)

    def _deserialize_timeslot(self, slot_data: Dict[str, Any]) -> TimeSlot:
        """Deserialize TimeSlot from message data with comprehensive error handling"""
        try:
            # Ensure required fields are present
            if not slot_data or "start_time" not in slot_data or "end_time" not in slot_data:
                logger.error(f"Missing required time fields in slot_data: {slot_data}")
                raise ValueError("TimeSlot data must contain start_time and end_time")
            
            # Parse times with error handling
            try:
                start_time = self._parse_time_string(slot_data["start_time"])
                end_time = self._parse_time_string(slot_data["end_time"])
            except Exception as e:
                logger.error(f"Failed to parse times from slot_data {slot_data}: {e}")
                # Provide a reasonable fallback
                start_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
                end_time = start_time + timedelta(hours=1)
            
            # Ensure all optional fields have defaults
            confidence_score = slot_data.get("confidence_score", 0.8)
            conflicts = slot_data.get("conflicts", [])
            context_score = slot_data.get("context_score", {})
            
            # Validate types and ranges
            if not isinstance(confidence_score, (int, float)):
                logger.warning(f"Invalid confidence_score type: {type(confidence_score)}, using default")
                confidence_score = 0.8
            elif not (0.0 <= confidence_score <= 1.0):
                logger.warning(f"Confidence score {confidence_score} out of range, clamping to [0,1]")
                confidence_score = max(0.0, min(1.0, confidence_score))
            
            if not isinstance(conflicts, list):
                logger.warning(f"Invalid conflicts type: {type(conflicts)}, using empty list")
                conflicts = []
            
            if not isinstance(context_score, dict):
                logger.warning(f"Invalid context_score type: {type(context_score)}, using empty dict")
                context_score = {}
            
            return TimeSlot(
                start_time=start_time,
                end_time=end_time,
                confidence_score=float(confidence_score),
                conflicts=conflicts,
                context_score=context_score
            )
            
        except Exception as e:
            logger.error(f"Critical error deserializing TimeSlot from {slot_data}: {e}")
            # Return a fallback TimeSlot to prevent crashes
            fallback_start = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
            return TimeSlot(
                start_time=fallback_start,
                end_time=fallback_start + timedelta(hours=1),
                confidence_score=0.1,  # Low confidence for fallback
                conflicts=["Parse error - using fallback time"],
                context_score={"fallback": True}
            )
    
    def _get_current_constraints(self) -> Dict[str, Any]:
        """Get current scheduling constraints"""
        return {
            "max_meetings_today": self.preferences.max_meetings_per_day,
            "focus_time_blocks": ["09:00-11:00", "14:00-16:00"],
            "current_workload": self.current_context.current_workload.value,
            "energy_level": self.current_context.energy_level.value
        }
    
    def _analyze_scheduling_context(self, meeting_context: MeetingContext) -> Dict[str, Any]:
        """Analyze scheduling context for intelligent decision making"""
        return {
            "meeting_complexity": "high" if meeting_context.requires_preparation else "medium",
            "optimal_energy_match": meeting_context.energy_requirement,
            "duration_category": "short" if meeting_context.duration_minutes <= 30 else "standard"
        }
    
    def _suggest_alternatives(self, meeting_context: MeetingContext) -> List[str]:
        """Suggest alternatives when no suitable times found"""
        return [
            "Consider extending search timeframe to next week",
            f"Reduce meeting duration from {meeting_context.duration_minutes} to 30 minutes",
            "Consider splitting into multiple shorter sessions",
            "Schedule during evening hours if urgent"
        ]
    
    def _generate_counter_proposals(self, original_proposals: List[TimeSlot]) -> List[TimeSlot]:
        """Generate counter-proposals based on original proposals"""
        counter_proposals = []
        
        for slot in original_proposals:
            # Suggest alternative times around the original proposals
            alt_start = slot.start_time + timedelta(hours=1)
            alt_end = alt_start + (slot.end_time - slot.start_time)
            
            counter_slot = TimeSlot(
                start_time=alt_start,
                end_time=alt_end,
                confidence_score=0.8,
                conflicts=[],
                context_score={"alternative_proposal": 1.0}
            )
            counter_proposals.append(counter_slot)
        
        return counter_proposals[:2]  # Limit to 2 counter-proposals
    
    def _prepare_calendar_event_details(self, proposal_message: CoordinationMessage, 
                                      selected_time: TimeSlot) -> Dict[str, Any]:
        """Prepare calendar event details"""
        
        # Extract meeting context from original request
        conversation = self.active_conversations.get(proposal_message.conversation_id, [])
        meeting_context = None
        
        for msg in conversation:
            if msg.message_type == MessageType.SCHEDULE_REQUEST:
                meeting_context = MeetingContext(**msg.payload.get("meeting_context", {}))
                break
        
        if not meeting_context:
            meeting_context = MeetingContext(
                meeting_type="coordination_meeting",
                duration_minutes=30,
                attendees=[],
                subject="Agent Coordinated Meeting"
            )
        
        # Ensure both agents are included as attendees
        attendees = list(meeting_context.attendees) if meeting_context.attendees else []
        
        # Add the agent who sent the proposal (other agent) if not already included
        other_agent_email = proposal_message.from_agent.user_email
        if other_agent_email not in attendees:
            attendees.append(other_agent_email)
        
        # Add this agent (the one receiving the confirmation) if not already included
        this_agent_email = self.agent_identity.user_email
        if this_agent_email not in attendees:
            attendees.append(this_agent_email)
        
        # Generate enhanced title and description
        enhanced_title = self._generate_enhanced_title(meeting_context, attendees, conversation)
        enhanced_description = self._generate_enhanced_description(meeting_context, attendees, conversation, selected_time)
        
        return {
            "summary": enhanced_title,
            "description": enhanced_description,
            "start_time": selected_time.start_time.isoformat(),
            "end_time": selected_time.end_time.isoformat(),
            "attendees": attendees,
            "coordinated_by_agents": True,
            "coordination_confidence": selected_time.confidence_score
        }
    
    def _generate_enhanced_title(self, meeting_context: MeetingContext, 
                               attendees: List[str], conversation: List[CoordinationMessage]) -> str:
        """Generate intelligent title with participants and meeting type"""
        
        base_title = meeting_context.subject or "Agent Coordinated Meeting"
        
        # Extract participant names (remove domain from email)
        participant_names = []
        for email in attendees:
            if email != self.agent_identity.user_email:  # Exclude self
                name = email.split('@')[0].replace('.', ' ').title()
                participant_names.append(name)
        
        # Format meeting type for display
        meeting_type_display = meeting_context.meeting_type.replace('_', ' ').title()
        
        # Build enhanced title: [Subject] | [Participants] | [Type]
        title_parts = [base_title]
        
        if participant_names:
            if len(participant_names) == 1:
                title_parts.append(participant_names[0])
            elif len(participant_names) == 2:
                title_parts.append(f"{participant_names[0]} & {participant_names[1]}")
            else:
                title_parts.append(f"{participant_names[0]} + {len(participant_names)-1} others")
        
        if meeting_type_display and meeting_type_display != "Coordination Meeting":
            title_parts.append(meeting_type_display)
        
        return " | ".join(title_parts)
    
    def _generate_enhanced_description(self, meeting_context: MeetingContext, 
                                     attendees: List[str], conversation: List[CoordinationMessage],
                                     selected_time: TimeSlot) -> str:
        """Generate rich context description for calendar event"""
        
        description_parts = []
        
        # Meeting Details Section
        description_parts.append("📋 MEETING DETAILS")
        
        if meeting_context.description:
            description_parts.append(f"• Purpose: {meeting_context.description}")
        
        meeting_type_display = meeting_context.meeting_type.replace('_', ' ').title()
        description_parts.append(f"• Type: {meeting_type_display}")
        
        if hasattr(meeting_context, 'requires_preparation') and meeting_context.requires_preparation:
            description_parts.append("• Preparation Required: Yes")
        
        description_parts.append("")  # Empty line
        
        # Participants Section
        description_parts.append("👥 PARTICIPANTS")
        for email in attendees:
            if email == self.agent_identity.user_email:
                name = self.agent_identity.user_name
                description_parts.append(f"• {name} ({email})")
            else:
                name = email.split('@')[0].replace('.', ' ').title()
                description_parts.append(f"• {name} ({email})")
        
        description_parts.append("")  # Empty line
        
        # Coordination Summary Section
        description_parts.append("📅 COORDINATION SUMMARY")
        description_parts.append("• Scheduled via: Agent coordination")
        
        # Count alternative times considered
        alternatives_count = self._count_alternatives_from_conversation(conversation)
        if alternatives_count > 1:
            description_parts.append(f"• Alternative times considered: {alternatives_count} options")
        
        description_parts.append("")  # Empty line
        
        # Relevant Links & Resources Section
        description_parts.append("📎 RELEVANT LINKS & RESOURCES")
        all_links = self._extract_all_links(conversation)
        
        if all_links:
            for link in all_links:
                description_parts.append(f"• Link: {link}")
        else:
            description_parts.append("• No links referenced in coordination")
        
        # Project context detection
        project_context = self._detect_project_context(conversation)
        if project_context:
            description_parts.append(f"• Project context: {project_context}")
        
        description_parts.append("")  # Empty line
        
        # Next Steps Section
        description_parts.append("🎯 NEXT STEPS")
        agenda_items = self._extract_agenda_items(conversation)
        
        if agenda_items:
            for item in agenda_items:
                description_parts.append(f"• {item}")
        else:
            description_parts.append("• Meeting agenda to be confirmed")
        
        preparation_items = self._suggest_preparation_items(meeting_context)
        if preparation_items:
            description_parts.append("• Pre-meeting preparation:")
            for prep in preparation_items:
                description_parts.append(f"  - {prep}")
        
        description_parts.append("")  # Empty line
        description_parts.append("---")
        description_parts.append("🤖 Coordinated by Claude Code agents")
        
        return "\n".join(description_parts)
    
    def _count_alternatives_from_conversation(self, conversation: List[CoordinationMessage]) -> int:
        """Count how many alternative times were considered during coordination"""
        alternatives = 0
        
        for msg in conversation:
            if msg.message_type == MessageType.SCHEDULE_PROPOSAL:
                if 'proposed_times' in msg.payload:
                    alternatives += len(msg.payload['proposed_times'])
            elif msg.message_type == MessageType.SCHEDULE_COUNTER_PROPOSAL:
                if 'counter_proposals' in msg.payload:
                    alternatives += len(msg.payload['counter_proposals'])
        
        return max(alternatives, 1)  # At least 1 option was considered
    
    def _extract_all_links(self, conversation: List[CoordinationMessage]) -> List[str]:
        """Extract all HTTP/HTTPS links from coordination messages and email content"""
        links = []
        import re
        
        # Comprehensive URL pattern to catch all HTTP/HTTPS links
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?)]'
        
        for msg in conversation:
            # Search message payload for links
            self._extract_links_from_data_structure(msg.payload, url_pattern, links)
            
            # Also search email content that was used to create the message
            # This covers subjects, human-readable descriptions, and any other text content
            
            # Check if there's a meeting context with subject/description
            if hasattr(msg, 'payload') and 'meeting_context' in msg.payload:
                context = msg.payload['meeting_context']
                if isinstance(context, dict):
                    # Search meeting subject and description
                    for field in ['subject', 'description']:
                        if field in context and isinstance(context[field], str):
                            found_links = re.findall(url_pattern, context[field])
                            links.extend(found_links)
            
            # Search any string fields in the message payload root level
            for key, value in msg.payload.items():
                if isinstance(value, str):
                    found_links = re.findall(url_pattern, value)
                    links.extend(found_links)
        
        # Remove duplicates and return ALL links (no artificial limit)
        unique_links = list(set(links))
        # Clean up any malformed URLs that might have trailing punctuation
        cleaned_links = []
        for link in unique_links:
            # Remove common trailing punctuation that might get caught
            link = link.rstrip('.,;:!?)')
            if link and len(link) > 10:  # Basic sanity check
                cleaned_links.append(link)
        
        return cleaned_links
    
    def _extract_links_from_data_structure(self, data, url_pattern, links):
        """Recursively extract links from nested data structures"""
        import re
        
        if isinstance(data, str):
            found_links = re.findall(url_pattern, data)
            links.extend(found_links)
        elif isinstance(data, dict):
            for key, value in data.items():
                self._extract_links_from_data_structure(value, url_pattern, links)
        elif isinstance(data, list):
            for item in data:
                self._extract_links_from_data_structure(item, url_pattern, links)
    
    def _detect_project_context(self, conversation: List[CoordinationMessage]) -> str:
        """Detect project keywords and context from coordination messages"""
        
        # Common project-related keywords to look for
        project_keywords = [
            'project', 'initiative', 'campaign', 'program', 'roadmap',
            'sprint', 'milestone', 'deliverable', 'launch', 'release',
            'planning', 'strategy', 'review', 'retrospective', 'standup'
        ]
        
        context_words = []
        
        for msg in conversation:
            # Check subject and description
            if hasattr(msg, 'payload') and 'meeting_context' in msg.payload:
                context = msg.payload['meeting_context']
                
                subject = context.get('subject', '').lower()
                description = context.get('description', '').lower()
                
                for keyword in project_keywords:
                    if keyword in subject or keyword in description:
                        # Extract surrounding context
                        if keyword in subject:
                            context_words.append(subject.split(keyword)[0].strip().split()[-2:] + 
                                               [keyword] + 
                                               subject.split(keyword)[1].strip().split()[:2])
                        break
        
        if context_words and context_words[0]:
            # Clean and return the most relevant context
            context_phrase = ' '.join([word for word in context_words[0] if word])
            return context_phrase.title()[:50]  # Limit length
        
        return ""
    
    def _extract_agenda_items(self, conversation: List[CoordinationMessage]) -> List[str]:
        """Extract potential agenda items from coordination messages"""
        agenda_items = []
        
        # Look for agenda-related keywords and patterns
        agenda_patterns = [
            r'agenda[:\s]+([^\n]+)',
            r'discuss[:\s]+([^\n]+)', 
            r'review[:\s]+([^\n]+)',
            r'plan[:\s]+([^\n]+)',
            r'topics?[:\s]+([^\n]+)'
        ]
        
        import re
        
        for msg in conversation:
            if hasattr(msg, 'payload') and 'meeting_context' in msg.payload:
                context = msg.payload['meeting_context']
                description = context.get('description', '')
                
                for pattern in agenda_patterns:
                    matches = re.findall(pattern, description, re.IGNORECASE)
                    for match in matches:
                        if match.strip():
                            agenda_items.append(match.strip())
        
        return agenda_items[:3]  # Limit to 3 agenda items
    
    def _suggest_preparation_items(self, meeting_context: MeetingContext) -> List[str]:
        """Suggest preparation items based on meeting type and context"""
        preparations = []
        
        meeting_type = meeting_context.meeting_type.lower()
        
        # Type-based preparation suggestions
        if 'planning' in meeting_type or 'strategy' in meeting_type:
            preparations.extend([
                "Review previous planning documents",
                "Prepare status updates on current initiatives"
            ])
        elif 'review' in meeting_type or 'retrospective' in meeting_type:
            preparations.extend([
                "Gather performance metrics and outcomes",
                "Prepare feedback and improvement suggestions"
            ])
        elif '1:1' in meeting_type or 'one_on_one' in meeting_type:
            preparations.extend([
                "Prepare personal updates and questions",
                "Review previous conversation notes"
            ])
        elif 'standup' in meeting_type or 'sync' in meeting_type:
            preparations.extend([
                "Prepare brief status update",
                "Note any blockers or help needed"
            ])
        elif 'client' in meeting_type or 'external' in meeting_type:
            preparations.extend([
                "Review client background and history",
                "Prepare relevant materials and presentations"
            ])
        
        
        return preparations[:3]  # Limit to 3 preparation items
    
    def _create_confirmed_calendar_event(self, confirmed_time: TimeSlot, 
                                       event_details: Dict[str, Any]) -> bool:
        """Create calendar event for confirmed meeting"""
        try:
            # Check for duplicate events in the same time slot to prevent double-booking
            existing_events = []
            try:
                # Check for existing events at the same time
                existing_events = self.calendar_manager.get_events(
                    time_min=confirmed_time.start_time - timedelta(minutes=5),
                    time_max=confirmed_time.end_time + timedelta(minutes=5),
                    max_results=10
                )
            except Exception as calendar_error:
                logger.warning(f"Could not check for existing events: {calendar_error}")
            
            # Look for potential duplicates
            event_title = event_details.get("summary", "Agent Coordinated Meeting")
            for existing_event in existing_events:
                if existing_event.get('summary', '').strip() == event_title.strip():
                    logger.info(f"Event '{event_title}' already exists at {confirmed_time.start_time}")
                    return True  # Consider this a success since the event exists
            
            # Create the calendar event with all attendees
            event_created = self.calendar_manager.create_event(
                title=event_title,
                start_time=confirmed_time.start_time,
                end_time=confirmed_time.end_time,
                description=event_details.get("description", ""),
                attendees=event_details.get("attendees", [])
            )
            
            if event_created:
                logger.info(f"Calendar event created successfully: {event_title}")
                logger.info(f"Attendees invited: {event_details.get('attendees', [])}")
                return True
            else:
                logger.warning("Calendar event creation returned None")
                return False
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            # Don't fail the entire coordination if calendar creation fails
            logger.info("Continuing coordination despite calendar error")
            return False
    
    def _serialize_meeting_context(self, meeting_context: MeetingContext) -> Dict[str, Any]:
        """Serialize MeetingContext for JSON transmission"""
        return asdict(meeting_context)
    
    def _serialize_preferences(self, preferences: SchedulingPreferences) -> Dict[str, Any]:
        """Serialize SchedulingPreferences for JSON transmission"""
        return asdict(preferences)
    
    def _serialize_context(self, context: ContextualFactors) -> Dict[str, Any]:
        """Serialize ContextualFactors with enum handling"""
        context_dict = asdict(context)
        
        # Convert enums to string values
        if isinstance(context_dict.get('current_workload'), WorkloadLevel):
            context_dict['current_workload'] = context_dict['current_workload'].value
        elif hasattr(context_dict.get('current_workload'), 'value'):
            context_dict['current_workload'] = context_dict['current_workload'].value
            
        if isinstance(context_dict.get('energy_level'), EnergyLevel):
            context_dict['energy_level'] = context_dict['energy_level'].value
        elif hasattr(context_dict.get('energy_level'), 'value'):
            context_dict['energy_level'] = context_dict['energy_level'].value
        
        return context_dict
    
    def _find_original_request_in_conversation(self, conversation: List[CoordinationMessage]) -> Optional[CoordinationMessage]:
        """Find the original schedule request in the conversation"""
        for message in conversation:
            if message.message_type == MessageType.SCHEDULE_REQUEST:
                return message
        return None
    
    def _handle_reverse_proposal(self, message: CoordinationMessage, proposed_times: List[TimeSlot]) -> Optional[CoordinationMessage]:
        """Handle proposals received without original requests (reverse-initiated coordination)
        
        When another agent sends a proposal without first sending a request, we need to:
        1. Extract meeting context from whatever information is available
        2. Create a reasonable meeting context for scheduling
        3. Find mutual availability and respond appropriately
        """
        logger.info(f"Handling reverse proposal from {message.from_agent.agent_id} with {len(proposed_times)} time slots")
        
        try:
            # Extract meeting context from available information
            meeting_context = self._extract_meeting_context_from_proposal(message, proposed_times)
            
            # Create a synthetic request payload for time finding
            request_payload = {
                'time_preferences': ['morning', 'afternoon'],
                'meeting_context': {
                    'subject': meeting_context.subject,
                    'duration_minutes': meeting_context.duration_minutes,
                    'attendees': meeting_context.attendees,
                    'description': meeting_context.description,
                    'meeting_type': meeting_context.meeting_type
                }
            }
            
            # Find our available times using the synthetic context
            our_available_times = self._find_all_available_times(meeting_context, request_payload)
            
            # Find mutual times between their proposal and our availability
            mutual_times = self._find_mutual_availability(proposed_times, our_available_times)
            
            if len(mutual_times) == 0:
                # No mutual times available
                logger.info("No mutual availability found for reverse proposal")
                return self._create_no_mutual_time_message(message, proposed_times, our_available_times)
            
            elif len(mutual_times) == 1:
                # Exactly one mutual time - schedule it directly
                logger.info("Found exactly one mutual time for reverse proposal - scheduling directly")
                best_time = mutual_times[0]
                
                # Create calendar event
                event_created = self._create_calendar_event(best_time, meeting_context)
                if event_created:
                    return self._create_confirmation_message(message, best_time, meeting_context)
                else:
                    return self._create_rejection_message(message, "Failed to create calendar event for the selected time")
            
            else:
                # Multiple mutual times - propose the best one
                logger.info(f"Found {len(mutual_times)} mutual times for reverse proposal - proposing best option")
                best_time = mutual_times[0]  # Take the highest scored time
                
                return self._create_counter_proposal_message(message, [best_time], meeting_context)
                
        except Exception as e:
            logger.error(f"Error handling reverse proposal: {e}")
            return self._create_rejection_message(message, "Unable to process your meeting proposal - please try again with more specific details")
    
    def _extract_meeting_context_from_proposal(self, message: CoordinationMessage, proposed_times: List[TimeSlot]) -> MeetingContext:
        """Extract meeting context from proposal message when no original request exists"""
        
        # Extract basic info from message
        attendees = [self.agent_identity.user_email, message.from_agent.user_email]
        
        # Infer duration from proposed time slots if available
        duration_minutes = 30  # Default
        if proposed_times:
            # Calculate duration from first time slot
            first_slot = proposed_times[0]
            duration_delta = first_slot.end_time - first_slot.start_time
            duration_minutes = int(duration_delta.total_seconds() / 60)
        
        # Try to extract subject from email subject or conversation
        subject = "Coordination Meeting"  # Default
        
        # Check if there's any context in the message payload
        if message.payload and 'context_analysis' in message.payload:
            context = message.payload['context_analysis']
            if isinstance(context, dict) and 'meeting_purpose' in context:
                subject = context['meeting_purpose']
        
        # Check conversation threading for subject hints
        conversation = self.active_conversations.get(message.conversation_id, [])
        if conversation:
            for msg in conversation:
                # Look for subject hints in any previous messages
                if hasattr(msg, 'payload') and msg.payload and 'meeting_context' in msg.payload:
                    ctx = msg.payload['meeting_context']
                    if isinstance(ctx, dict) and 'subject' in ctx:
                        subject = ctx['subject']
                        break
        
        return MeetingContext(
            meeting_type="coordination_meeting",
            duration_minutes=duration_minutes,
            attendees=attendees,
            subject=subject,
            description=f"Meeting coordinated between {message.from_agent.user_name} and {self.agent_identity.user_name}"
        )
    
    def _load_processed_message_ids(self):
        """Load processed message IDs from persistent JSON storage"""
        import json
        import os
        from datetime import datetime, timedelta
        
        try:
            if os.path.exists(self.processed_messages_file):
                with open(self.processed_messages_file, 'r') as f:
                    data = json.load(f)
                
                processed_messages = data.get('processed_messages', {})
                
                # Load message IDs that aren't too old (within 30 days)
                cutoff_date = datetime.now() - timedelta(days=30)
                current_ids = set()
                
                for message_id, timestamp_str in processed_messages.items():
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if timestamp > cutoff_date:
                            current_ids.add(message_id)
                    except (ValueError, AttributeError):
                        # Skip entries with invalid timestamps
                        continue
                
                self.processed_message_ids = current_ids
                logger.info(f"Loaded {len(current_ids)} processed message IDs from storage")
                
                # Cleanup old entries if needed
                if len(current_ids) != len(processed_messages):
                    self._save_processed_message_ids()
                    logger.info(f"Cleaned up {len(processed_messages) - len(current_ids)} old message IDs")
            else:
                logger.info("No processed messages file found - starting with empty set")
                
        except Exception as e:
            logger.error(f"Error loading processed message IDs: {e}")
            # Fallback to empty set if loading fails
            self.processed_message_ids = set()
    
    def _save_processed_message_ids(self):
        """Save processed message IDs to persistent JSON storage"""
        import json
        from datetime import datetime
        
        try:
            # Create data structure with timestamps
            processed_messages = {}
            current_time = datetime.now().isoformat() + 'Z'
            
            for message_id in self.processed_message_ids:
                processed_messages[message_id] = current_time
            
            data = {
                'processed_messages': processed_messages,
                'last_updated': current_time,
                'last_cleanup': current_time
            }
            
            with open(self.processed_messages_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.processed_message_ids)} processed message IDs to storage")
            
        except Exception as e:
            logger.error(f"Error saving processed message IDs: {e}")
    
    def _cleanup_old_processed_ids(self, days_to_keep=30):
        """Remove processed message IDs older than specified days"""
        import json
        import os
        from datetime import datetime, timedelta
        
        try:
            if not os.path.exists(self.processed_messages_file):
                return
            
            with open(self.processed_messages_file, 'r') as f:
                data = json.load(f)
            
            processed_messages = data.get('processed_messages', {})
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Filter out old entries
            updated_messages = {}
            for message_id, timestamp_str in processed_messages.items():
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if timestamp > cutoff_date:
                        updated_messages[message_id] = timestamp_str
                except (ValueError, AttributeError):
                    # Skip entries with invalid timestamps
                    continue
            
            # Update in-memory set
            self.processed_message_ids = set(updated_messages.keys())
            
            # Save cleaned data
            data['processed_messages'] = updated_messages
            data['last_cleanup'] = datetime.now().isoformat() + 'Z'
            
            with open(self.processed_messages_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            removed_count = len(processed_messages) - len(updated_messages)
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old processed message IDs")
                
        except Exception as e:
            logger.error(f"Error cleaning up old processed message IDs: {e}")
    
    def _find_mutual_availability(self, proposed_times: List[TimeSlot], 
                                our_available_times: List[TimeSlot]) -> List[TimeSlot]:
        """Find mutual availability between proposed times and our availability"""
        logger.info(f"🔍 DEBUGGING MUTUAL AVAILABILITY DETECTION")
        logger.info(f"📋 Comparing {len(proposed_times)} proposed times with {len(our_available_times)} available times")
        
        # Log all proposed times with detailed info
        logger.info(f"🎯 PROPOSED TIMES:")
        for i, slot in enumerate(proposed_times):
            logger.info(f"  Proposed {i+1}: {slot.start_time} to {slot.end_time}")
            logger.info(f"    - Raw start: {slot.start_time} (tz: {slot.start_time.tzinfo})")
            logger.info(f"    - Raw end: {slot.end_time} (tz: {slot.end_time.tzinfo})")
            logger.info(f"    - Formatted: {slot.start_time.strftime('%A, %B %d at %I:%M %p')}")
            logger.info(f"    - ISO format: {slot.start_time.isoformat()}")
        
        # Log all our available times with detailed info
        logger.info(f"✅ OUR AVAILABLE TIMES:")
        for i, slot in enumerate(our_available_times):
            logger.info(f"  Available {i+1}: {slot.start_time} to {slot.end_time}")
            logger.info(f"    - Raw start: {slot.start_time} (tz: {slot.start_time.tzinfo})")
            logger.info(f"    - Raw end: {slot.end_time} (tz: {slot.end_time.tzinfo})")
            logger.info(f"    - Formatted: {slot.start_time.strftime('%A, %B %d at %I:%M %p')}")
            logger.info(f"    - ISO format: {slot.start_time.isoformat()}")
        
        mutual_times = []
        
        for p_idx, proposed_slot in enumerate(proposed_times):
            logger.info(f"🔍 Checking proposed slot {p_idx+1}: {proposed_slot.start_time.strftime('%A, %B %d at %I:%M %p')}")
            
            for a_idx, our_slot in enumerate(our_available_times):
                logger.info(f"  ⚖️ Comparing with available slot {a_idx+1}: {our_slot.start_time.strftime('%A, %B %d at %I:%M %p')}")
                
                # Check if times overlap significantly (allowing for small differences)
                proposed_start = proposed_slot.start_time
                proposed_end = proposed_slot.end_time
                our_start = our_slot.start_time
                our_end = our_slot.end_time
                
                # Log the exact datetime objects being compared
                logger.info(f"    📅 Proposed: {proposed_start} to {proposed_end}")
                logger.info(f"    📅 Available: {our_start} to {our_end}")
                
                # Normalize timezones for comparison if they differ
                if proposed_start.tzinfo != our_start.tzinfo:
                    logger.info(f"    ⚠️ Timezone mismatch: {proposed_start.tzinfo} vs {our_start.tzinfo}")
                    # Convert both to UTC for comparison
                    proposed_start_utc = proposed_start.astimezone(pytz.UTC)
                    proposed_end_utc = proposed_end.astimezone(pytz.UTC)
                    our_start_utc = our_start.astimezone(pytz.UTC)
                    our_end_utc = our_end.astimezone(pytz.UTC)
                    logger.info(f"    🌍 UTC Proposed: {proposed_start_utc} to {proposed_end_utc}")
                    logger.info(f"    🌍 UTC Available: {our_start_utc} to {our_end_utc}")
                    
                    # Use UTC times for comparison
                    proposed_start = proposed_start_utc
                    proposed_end = proposed_end_utc
                    our_start = our_start_utc
                    our_end = our_end_utc
                
                # Allow 15-minute tolerance for small time differences
                tolerance = timedelta(minutes=15)
                logger.info(f"    ⏰ Using tolerance: {tolerance}")
                
                # Check if there's significant overlap
                overlap_start = max(proposed_start, our_start)
                overlap_end = min(proposed_end, our_end)
                
                logger.info(f"    🔄 Overlap calculation:")
                logger.info(f"      - Overlap start: max({proposed_start}, {our_start}) = {overlap_start}")
                logger.info(f"      - Overlap end: min({proposed_end}, {our_end}) = {overlap_end}")
                
                if overlap_end > overlap_start:
                    # There's overlap - check if it's substantial enough
                    overlap_duration = overlap_end - overlap_start
                    required_duration = proposed_end - proposed_start
                    
                    logger.info(f"    ✅ Overlap detected!")
                    logger.info(f"      - Overlap duration: {overlap_duration}")
                    logger.info(f"      - Required duration: {required_duration}")
                    logger.info(f"      - Minimum needed: {required_duration - tolerance}")
                    
                    if overlap_duration >= required_duration - tolerance:
                        logger.info(f"    🎉 MATCH FOUND! Overlap is sufficient")
                        # Use the original times (not UTC converted) for the result
                        mutual_slot = TimeSlot(
                            start_time=proposed_slot.start_time,  # Use original proposed time
                            end_time=proposed_slot.end_time,      # Use original proposed time
                            confidence_score=our_slot.confidence_score,
                            conflicts=our_slot.conflicts,
                            context_score=our_slot.context_score
                        )
                        mutual_times.append(mutual_slot)
                        logger.info(f"    📝 Added mutual slot: {mutual_slot.start_time} to {mutual_slot.end_time}")
                        break  # Found a match for this proposed time
                    else:
                        logger.info(f"    ❌ Insufficient overlap: {overlap_duration} < {required_duration - tolerance}")
                else:
                    logger.info(f"    ❌ No overlap: overlap_end ({overlap_end}) <= overlap_start ({overlap_start})")
        
        logger.info(f"🔍 Initial mutual times found: {len(mutual_times)}")
        
        # Remove duplicates and sort by confidence score
        seen_times = set()
        unique_mutual_times = []
        
        for slot in mutual_times:
            time_key = (slot.start_time, slot.end_time)
            if time_key not in seen_times:
                seen_times.add(time_key)
                unique_mutual_times.append(slot)
            else:
                logger.info(f"    🔄 Removing duplicate: {slot.start_time} to {slot.end_time}")
        
        unique_mutual_times.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logger.info(f"📊 FINAL RESULT: {len(unique_mutual_times)} unique mutual times found")
        for i, slot in enumerate(unique_mutual_times):
            logger.info(f"  Final {i+1}: {slot.start_time.strftime('%A, %B %d at %I:%M %p')} (confidence: {slot.confidence_score})")
        
        return unique_mutual_times
    
    def _create_no_mutual_time_message(self, original_message: CoordinationMessage, 
                                     proposed_times: List[TimeSlot], 
                                     our_available_times: List[TimeSlot]) -> CoordinationMessage:
        """Create a 'no mutual window found' message with alternatives"""
        
        # Provide summary of what was attempted
        proposed_summary = []
        for i, slot in enumerate(proposed_times[:3], 1):
            time_str = slot.start_time.strftime('%A, %B %d at %I:%M %p')
            proposed_summary.append(f"Option {i}: {time_str}")
        
        our_summary = []
        for i, slot in enumerate(our_available_times[:3], 1):
            time_str = slot.start_time.strftime('%A, %B %d at %I:%M %p')
            our_summary.append(f"Available {i}: {time_str}")
        
        # Create a detailed rejection reason with context
        detailed_reason = (f"No mutual availability found after comparing all proposed times. "
                          f"Their proposals: {', '.join(proposed_summary[:2])}{'...' if len(proposed_summary) > 2 else ''}. "
                          f"My availability: {', '.join(our_summary[:2])}{'...' if len(our_summary) > 2 else ''}. "
                          "Consider extending the timeframe or adjusting preferences.")
        
        # Use the standardized rejection message creation with validation
        rejection_message = self._create_rejection_message(original_message, detailed_reason)
        
        # Add additional context to the payload
        rejection_message.payload.update({
            'coordination_status': 'no_mutual_availability',
            'their_proposed_times': proposed_summary,
            'our_available_times': our_summary
        })
        
        return rejection_message
    
    def _create_rejection_message(self, original_message: CoordinationMessage, reason: str) -> CoordinationMessage:
        """Create a rejection message with mandatory meaningful reason"""
        # Validate that reason is meaningful
        if not reason or reason.strip() == "" or reason.strip().lower() in ["no reason provided", "none", "n/a"]:
            raise ValueError("Rejection reason must be provided and meaningful. Cannot reject meeting without a proper explanation.")
        
        # Ensure reason is descriptive enough
        if len(reason.strip()) < 10:
            raise ValueError(f"Rejection reason too brief: '{reason}'. Please provide a more detailed explanation (at least 10 characters).")
        
        payload = {
            'original_message_id': original_message.message_id,
            'rejection_reason': reason.strip(),
            'alternative_suggestions': [
                "Consider extending the meeting timeframe",
                "Try scheduling for next week",
                "Consider a shorter meeting duration"
            ]
        }
        
        return CoordinationMessage(
            message_id="",
            message_type=MessageType.SCHEDULE_REJECTION,
            from_agent=self.agent_identity,
            to_agent_email=original_message.from_agent.user_email,
            timestamp=datetime.now(),
            conversation_id=original_message.conversation_id,
            payload=payload,
            requires_response=False
        )

# ==================== MAIN INTEGRATION FUNCTIONS ====================

# Global coordination system instance
_integrated_coordinator = None

def initialize_integrated_coordination_system(agent_config: Dict[str, Any] = None):
    """Initialize integrated coordination system with configurable agent identity"""
    global _integrated_coordinator
    if _integrated_coordinator is None:
        # Use provided config or auto-detect from Gmail
        if agent_config is None:
            # Auto-detect user email from Gmail authentication
            user_email = None
            try:
                from gmail_functions import GmailManager
                gmail = GmailManager()
                profile = gmail.service.users().getProfile(userId='me').execute()
                user_email = profile["emailAddress"]
                logger.info(f"Auto-detected Gmail account: {user_email}")
            except Exception as e:
                logger.error(f"Gmail authentication required for coordination system: {e}")
                raise ValueError("Gmail authentication failed. Please ensure valid credentials.json and token.json are available.")
            
            # Validate the detected email
            if not user_email or '@' not in user_email:
                raise ValueError("Invalid Gmail account detected. Please check authentication.")
            
            # Generate agent identity from detected email
            email_prefix = user_email.split('@')[0]
            agent_config = {
                "agent_id": f"{email_prefix}_claude_agent",
                "user_name": email_prefix.replace('.', ' ').title(),
                "user_email": user_email
            }
        
        # Validate agent config
        if not agent_config.get("user_email") or "example.com" in agent_config.get("user_email", ""):
            raise ValueError("Invalid agent configuration: valid user_email required, no example.com addresses allowed")
        
        # Create agent identity from config
        agent_identity = AgentIdentity(
            agent_id=agent_config.get("agent_id", "claude_agent_v2"),
            user_name=agent_config.get("user_name", "Claude Agent User"),
            user_email=agent_config["user_email"],
            capabilities=[
                "calendar_access", 
                "scheduling_coordination", 
                "multi_agent_communication",
                "email_coordination",
                "context_awareness",
                "intelligent_scheduling"
            ]
        )
        
        # Use provided preferences or defaults
        pref_config = agent_config.get("preferences", {})
        preferences = SchedulingPreferences(
            preferred_meeting_times=pref_config.get("preferred_meeting_times", ["morning", "afternoon"]),
            max_meetings_per_day=pref_config.get("max_meetings_per_day", 5),
            min_meeting_gap_minutes=pref_config.get("min_meeting_gap_minutes", 15),
            focus_time_protection=pref_config.get("focus_time_protection", True),
            negotiation_style=pref_config.get("negotiation_style", "collaborative"),
            response_time_preference=pref_config.get("response_time_preference", "immediate")
        )
        
        _integrated_coordinator = IntegratedCoordinationProtocol(agent_identity, preferences)
    
    return _integrated_coordinator

def coordinate_intelligent_meeting(target_agent_email: str, meeting_subject: str, 
                                 duration_minutes: int = 30, meeting_type: str = "1:1", 
                                 attendees: List[str] = None, time_preference: str = None) -> bool:
    """Send intelligent coordination request to target agent"""
    
    coordinator = initialize_integrated_coordination_system()
    
    # Use provided attendees or default to sender and target
    if attendees is None:
        attendees = [coordinator.agent_identity.user_email, target_agent_email]
    
    meeting_context = MeetingContext(
        meeting_type=meeting_type,
        duration_minutes=duration_minutes,
        attendees=attendees,
        subject=meeting_subject,
        description=f"Intelligently coordinated {meeting_type} meeting"
    )
    
    # Parse time preference if provided
    parsed_time_prefs = None
    if time_preference:
        parsed_time_prefs = [time_preference]  # Convert to list for compatibility
    
    return coordinator.send_schedule_request(target_agent_email, meeting_context, parsed_time_prefs)

def process_agent_coordination_messages() -> List[Dict[str, Any]]:
    """Process incoming coordination messages with intelligent responses"""
    coordinator = initialize_integrated_coordination_system()
    return coordinator.process_incoming_coordination_messages()

def get_coordination_system_status() -> Dict[str, Any]:
    """Get integrated coordination system status"""
    coordinator = initialize_integrated_coordination_system()
    return {
        'agent_id': coordinator.agent_identity.agent_id,
        'email': coordinator.agent_identity.user_email,
        'protocol_version': coordinator.email_transport.PROTOCOL_VERSION,
        'active_conversations': len(coordinator.active_conversations),
        'current_workload': coordinator.current_context.current_workload.value,
        'energy_level': coordinator.current_context.energy_level.value,
        'status': 'active',
        'capabilities': coordinator.agent_identity.capabilities
    }

def update_coordination_context(workload: str = None, energy: str = None, 
                              meetings_today: int = None) -> Dict[str, Any]:
    """Update coordination context for better scheduling decisions"""
    coordinator = initialize_integrated_coordination_system()
    
    updates = {}
    if workload:
        coordinator.current_context.current_workload = WorkloadLevel(workload)
        updates['workload'] = workload
    if energy:
        coordinator.current_context.energy_level = EnergyLevel(energy)
        updates['energy'] = energy
    if meetings_today is not None:
        coordinator.current_context.meetings_today = meetings_today
        updates['meetings_today'] = meetings_today
    
    return {
        'context_updated': True,
        'updates': updates,
        'current_context': {
            'workload': coordinator.current_context.current_workload.value,
            'energy': coordinator.current_context.energy_level.value,
            'meetings_today': coordinator.current_context.meetings_today
        }
    }

# ==================== TESTING FUNCTIONS ====================

def test_integrated_coordination():
    """Test the complete integrated coordination system"""
    print("🧪 Testing Integrated Agent Coordination System")
    print("=" * 55)
    
    try:
        # Initialize system
        coordinator = initialize_integrated_coordination_system()
        print(f"✅ System initialized: {coordinator.agent_identity.agent_id}")
        
        # Test sending coordination request
        success = coordinate_intelligent_meeting(
            target_agent_email="test@example.com",
            meeting_subject="Test Intelligent Coordination", 
            duration_minutes=30
        )
        print(f"✅ Coordination request sent: {success}")
        
        # Test processing messages
        results = process_agent_coordination_messages()
        print(f"✅ Message processing: {len(results)} messages processed")
        
        # Test context update
        context_result = update_coordination_context(workload="heavy", energy="high")
        print(f"✅ Context updated: {context_result['context_updated']}")
        
        # Get system status
        status = get_coordination_system_status()
        print(f"✅ System status: {status['status']}")
        print(f"   Active conversations: {status['active_conversations']}")
        print(f"   Current workload: {status['current_workload']}")
        
        print("\n🎯 Integrated coordination system is ready!")
        print("Features: Email transport, intelligent scheduling, context awareness")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_integrated_coordination()