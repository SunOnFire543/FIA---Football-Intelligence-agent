# Fetch.ai, Agentverse & ASI:One Integration Setup

## 1. Hackathon Overview
This application satisfies the **Fetch-A-Thon 3.0** requirements:
- **Agentverse Registration**: Discoverable agent profile with defined capabilities.
- **Agent Chat Protocol (ACP)**: Standardized messaging protocol for communication.
- **ASI:One Native Flow**: Completes multi-step reasoning, tool execution, and analytical reports entirely within an ASI:One chat conversation.

---

## 2. Agent Discoverability Manifest
The agent exports its discoverability manifest at startup or via CLI:
```bash
python -m app.main manifest
```

Manifest JSON:
```json
{
  "name": "FootballIntelligenceAgent",
  "version": "1.0.0",
  "description": "Grok-powered Football Analytics and Odds Intelligence Agent. Provides probabilistic Dixon-Coles goal modeling, multi-bookmaker odds comparison, statistical expected value (EV), and 5-leg & 10-leg parlay intelligence.",
  "protocols": [
    "agent-chat-protocol/v1",
    "uagents/v1"
  ],
  "supported_competitions": [
    "Premier League (PL)",
    "La Liga (PD)",
    "UEFA Champions League (CL)"
  ],
  "supported_markets": [
    "Match Result (1X2)",
    "Double Chance",
    "Over / Under Total Goals (0.5 to 4.5)",
    "Both Teams To Score (BTTS)",
    "Player Shots & Shots On Target (SOT)",
    "Anytime Goalscorer",
    "Total Match Corners",
    "Total Cards & Fouls"
  ],
  "endpoints": {
    "acp": "/acp/message",
    "health": "/health"
  }
}
```

---

## 3. Agentverse Registration Instructions
1. Navigate to [Agentverse](https://agentverse.ai/) and log in with your credentials.
2. Select **My Agents** -> **Create Agent**.
3. Choose **Hosted Agent** or **Local Agent Proxy** pointing to your public endpoint or ngrok tunnel (`http://<your-host>:8000/submit`).
4. Enter `AGENT_NAME`: `FootballIntelligenceAgent`.
5. Copy your Agentverse API Key into your `.env`:
   ```bash
   AGENTVERSE_API_KEY=your_key_here
   AGENT_SEED="football_intelligence_engine_secure_seed"
   ```
6. Set the Agent Chat Protocol (ACP) handler endpoint to `/acp/message`.
7. Publish the agent to make it discoverable in **ASI:One**.

---

## 4. ASI:One Verification Steps
1. Open the [ASI:One](https://asi.one/) agent interface.
2. Search for `FootballIntelligenceAgent`.
3. Start a chat and send the test prompt:
   > "Analyse the next Arsenal match using historical statistics, compare current bookmaker odds, and generate a five-leg and ten-leg parlay if the data supports them."
4. Verify that:
   - Match expected goals are computed.
   - 1X2 and Over/Under probabilities are generated.
   - Cross-bookmaker odds and positive EV opportunities are identified.
   - Exactly 5-leg and 10-leg candidates are constructed with joint probabilities.
   - The result verification audit ID (`EVID_...`) is presented.
