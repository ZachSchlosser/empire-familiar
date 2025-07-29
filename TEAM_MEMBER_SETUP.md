# Team Member Setup - Agent Coordination System

## 🎯 **What This Enables**

After this setup, you and Zach's agents will be able to automatically coordinate meetings via email:
- Send meeting requests between agents
- Negotiate optimal times automatically  
- Create calendar events when confirmed
- Handle back-and-forth counter-proposals

---

## 🚨 **IMPORTANT: Required Updates**

Zach has fixed critical bugs in the coordination system. You MUST update your files to get:
- ✅ **Counter-proposal handling** (was completely broken)
- ✅ **Rejection message handling** (was missing)
- ✅ **Enum parsing fixes** (auto-responses were failing)
- ✅ **Calendar error handling** (graceful degradation)

---

## 📋 **Prerequisites**

✅ You already have the basic calendar scheduler working  
✅ You have Google Calendar and Gmail API access  
✅ Your `credentials.json` and `token.json` are working  
✅ You can send/receive emails programmatically  

---

## 🔄 **File Updates Required**

### **Critical Update: Replace This File**
**`integrated_agent_coordination.py`** - The main coordination system
- **Why:** Contains all the bug fixes for counter-proposals and auto-responses
- **Action:** Replace your entire file with Zach's updated version

### **Verify These Files Exist** (copy if missing):
- `agent_email_monitor.py` - Email monitoring system
- `coordination_helpers.py` - Easy-to-use helper functions
- `agent_config.py` - Configuration management

---

## ⚙️ **Setup Steps**

### **Step 1: Update Your Code**
```bash
# In your project directory
cp [zach-files]/integrated_agent_coordination.py .
cp [zach-files]/agent_email_monitor.py .
cp [zach-files]/coordination_helpers.py .
cp [zach-files]/agent_config.py .
```

### **Step 2: Install Dependencies** (if needed)
```bash
source calendar_env/bin/activate  # or your venv name
pip install schedule dateutil
```

### **Step 3: Configure Your Agent Identity**
```python
from coordination_helpers import setup_coordination_for_user

# Set this to YOUR information
setup_coordination_for_user(
    user_name="Your Name",
    user_email="your-email@domain.com"
)
```

### **Step 4: Test Basic Email Sending**
```python
from coordination_helpers import schedule_meeting_with_agent

# Test sending to Zach
result = schedule_meeting_with_agent(
    target_email="zach@empire.email",
    meeting_subject="Test from [Your Name]",
    duration_minutes=30
)
print("Sent:", result['coordination_initiated'])
```

### **Step 5: Test Email Monitoring**
```bash
# Test quick check
python3 agent_email_monitor.py quick

# Start continuous monitoring (in separate terminal)
python3 agent_email_monitor.py monitor 60  # Monitor for 1 hour
```

---

## 🧪 **Testing Protocol**

### **Phase 1: One-Way Test**
1. **You send** coordination request to `zach@empire.email`
2. **Zach starts monitoring** with `python3 agent_email_monitor.py monitor 30`
3. **Verify** Zach receives your message and auto-responds

### **Phase 2: Full Coordination Test**  
1. **You send** meeting request to Zach
2. **Zach's agent** responds with 3 time proposals
3. **Your agent** evaluates and either:
   - Confirms one of the times, OR
   - Sends counter-proposal with different times
4. **Continue negotiation** until meeting is confirmed
5. **Verify** calendar event is created on both sides

### **Phase 3: Stress Test**
1. Send multiple coordination requests
2. Test rejection scenarios  
3. Test with conflicting calendar events
4. Verify maximum negotiation rounds (4) work

---

## 🔧 **Troubleshooting**

### **"No auto-response sent"**
- ✅ Check you updated `integrated_agent_coordination.py` 
- ✅ Verify Gmail API permissions
- ✅ Check email monitoring is running

### **"Enum parsing error"**  
- ✅ You MUST use the updated coordination file
- ✅ Old version has critical enum bugs

### **"Calendar API errors"**
- ✅ System will continue working (graceful degradation)
- ✅ Check Calendar API permissions if needed

### **"Email not received"**
- ✅ Check spam folder
- ✅ Verify email addresses are correct
- ✅ Gmail might have delays (wait 30-60 seconds)

---

## 📧 **Quick Reference Commands**

```python
# Send meeting request
from coordination_helpers import schedule_meeting_with_agent
schedule_meeting_with_agent("zach@empire.email", "Project Sync", 30)

# Check for coordination messages  
from integrated_agent_coordination import process_agent_coordination_messages
results = process_agent_coordination_messages()

# Start monitoring
# Terminal: python3 agent_email_monitor.py monitor 60
```

---

## 🎉 **Success Indicators**

You'll know it's working when:
- ✅ Your coordination requests send successfully
- ✅ You receive auto-responses from Zach's agent
- ✅ Back-and-forth negotiation happens automatically
- ✅ Calendar events are created when meetings are confirmed
- ✅ Both agents can initiate coordination

---

## 🔗 **Contact**

If you run into issues:
1. Check you have the latest `integrated_agent_coordination.py` file
2. Verify your Gmail API access is working
3. Test with Zach using the testing protocol above

**The system is designed to be fully autonomous once set up!** 🤖