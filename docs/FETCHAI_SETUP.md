# Fetch.ai, uAgents & Agentverse Integration Guide

## 1. Hackathon Status & Scope
- **uAgents Framework**: **IMPLEMENTED & TESTED WITH MOCKS** (`app/fetch/uagent_service.py`).
- **Agent Chat Protocol (ACP)**: **IMPLEMENTED & TESTED WITH LOCAL SIMULATION** (`app/fetch/acp_server.py`).
- **Agentverse Registration**: **REGISTRATION REQUIRED** (Awaiting user Agentverse account setup and mailbox key).
- **ASI:One Live Discoverability**: **NOT VERIFIED** (Pending Agentverse public deployment).

---

## 2. Running the uAgent Locally
The application instantiates an authentic Fetch.ai `uagents.Agent`:

```bash
python -m app.main run-uagent
```

Output:
```text
[+] Starting uAgents runtime for FootballIntelligenceAgent...
[+] uAgent instantiated with address: agent1qtldj59wykss0ygez49dntapnexx6aq204zz9nkjc4rutepj7xj0ksmk5v4
[+] Registered protocols: ['AgentChatProtocol']
[+] Starting agent event loop...
```

The agent generates a unique, deterministic cryptographic address based on `AGENT_SEED` and registers `FootballIntelligenceProtocol` for message exchange.

---

## 3. Local ACP Message Simulation
You can simulate the Agent Chat Protocol message loop locally before connecting to live Agentverse:

```bash
python -m app.main acp-query "Analyse the next Arsenal match"
```

This executes a complete local ACP simulation (`ACPMessageRequest` -> Pipeline Execution -> `ACPMessageResponse`), returning a formatted intelligence report.

---

## 4. Manual Steps for Agentverse Deployment & ASI:One Discovery
To deploy this agent live on the Agentverse network:

1. **Create an Agentverse Account**:
   - Sign up at [Agentverse](https://agentverse.ai/).
2. **Obtain an Agent Mailbox Key**:
   - Navigate to **Agentverse -> Mailroom**.
   - Create a new mailbox for `agent1q...` (the address printed by `python -m app.main run-uagent`).
   - Copy the generated mailbox API key.
3. **Configure Environment**:
   - In `.env`, set:
     ```bash
     AGENTVERSE_API_KEY=<your_agentverse_mailbox_key>
     AGENT_SEED="your_chosen_secret_seed_phrase"
     ```
4. **Start the Mailbox Agent**:
   - Run `python -m app.main run-uagent`.
   - The agent will connect to the Agentverse mailbox over WebSocket/HTTP.
5. **Publish to ASI:One**:
   - In Agentverse, navigate to **Agent Details -> Discoverability**.
   - Paste the contents of `python -m app.main manifest` into the Agentverse agent profile.
   - Toggle **Public Discoverability** to ON.
   - Once verified by Agentverse, the agent becomes searchable inside [ASI:One](https://asi.one/).

---

## 5. Fetch-A-Thon Architecture & LLM Disclosure
- **Framework Compliance**: The agent natively runs on `uagents` (Fetch.ai official Python framework) implementing `AgentChatProtocol:0.3.0` (`uagents_core.contrib.protocols.chat`).
- **Primary LLM Reasoning**: Cognitive reasoning, tool-calling planning, and real-time grounding are powered by **Groq** (`openai/gpt-oss-120b` with built-in `browser_search`).
- **ASI:One / ASI1 Transparency**: Groq is not ASI1 and is not claimed to be ASI1. FIA combines Fetch.ai's decentralized agent communication protocol with Groq's ultra-fast reasoning and Exa-powered browser search.
