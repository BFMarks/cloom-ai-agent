# 🤖 Cloom AI Voice Agent

AI phone system: **Twilio → Asterisk → LiveKit → AI Agent**

Call **+1 (786) 628-9740** to talk to the AI!

---

## 🚀 Top 5 Commands Per Server

### **LiveKit/Agent Server** (18.116.27.160)
```bash
# SSH in
ssh -i /Users/bryanmarks/Downloads/CloomAI.pem ubuntu@18.116.27.160

# 1. Restart AI agent
sudo systemctl restart voice-agent

# 2. Watch agent logs live
sudo journalctl -u voice-agent -f

# 3. Edit AI personality/code
nano ~/sip/agent-starter-python/src/agent.py

# 4. Pull code updates from GitHub
cd ~/sip/agent-starter-python && git pull my-repo main && sudo systemctl restart voice-agent

# 5. Test agent manually (see all output)
cd ~/sip/agent-starter-python && source venv/bin/activate && python src/agent.py dev
```

### **Asterisk Server** (3.21.228.204)
```bash
# SSH in
ssh -i /Users/bryanmarks/Downloads/CloomAI.pem ubuntu@3.21.228.204

# 1. Watch live calls
sudo asterisk -rvvvvv

# 2. Restart Asterisk
sudo systemctl restart asterisk

# 3. Edit call routing
sudo nano /etc/asterisk/extensions.conf && sudo asterisk -rx "dialplan reload"

# 4. Edit SIP config (trunks/endpoints)
sudo nano /etc/asterisk/pjsip.conf && sudo asterisk -rx "pjsip reload"

# 5. Check endpoints status
sudo asterisk -rx "pjsip show endpoints"
```

---

## 🎨 Customize the AI

### Change Personality
```bash
# Edit src/agent.py, find:
instructions="""YOUR INSTRUCTIONS HERE"""
```

### Change Voice
```python
tts=cartesia.TTS(voice="VOICE_ID_HERE")
```

### Change Model
```python
llm=openai.LLM(model="gpt-4o")  # Smarter but slower/expensive
```

---

## 🔄 Deploy Workflow
```bash
# 1. Local: Make changes
# 2. Local: Commit and push
git add .
git commit -m "Your changes"
git push

# 3. Server: Pull and restart
ssh -i /Users/bryanmarks/Downloads/CloomAI.pem ubuntu@18.116.27.160
cd ~/sip/agent-starter-python
git pull my-repo main
sudo systemctl restart voice-agent
```

---

## 📞 Testing

**Production:** Call +1 (786) 628-9740

**Local Test:**
- Use Zoiper to connect to `3.21.228.204`
- Username: `1001`, Password: `SecurePassword123`
- Dial extension `1000`

---

## 🔍 Additional Commands

### Service Status
```bash
# Agent
sudo systemctl status voice-agent

# Asterisk
sudo systemctl status asterisk

# Docker (LiveKit + SIP)
sudo docker ps
```

### View Logs
```bash
# Agent (recent 100 lines)
sudo journalctl -u voice-agent -n 100 --no-pager

# LiveKit container
sudo podman logs sip_livekit_1 --tail 50

# SIP container
sudo podman logs sip_sip_1 --tail 50
```

### Edit API Keys
```bash
# On 18.116.27.160
nano ~/sip/agent-starter-python/.env.local
# Edit OPENAI_API_KEY, DEEPGRAM_API_KEY, CARTESIA_API_KEY
sudo systemctl restart voice-agent
```

### Asterisk Diagnostics
```bash
sudo asterisk -rx "core show channels"     # Active calls
sudo asterisk -rx "pjsip show contacts"    # Registered endpoints
sudo tcpdump -i any -n port 5060 -v        # Watch SIP traffic
```

### Docker Management
```bash
cd ~/sip
sudo docker-compose restart    # Restart all
sudo docker-compose down       # Stop all
sudo docker-compose up -d      # Start all
```

---

## 🆘 Quick Fixes

**Agent not responding:**
```bash
ssh -i /Users/bryanmarks/Downloads/CloomAI.pem ubuntu@18.116.27.160
sudo systemctl restart voice-agent
sudo journalctl -u voice-agent -n 50
```

**Calls not connecting:**
```bash
ssh -i /Users/bryanmarks/Downloads/CloomAI.pem ubuntu@3.21.228.204
sudo asterisk -rvvvvv
# Make test call and watch for errors
```

**No audio:**
- Check AWS Security Groups allow UDP 10000-20000
- Verify `direct_media=no` in `/etc/asterisk/pjsip.conf`

---

## 📁 Key Files

**LiveKit Server:**
- `~/sip/agent-starter-python/src/agent.py` - AI code
- `~/sip/agent-starter-python/.env.local` - API keys
- `/etc/systemd/system/voice-agent.service` - Service config

**Asterisk Server:**
- `/etc/asterisk/pjsip.conf` - SIP configuration
- `/etc/asterisk/extensions.conf` - Call routing

---

## 📊 Architecture
```
Phone → Twilio (+17866289740)
    ↓
Asterisk PBX (3.21.228.204)
    ↓
LiveKit Server (18.116.27.160)
    ↓
AI Agent (OpenAI + Deepgram + Cartesia)
```

**Servers:**
- **18.116.27.160**: LiveKit + AI Agent
- **3.21.228.204**: Asterisk PBX

**Test Extension:** 1001 @ 3.21.228.204git commit -m "Add streamlined README"