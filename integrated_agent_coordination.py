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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

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

class Priority(Enum):
    """Message priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

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
    urgency: Priority
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
    priority: Priority
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
    """Handles email-based agent communication transport"""
    
    def __init__(self, agent_identity: AgentIdentity, credentials_file='credentials.json'):
        """Initialize email transport layer"""
        self.agent_identity = agent_identity
        self.gmail = GmailManager(credentials_file)
        
        # Email protocol constants
        self.AGENT_SUBJECT_PREFIX = "[CLAUDE-COORD]"
        self.PROTOCOL_VERSION = "agent_coord_v2"
        self.MESSAGE_SEPARATOR = "=== AGENT COORDINATION ==="
        
        logger.info(f"Email transport initialized for {agent_identity.agent_id}")
    
    def send_coordination_message(self, message: CoordinationMessage) -> bool:
        """Send coordination message via email"""
        try:
            # Create email subject
            subject = f"{self.AGENT_SUBJECT_PREFIX} {message.message_type.value.replace('_', ' ').title()}"
            
            # Create structured email body
            email_body = self._create_coordination_email_body(message)
            
            # Send via Gmail
            result = self.gmail.send_email(
                to_email=message.to_agent_email,
                subject=subject,
                body=email_body
            )
            
            if result:
                logger.info(f"Coordination message sent to {message.to_agent_email}")
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
            # Search for coordination emails
            query = f"subject:{self.AGENT_SUBJECT_PREFIX} is:unread"
            messages = self.gmail.get_messages(query=query, max_results=max_messages)
            
            coordination_messages = []
            for message in messages:
                parsed_message = self._parse_coordination_email(message)
                if parsed_message:
                    coordination_messages.append(parsed_message)
                    # Mark as read after parsing
                    self.gmail.mark_as_read(message['id'])
            
            if coordination_messages:
                logger.info(f"Found {len(coordination_messages)} new coordination messages")
            
            return coordination_messages
            
        except Exception as e:
            logger.error(f"Error checking for coordination messages: {e}")
            return []
    
    def _create_coordination_email_body(self, message: CoordinationMessage) -> str:
        """Create structured email body for coordination message"""
        
        # Human-readable header
        human_summary = self._generate_human_summary(message)
        
        # Structured coordination data
        coord_data = {
            'protocol': self.PROTOCOL_VERSION,
            'message_id': message.message_id,
            'conversation_id': message.conversation_id,
            'from_agent': asdict(message.from_agent),
            'message_type': message.message_type.value,
            'timestamp': message.timestamp.isoformat(),
            'priority': message.priority.value,
            'requires_response': message.requires_response,
            'expires_at': message.expires_at.isoformat() if message.expires_at else None,
            'payload': message.payload
        }
        
        # Encode coordination data
        encoded_data = base64.b64encode(json.dumps(coord_data).encode()).decode()
        
        # Create email body
        email_body = f"""
{human_summary}

{self.MESSAGE_SEPARATOR}
COORDINATION_DATA_START
{encoded_data}
COORDINATION_DATA_END
{self.MESSAGE_SEPARATOR}

This is an automated coordination message between Claude Code agents.
Protocol: {self.PROTOCOL_VERSION}
Agent: {self.agent_identity.agent_id}
"""
        
        return email_body.strip()
    
    def _parse_coordination_email(self, gmail_message: Dict[str, Any]) -> Optional[CoordinationMessage]:
        """Parse Gmail message into CoordinationMessage"""
        try:
            # Get message body
            body = self.gmail.extract_message_body(gmail_message['payload'])
            
            # Extract coordination data
            if self.MESSAGE_SEPARATOR not in body:
                return None
            
            # Find encoded data
            data_start = body.find("COORDINATION_DATA_START")
            data_end = body.find("COORDINATION_DATA_END")
            
            if data_start == -1 or data_end == -1:
                return None
            
            encoded_data = body[data_start + len("COORDINATION_DATA_START"):data_end].strip()
            
            # Decode coordination data
            coord_data = json.loads(base64.b64decode(encoded_data).decode())
            
            # Create CoordinationMessage
            from_agent = AgentIdentity(**coord_data['from_agent'])
            
            return CoordinationMessage(
                message_id=coord_data['message_id'],
                message_type=MessageType(coord_data['message_type']),
                from_agent=from_agent,
                to_agent_email=self.agent_identity.user_email,
                timestamp=datetime.fromisoformat(coord_data['timestamp']),
                conversation_id=coord_data['conversation_id'],
                priority=Priority(coord_data['priority']),
                payload=coord_data['payload'],
                requires_response=coord_data['requires_response'],
                expires_at=datetime.fromisoformat(coord_data['expires_at']) if coord_data['expires_at'] else None
            )
            
        except Exception as e:
            logger.error(f"Error parsing coordination email: {e}")
            return None
    
    def _generate_human_summary(self, message: CoordinationMessage) -> str:
        """Generate human-readable summary of coordination message"""
        
        message_type = message.message_type.value.replace('_', ' ').title()
        from_agent = message.from_agent.user_name
        
        summary = f"Agent Coordination: {message_type}\n"
        summary += f"From: {from_agent} ({message.from_agent.agent_id})\n"
        summary += f"Priority: {message.priority.value.upper()}\n"
        summary += f"Time: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Add payload-specific summary
        if message.message_type == MessageType.SCHEDULE_REQUEST:
            if 'meeting_context' in message.payload:
                ctx = message.payload['meeting_context']
                summary += f"Meeting: {ctx.get('subject', 'N/A')}\n"
                summary += f"Duration: {ctx.get('duration_minutes', 'N/A')} minutes\n"
        
        elif message.message_type == MessageType.SCHEDULE_PROPOSAL:
            if 'proposed_times' in message.payload:
                count = len(message.payload['proposed_times'])
                summary += f"Proposed Times: {count} options\n"
        
        return summary

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
            priority=meeting_context.urgency,
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
        """Handle incoming schedule request"""
        
        logger.info(f"Processing schedule request from {message.from_agent.agent_id}")
        
        try:
            # Parse meeting context with proper enum handling
            context_data = message.payload["meeting_context"].copy()
            
            # Convert urgency string to Priority enum if needed
            if 'urgency' in context_data and isinstance(context_data['urgency'], str):
                context_data['urgency'] = Priority(context_data['urgency'])
            
            meeting_context = MeetingContext(**context_data)
            time_preferences = message.payload.get("time_preferences", ["morning", "afternoon"])
            
            # Find available times using calendar integration
            proposed_times = self._find_intelligent_available_times(meeting_context, message.payload)
            
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
                    priority=message.priority,
                    payload=payload
                )
            else:
                # Send rejection with alternatives
                payload = {
                    'original_request_id': message.message_id,
                    'rejection_reason': 'No suitable times found',
                    'alternative_suggestions': self._suggest_alternatives(meeting_context)
                }
                
                return CoordinationMessage(
                    message_id="",
                    message_type=MessageType.SCHEDULE_REJECTION,
                    from_agent=self.agent_identity,
                    to_agent_email=message.from_agent.user_email,
                    timestamp=datetime.now(),
                    conversation_id=message.conversation_id,
                    priority=message.priority,
                    payload=payload,
                    requires_response=False
                )
                
        except Exception as e:
            logger.error(f"Error handling schedule request: {e}")
            return None
    
    def _handle_schedule_proposal(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Handle incoming schedule proposal"""
        
        logger.info(f"Processing schedule proposal from {message.from_agent.agent_id}")
        
        try:
            proposed_times = [self._deserialize_timeslot(slot_data) 
                             for slot_data in message.payload["proposed_times"]]
            
            # Evaluate proposals with contextual intelligence
            best_option = self._evaluate_proposals_intelligently(proposed_times)
            
            if best_option and best_option.confidence_score > 0.7:
                # Accept the proposal
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
                    priority=message.priority,
                    payload=payload,
                    requires_response=False
                )
            else:
                # Send counter-proposal
                counter_proposals = self._generate_counter_proposals(proposed_times)
                
                if counter_proposals:
                    payload = {
                        'original_proposal_id': message.message_id,
                        'counter_proposals': [self._serialize_timeslot(slot) for slot in counter_proposals],
                        'reasoning': 'Suggesting alternatives based on scheduling optimization'
                    }
                    
                    return CoordinationMessage(
                        message_id="",
                        message_type=MessageType.SCHEDULE_COUNTER_PROPOSAL,
                        from_agent=self.agent_identity,
                        to_agent_email=message.from_agent.user_email,
                        timestamp=datetime.now(),
                        conversation_id=message.conversation_id,
                        priority=message.priority,
                        payload=payload
                    )
                
        except Exception as e:
            logger.error(f"Error handling schedule proposal: {e}")
            
        return None
    
    def _handle_schedule_confirmation(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Handle schedule confirmation and create calendar event with attendee invites"""
        
        logger.info(f"Processing schedule confirmation from {message.from_agent.agent_id}")
        
        try:
            # Validate message payload
            if "selected_time" not in message.payload:
                logger.error("Schedule confirmation missing selected_time in payload")
                return None
            
            confirmed_time = self._deserialize_timeslot(message.payload["selected_time"])
            logger.info(f"Confirmed meeting time: {confirmed_time.start_time} - {confirmed_time.end_time}")
            
            # Prepare proper event details with both agents as attendees
            event_details = self._prepare_calendar_event_details(message, confirmed_time)
            logger.info(f"Event details prepared with {len(event_details.get('attendees', []))} attendees")
            
            # Create calendar event with proper attendee list
            event_created = self._create_confirmed_calendar_event(confirmed_time, event_details)
            
            if event_created:
                logger.info(f"✅ Calendar event created successfully for {confirmed_time.start_time}")
                logger.info(f"📧 Invites sent to: {event_details.get('attendees', [])}")
                
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
                    priority=Priority.LOW,
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
                    priority=Priority.LOW,
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
            counter_proposals = [self._deserialize_timeslot(slot_data) 
                               for slot_data in message.payload["counter_proposals"]]
            
            # Evaluate counter-proposals with contextual intelligence
            best_option = self._evaluate_proposals_intelligently(counter_proposals)
            
            # Get conversation history to check for negotiation rounds
            conversation = self.active_conversations.get(message.conversation_id, [])
            negotiation_rounds = len([msg for msg in conversation 
                                    if msg.message_type in [MessageType.SCHEDULE_PROPOSAL, 
                                                          MessageType.SCHEDULE_COUNTER_PROPOSAL]])
            
            # Limit negotiation rounds to prevent infinite back-and-forth
            if negotiation_rounds >= 4:  # Max 4 rounds of negotiation
                logger.info("Maximum negotiation rounds reached, accepting best available option")
                if best_option:
                    # Force acceptance of best option
                    payload = {
                        'proposal_message_id': message.message_id,
                        'selected_time': self._serialize_timeslot(best_option),
                        'confidence_score': best_option.confidence_score,
                        'calendar_event_details': self._prepare_calendar_event_details(message, best_option),
                        'negotiation_complete': True
                    }
                    
                    return CoordinationMessage(
                        message_id="",
                        message_type=MessageType.SCHEDULE_CONFIRMATION,
                        from_agent=self.agent_identity,
                        to_agent_email=message.from_agent.user_email,
                        timestamp=datetime.now(),
                        conversation_id=message.conversation_id,
                        priority=message.priority,
                        payload=payload,
                        requires_response=False
                    )
            
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
                    priority=message.priority,
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
                            priority=message.priority,
                            payload=payload
                        )
                
                # If we can't find alternatives, reject
                return self._create_rejection_message(message, "Unable to find mutually acceptable time")
                
        except Exception as e:
            logger.error(f"Error handling schedule counter-proposal: {e}")
            return self._create_rejection_message(message, f"Error processing counter-proposal: {str(e)}")
    
    def _handle_schedule_rejection(self, message: CoordinationMessage) -> Optional[CoordinationMessage]:
        """Handle incoming schedule rejection"""
        
        logger.info(f"Processing schedule rejection from {message.from_agent.agent_id}")
        
        try:
            rejection_reason = message.payload.get("rejection_reason", "No reason provided")
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
                priority=Priority.LOW,
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
            # Get calendar events for analysis with proper timezone handling
            now = datetime.now()
            search_end = now + timedelta(days=7)
            
            # Use try-catch for calendar API to handle errors gracefully
            existing_events = []
            try:
                existing_events = self.calendar_manager.get_events(
                    time_min=now,
                    time_max=search_end,
                    max_results=50
                )
            except Exception as calendar_error:
                logger.warning(f"Calendar API error (using empty events list): {calendar_error}")
                existing_events = []
            
            # Generate intelligent time slots
            slots = []
            time_preferences = request_payload.get("time_preferences", ["morning", "afternoon"])
            
            for day_offset in range(1, 8):  # Next 7 days
                target_date = now + timedelta(days=day_offset)
                
                # Skip weekends unless explicitly requested
                if target_date.weekday() >= 5:
                    continue
                
                # Generate slots based on preferences and context
                daily_slots = self._generate_intelligent_daily_slots(
                    target_date, meeting_context, time_preferences, existing_events
                )
                
                slots.extend(daily_slots)
            
            # Score and rank slots
            scored_slots = []
            for slot in slots:
                score = self._calculate_contextual_score(slot, meeting_context)
                slot.confidence_score = score
                scored_slots.append(slot)
            
            # Return top 3 slots
            scored_slots.sort(key=lambda x: x.confidence_score, reverse=True)
            return scored_slots[:3]
            
        except Exception as e:
            logger.error(f"Error finding intelligent available times: {e}")
            return []
    
    def _generate_intelligent_daily_slots(self, target_date: datetime, meeting_context: MeetingContext,
                                        time_preferences: List[str], existing_events: List[Dict[str, Any]]) -> List[TimeSlot]:
        """Generate intelligent time slots for a specific day"""
        
        slots = []
        
        # Define time blocks based on preferences
        time_blocks = []
        if "morning" in time_preferences:
            time_blocks.extend([9, 10, 11])  # 9 AM, 10 AM, 11 AM
        if "afternoon" in time_preferences:
            time_blocks.extend([14, 15, 16])  # 2 PM, 3 PM, 4 PM
        if "evening" in time_preferences:
            time_blocks.extend([17, 18])  # 5 PM, 6 PM
        
        for hour in time_blocks:
            start_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
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
                urgency=Priority.MEDIUM,
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
    
    def _deserialize_timeslot(self, slot_data: Dict[str, Any]) -> TimeSlot:
        """Deserialize TimeSlot from message data"""
        return TimeSlot(
            start_time=datetime.fromisoformat(slot_data["start_time"]),
            end_time=datetime.fromisoformat(slot_data["end_time"]),
            confidence_score=slot_data["confidence_score"],
            conflicts=slot_data.get("conflicts", []),
            context_score=slot_data.get("context_score", {})
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
            "urgency_factor": meeting_context.urgency.value,
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
                urgency=Priority.MEDIUM,
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
        
        return {
            "summary": meeting_context.subject,
            "description": f"{meeting_context.description or ''}\n\nCoordinated by Claude Code agents",
            "start_time": selected_time.start_time.isoformat(),
            "end_time": selected_time.end_time.isoformat(),
            "attendees": attendees,
            "coordinated_by_agents": True,
            "coordination_confidence": selected_time.confidence_score
        }
    
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
        """Serialize MeetingContext with enum handling"""
        context_dict = asdict(meeting_context)
        
        # Convert enum to string value
        if isinstance(context_dict.get('urgency'), Priority):
            context_dict['urgency'] = context_dict['urgency'].value
        elif hasattr(context_dict.get('urgency'), 'value'):
            context_dict['urgency'] = context_dict['urgency'].value
        
        return context_dict
    
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
    
    def _create_rejection_message(self, original_message: CoordinationMessage, reason: str) -> CoordinationMessage:
        """Create a rejection message"""
        payload = {
            'original_message_id': original_message.message_id,
            'rejection_reason': reason,
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
            priority=original_message.priority,
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
            user_email = "user@example.com"  # Fallback
            try:
                from gmail_functions import GmailManager
                gmail = GmailManager()
                profile = gmail.service.users().getProfile(userId='me').execute()
                user_email = profile["emailAddress"]
                logger.info(f"Auto-detected Gmail account: {user_email}")
            except Exception as e:
                logger.warning(f"Could not auto-detect Gmail account, using fallback: {e}")
            
            # Generate agent identity from detected email
            email_prefix = user_email.split('@')[0] if '@' in user_email else "claude"
            agent_config = {
                "agent_id": f"{email_prefix}_claude_agent",
                "user_name": user_email.split('@')[0].title() if '@' in user_email else "Claude Agent User",
                "user_email": user_email
            }
        
        # Create agent identity from config
        agent_identity = AgentIdentity(
            agent_id=agent_config.get("agent_id", "claude_agent_v2"),
            user_name=agent_config.get("user_name", "Claude Agent User"),
            user_email=agent_config.get("user_email", "user@example.com"),
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
                                 duration_minutes: int = 30, urgency: str = "medium", 
                                 meeting_type: str = "1:1", attendees: List[str] = None) -> bool:
    """Send intelligent coordination request to target agent"""
    
    coordinator = initialize_integrated_coordination_system()
    
    # Use provided attendees or default to sender and target
    if attendees is None:
        attendees = [coordinator.agent_identity.user_email, target_agent_email]
    
    meeting_context = MeetingContext(
        meeting_type=meeting_type,
        urgency=Priority(urgency),
        duration_minutes=duration_minutes,
        attendees=attendees,
        subject=meeting_subject,
        description=f"Intelligently coordinated {meeting_type} meeting"
    )
    
    return coordinator.send_schedule_request(target_agent_email, meeting_context)

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
            duration_minutes=30,
            urgency="medium"
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