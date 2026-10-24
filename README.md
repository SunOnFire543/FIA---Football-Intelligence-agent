# Football Intelligence Engine

![tag](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag](https://img.shields.io/badge/hackathon-5F43F1)

> **A Groq-Powered, Fetch.ai-Compatible Football Analytics and Odds Intelligence Agent for Fetch-A-Thon 3.0**

---

## 1. Project Overview & Current Implementation Status

The **Football Intelligence Engine** is a specialized sports analytics and betting intelligence agent. It strictly decouples reasoning (handled by **Groq** using `openai/gpt-oss-120b` and built-in `browser_search`) from deterministic quantitative computations (handled in Python with NumPy, SQLAlchemy, and Pydantic).

### Evidentiary Status Breakdown
All capabilities are classified using rigorous verification statuses:

| Component | Status | Operational Notes |
| :--- | :--- | :--- |
| **Groq LLM Client** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` / `VERIFIED_WITH_LIVE_PROVIDER` | Uses official Groq API (`POST /chat/completions`) with `openai/gpt-oss-120b`. Verified with live authentication and deterministic mocks. Requires `GROQ_API_KEY`. |
| **Tool Registry & Executor** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | 18 typed allowlisted tools, max 8 rounds, anti-looping protection. |
| **Groq Web Intelligence & Grounding** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` / `VERIFIED_WITH_LIVE_PROVIDER` | Groq built-in `browser_search` tool integration, citation parsing, selective search policy, source-quality tiering, and conflict auditing. |
| **uAgents Native Runtime** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | Instantiates genuine `uagents.Agent` with cryptographic address (`agent1qtld...`) and registered protocol. |
| **Agent Chat Protocol (ACP)** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | Tested via local simulation CLI (`acp-query`). |
| **Agentverse Registration** | `REGISTRATION_REQUIRED` | Awaiting user account setup and Agentverse mailbox activation for `agent1qtldj59wykss0ygez49dntapnexx6aq204zz9nkjc4rutepj7xj0ksmk5v4`. |
| **ASI:One Discoverability** | `NOT_VERIFIED` | Pending Agentverse live deployment. Manifest generated and validated. |
| **Bivariate Dixon-Coles Goal Model** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | $8 \times 8$ joint score matrix, low-score adjustment ($\rho = -0.08$ provisional literature baseline). |
| **Player Prop Model** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | Per-90 Poisson event rates for Shots, SOT, and Anytime Goalscorer. Minutes modulated by lineup status. |
| **Cross-Bookmaker Odds & EV Engine** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | Exact threshold matching, proportional vig removal, $EV = p \cdot O - 1$. Stale/suspended odds filtered. |
| **Parlay Engine (5 & 10 Legs)** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | Same-match joint score matrix summation. Explicit abstention when screening criteria fail. |
| **Temporal Backtesting Engine** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | Sequential walk-forward simulation strictly prior to cutoff timestamp to eliminate future-data leakage. |
| **Result Verification & Audit** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | Compact audit record (`CompactEvidenceRecord`) verifying bounds, calculation consistency, and data mode. |
| **Demo Data Provider** | `IMPLEMENTED` / `TESTED_WITH_MOCKS` | High-fidelity synthetic dataset for deterministic offline testing. Explicitly marked as simulated. |
| **Live Data Adapters** | `IMPLEMENTED` / `WAITING_FOR_CREDENTIALS` | Football-Data.org, API-Football, and The Odds API adapters implemented; require user API keys for live mode. |

---

## 2. Strict Separation: DEMO Mode vs. LIVE Mode

The engine implements an explicit application mode setting (`DATA_MODE`):

### DEMO Mode (`DATA_MODE=DEMO` - Default)
- Uses deterministic, clearly labeled synthetic test data.
- Conspicuously labels all reports with `[DATA MODE: DEMO (SIMULATED)]`.
- Marks bookmaker prices as simulated lines.
- Does NOT claim verified 5-year historical depth or real-world profitability.
- Enables complete, reproducible offline development and automated testing without external API credentials.

### LIVE Mode (`DATA_MODE=LIVE`)
- Requires valid credentials for external providers (`FOOTBALL_DATA_API_KEY` or `API_FOOTBALL_KEY`; `THE_ODDS_API_KEY`).
- Records live source identifiers, observation timestamps, and data freshness.
- Strictly refuses to invent fallback data: if a provider is unconfigured or returns insufficient data, the system reports `INSUFFICIENT_DATA` or `UNCONFIGURED_PROVIDER` rather than silently substituting demo data.

---

## 3. Submission & Agentverse Details

- **Agent Name**: `FootballIntelligenceAgent`
- **Agent Address**: `agent1qtldj59wykss0ygez49dntapnexx6aq204zz9nkjc4rutepj7xj0ksmk5v4` *(Cryptographic address generated from `AGENT_SEED`)*
- **Agentverse Profile Link**: `[REGISTRATION_REQUIRED: Follow docs/FETCHAI_SETUP.md]`
- **ASI:One Shared-Chat Link**: `[NOT_VERIFIED: Requires live Agentverse deployment]`
- **Public Repository URL**: `[PENDING AUTHORIZATION]`

---

## 4. Quickstart & Installation

### Requirements
- Python 3.11+ (Python 3.14 compatible)
- Git

### 1. Installation
```bash
git clone <repository-url>
cd football-intelligence
python -m pip install -e .
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env:
# LLM_PROVIDER=groq
# GROQ_API_KEY=your_groq_api_key_here
# GROQ_MODEL=openai/gpt-oss-120b
# DATA_MODE=DEMO
# FOOTBALL_DATA_API_KEY=your_key_here (optional for live mode)
# THE_ODDS_API_KEY=your_key_here (optional for live mode)
```

### 3. Run Automated Tests
```bash
python -m pytest tests -v
```
All **39 automated unit and regression tests** execute in under 7 seconds.

---

## 5. Demonstration Plan (3 to 5 Minutes)

### Step 1: Discoverability Manifest & Protocol Inspection (1 min)
Inspect the registered capabilities, supported competitions, and ACP endpoints:
```bash
python -m app.main manifest
```

### Step 2: Full End-to-End Match Intelligence Analysis in DEMO Mode (2 mins)
Execute the complete workflow for the Arsenal vs Chelsea fixture:
```bash
python -m app.main --mode DEMO analyze "Arsenal"
```
Demonstrates:
- Fixture resolution with explicit `[DATA MODE: DEMO (SIMULATED)]` notice.
- Dixon-Coles goal model: Expected goals **1.78 - 0.66**, provisional $\rho = -0.08$.
- 1X2 Probabilities: Home 63.4%, Draw 24.1%, Away 12.5% (Partition sum = 1.0).
- Monotonic Over/Under (Over 0.5: 90.4% $\ge$ Over 1.5: 70.7% $\ge$ Over 2.5: 43.9%).
- Odds comparison with simulated bookmaker lines & EV calculation.
- **Parlay A (5 Legs)**: Evaluated using bivariate score matrix joint probability (37.7%).
- **Parlay B (10 Legs)**: Multi-match combination evaluated across fixtures.
- Audit Record ID (`EVID_...`) verifying probability bounds and calculation integrity.

### Step 3: Verify LIVE Mode Fail-Safe Behavior (1 min)
Demonstrate that LIVE mode strictly refuses to fabricate fallback data when provider keys are absent:
```bash
python -m app.main --mode LIVE analyze "Arsenal"
```
Output:
```text
[-] LIVE MODE ERROR: Football data provider credentials are not configured.
    Please set FOOTBALL_DATA_API_KEY or API_FOOTBALL_KEY in your .env file.
    The Football Intelligence Engine strictly refuses to fabricate fallback data.
```

### Step 4: Local ACP Message Simulation (1 min)
Simulate an Agent Chat Protocol message exchange:
```bash
python -m app.main acp-query "Analyse the next Arsenal match"
```

### Step 5: Chronological Walk-Forward Backtesting (1 min)
Demonstrate temporal evaluation without future-data leakage:
```bash
python -m app.main evaluate --competition PL
```

---

## 6. Statistical Assumptions & Audit Notes
1. **Dixon-Coles Parameter $\rho$**: Provisional literature baseline $\rho = -0.08$ based on Dixon & Coles (1997). Empirical estimation via maximum likelihood requires $\ge 30$ historical matches.
2. **Score Matrix Upper Tail**: Goals are computed across an $8 \times 8$ matrix ($0 \dots 7$ goals per team). The residual upper tail mass ($\ge 8$ goals) is tracked and bounded ($< 1\%$).
3. **Player Playing-Time**: When official lineups are unconfirmed, player prop event rates carry an explicit uncertainty flag (`uncertainty_score = 0.35`).
4. **Single-Match Settlement**: All markets evaluate standard regular time (90 minutes + stoppage time). Extra time and penalty shootouts are excluded.
5. **Backtest Interpretation**: Backtesting demonstrates algorithm behavior on historical samples; it is not a guarantee of future returns.

---

## 7. Responsible Gambling Advisory
> [!IMPORTANT]
> **Responsible Gambling Advisory**: The Football Intelligence Engine is purely an analytical and probabilistic modeling platform. Probabilities and expected values represent statistical outputs derived from historical records. Sports events inherently possess variance; no outcome or parlay is guaranteed. Never wager money you cannot afford to lose.
