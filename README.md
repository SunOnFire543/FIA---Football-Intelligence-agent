# Football Intelligence Engine

![tag](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag](https://img.shields.io/badge/hackathon-5F43F1)

> **A Grok-Powered, Fetch.ai-Compatible Football Analytics and Odds Intelligence Agent for Fetch-A-Thon 3.0**

---

## 1. Problem Statement & Target Users

### The Problem
Modern sports betting and football analytics are plagued by two opposing extremes:
1. **Opaque LLM Hallucinations**: Generic chatbots routinely invent statistics, fabricate bookmaker odds, generate impossible joint probabilities, and produce ungrounded betting advice without mathematical rigor.
2. **Fragmented Quantitative Tools**: Traditional odds scrapers and statistical models lack contextual reasoning, conversational flexibility, and the ability to autonomously plan multi-step analyses across fixtures, player props, and niche markets.

### Target Users
- **Sports Analysts & Bettors**: Seeking mathematically verified expected-value ($EV = p \cdot O - 1$) opportunities and defensible parlay combinations.
- **ASI:One & Agentverse Users**: Discovering autonomous intelligence agents capable of answering complex analytical questions within a single chat conversation.
- **Syndicates & Quantitative Modellers**: Requiring transparent probability derivations, temporal leakage protection, and tamper-evident audit trails.

---

## 2. Core Differentiating Features

1. **Grok as Orchestration Brain**: Uses the official xAI API (`grok-4.7`) for intent extraction, planning, and structured reasoning. Grok never invents probabilities or prices—all mathematics is handled by the deterministic application layer.
2. **Bivariate Dixon-Coles Goal Model**: Implements low-score correlation adjustments ($\tau_{\lambda, \mu}(x, y)$ with parameter $\rho = -0.08$) generating full $8 \times 8$ score matrices for Home/Draw/Away, Double Chance, Over/Under (0.5 to 4.5), and BTTS.
3. **Player Prop & Niche Count Engines**: Models individual player shots, shots on target (SOT), and anytime goalscorer markets using per-90 event rates adjusted for starting lineups and expected minutes.
4. **Cross-Bookmaker Odds Intelligence**: Compares Pinnacle, Bet365, and Unibet for exact threshold equivalence, strips bookmaker margins (vig removal), and calculates expected net return per unit stake.
5. **Rigorous Parlay Intelligence**: Generates dedicated **5-leg** and **10-leg** candidates. Crucially, same-match parlays calculate joint probabilities directly from the bivariate score distribution matrix rather than multiplying correlated legs independently. The system explicitly abstains when data is insufficient.
6. **Temporal Walk-Forward Backtesting**: Validates models sequentially across chronological fixtures to strictly prevent future-data leakage, reporting Brier scores, log loss, and simulated ROI.
7. **Tamper-Evident Audit Records**: Generates a `CompactEvidenceRecord` (`EVID_...`) verifying calculations, bounds, freshness, and data provenance for every generated report.
8. **Native Fetch.ai / ASI:One Compatibility**: Fully implements the Agent Chat Protocol (ACP) and discoverability manifest.

---

## 3. High-Level Architecture

```
USER QUERY (ASI:One / CLI)
     │
     ▼
GROK REASONING & PLANNING (xAI Responses API)
     │
     ▼
ALLOWLISTED TOOL EXECUTOR (17 Typed Tools, Max Rounds, Anti-Loop Protection)
     │
     ├── Football Data & 5-Year Coverage Registry
     ├── Dixon-Coles Goal Model & Player Prop Engine
     ├── Odds Normalisation & Vig Removal Engine
     ├── Expected Value Engine (EV = p * O - 1)
     ├── 5-Leg & 10-Leg Parlay Intelligence (Joint Score Matrix)
     └── Result Verification & Evidence Provenance Layer
     │
     ▼
VERIFIED INTELLIGENCE REPORT
```

---

## 4. Role of Grok

Grok is responsible for high-level cognitive orchestration:
- Interprets user inquiries (e.g. *"Analyse the next Arsenal match, check player markets, compare bookmaker odds, and build a 5-leg and 10-leg parlay"*).
- Extracts entities: competitions, teams, players, thresholds, constraints.
- Formulates an execution plan and selects tools from the allowlisted registry.
- Synthesizes an evidence-backed final response.

**What Grok Never Does**:
- Never invents probabilities or odds.
- Never overrides deterministic mathematical calculations.
- Never manufactures substitute players, lineups, or historical records.

---

## 5. Submission & Agentverse Details

- **Agent Name**: `FootballIntelligenceAgent`
- **Agent Address**: `agent1q...` *(Configurable via `AGENT_SEED` upon deployment)*
- **Agentverse Profile**: `https://agentverse.ai/agents/...` *(Placeholder for deployment)*
- **ASI:One Shared Chat Demo**: `https://asi.one/chat/...` *(Placeholder for live shared session)*
- **Public Repository URL**: `https://github.com/.../football-intelligence` *(Placeholder pending publish authorization)*

---

## 6. Quickstart & Installation

### Requirements
- Python 3.11+ (Python 3.12 or 3.14 recommended)
- Git

### 1. Clone & Install
```bash
git clone <repository-url>
cd football-intelligence
python -m pip install -e .
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials:
# XAI_API_KEY=your_xai_key_here
# FOOTBALL_DATA_API_KEY=your_key_here (optional)
# THE_ODDS_API_KEY=your_key_here (optional)
```

### 3. Run Automated Tests
```bash
python -m pytest tests -v
```
*(All 20 unit and integration tests execute in < 2 seconds).*

---

## 7. Demonstration Plan (3 to 5 Minutes)

### Step 1: Discoverability Manifest & Protocol Inspection (1 min)
Inspect the registered capabilities, supported competitions, and ACP endpoints:
```bash
python -m app.main manifest
```

### Step 2: Full End-to-End Match Intelligence Analysis (2 mins)
Execute the complete workflow for the upcoming Arsenal vs Chelsea match:
```bash
python -m app.main analyze "Arsenal"
```
Demonstrates:
- Automatic fixture resolution (`FIX_ARS_CHE_2026`).
- 5-year data coverage audit (`AVAILABLE` for Premier League).
- Dixon-Coles goal model: Expected goals **1.78 - 0.66**, $\rho = -0.08$.
- 1X2 Probabilities: Home 63.4%, Draw 24.1%, Away 12.5% (Sum = 1.0).
- Cross-bookmaker best odds discovery (Pinnacle 1.86, Bet365 1.82).
- Positive EV Selections: Home Win (+18.0% EV), Under 2.5 (+20.7% EV), Saka Over 0.5 SOT (+13.7% EV).
- **Parlay A (5 Legs)**: Same-match combination evaluated with joint score matrix (Joint Prob: 37.7%, Combined Odds: 11.15).
- **Parlay B (10 Legs)**: Multi-match comprehensive accumulator (Joint Prob: 7.55%, Combined Odds: 118.61).
- Tamper-evident audit record (`EVID_...`).

### Step 3: Simulated ASI:One Conversation Message (1 min)
Simulate an incoming Agent Chat Protocol (ACP) query from ASI:One:
```bash
python -m app.main acp-query "Analyse the next Arsenal match"
```

### Step 4: Chronological Walk-Forward Backtesting (1 min)
Demonstrate temporal evaluation without future-data leakage:
```bash
python -m app.main evaluate --competition PL
```

---

## 8. Responsible Gambling Notice
> [!IMPORTANT]
> **Responsible Gambling Advisory**: The Football Intelligence Engine is purely an analytical and probabilistic modeling platform. Probabilities and expected values represent statistical outputs derived from historical records. Sports events inherently possess variance; no outcome or parlay is guaranteed. Never wager money you cannot afford to lose.
