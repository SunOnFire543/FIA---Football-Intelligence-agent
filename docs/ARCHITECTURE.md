# Architecture & System Design: Football Intelligence Engine

## 1. System Overview
The **Football Intelligence Engine** is a specialized, memory-efficient sports analytics agent designed for Fetch-A-Thon 3.0. It bridges **Groq's** high-speed reasoning and built-in browser-search capabilities (`openai/gpt-oss-120b`) with an uncompromising, deterministic statistical modeling and odds evaluation core in Python.

## 2. Logical Dataflow Architecture

```
USER REQUEST (CLI / Agent Chat Protocol via ASI:One)
        │
        ▼
   GROQ REASONING & PLANNING (Groq API: openai/gpt-oss-120b)
        │
        ├─────────────────────────────────────────────────┐
        ▼                                                 ▼
   ALLOWLISTED LOCAL PYTHON TOOLS                   BUILT-IN BROWSER SEARCH
   (Deterministic execution in Python)             (Executed on Groq servers)
        │                                                 │
   ┌────┴──────────────────────────┬────────────────┐     ▼
   ▼                               ▼                ▼   GROUNDING CITATIONS
FOOTBALL DATA PROVIDER      ODDS PROVIDER    COVERAGE   (Extracted URLs &
(Demo, Football-Data.org,   (Demo, The Odds  REGISTRY    freshness audit)
 API-Football)               API)                   │     │
   │                               │                │     │
   ▼                               ▼                │     │
FEATURE ENGINEERING         ODDS NORMALISATION      │     │
   │                        (Exact matching &       │     │
   ▼                         Margin removal)        │     │
STATISTICAL PREDICTION ENGINE ◄────┘                │     │
- Bivariate Dixon-Coles Poisson                     │     │
- Player Prop Per-90 Rates & Minutes                │     │
- Niche Count Poisson Distributions                 │     │
   │                                                │     │
   ▼                                                │     │
EXPECTED VALUE (EV) ENGINE                          │     │
- EV = p * Odds - 1                                 │     │
   │                                                │     │
   ▼                                                │     │
PARLAY INTELLIGENCE ENGINE                          │     │
- 5-Leg High-Probability Candidate                  │     │
- 10-Leg Multi-Match Candidate                      │     │
- Joint Score Matrix & Dependency Modeling          │     │
   │                                                │     │
   ▼                                                │     │
RESULT VERIFICATION & AUDIT PROVENANCE              │     │
- Evidence Record & Mathematical Integrity Checks ◄─┴─────┘
   │
   ▼
GROQ SYNTHESIS & REPORT BUILDER
   │
   ▼
USER RESPONSE (ASI:One / CLI)
```

## 3. Strict Separation of Concerns
1. **Groq (Reasoning LLM & Browser Search)**:
   - Extract intent, teams, competitions, players, and markets.
   - Propose tool calls from allowlisted registry.
   - Execute real-time web browsing via Groq's built-in `browser_search` tool (`openai/gpt-oss-120b`).
   - Extract citations, publication dates, and source claims.
   - Synthesize evidence-backed final reports.
   - Never fabricate numerical probabilities or bookmaker prices.
2. **Deterministic Layer (Python / NumPy / SQLite / SQLAlchemy)**:
   - Numerical odds comparison and vig removal.
   - Bivariate Dixon-Coles goal distribution matrix ($8 \times 8$).
   - Expected value ($EV = p \cdot O - 1$).
   - Bounded joint parlay probability calculations.
   - Walk-forward chronological backtesting without future-data leakage.

## 4. Fetch-A-Thon Architectural Trade-Off
- **Role of Groq**: Groq serves as the primary reasoning, workflow planning, and tool orchestration LLM.
- **Role of Fetch.ai uAgents**: uAgents provides the native agent identity (`agent1qtld...`), lifecycle management, and Agent Chat Protocol (ACP v0.3.0) message handling for ASI:One compatibility.
- **Accurate Disclosure**: Groq is not ASI1 and does not claim to be ASI1. The system architecture leverages Fetch.ai's decentralized agent communication framework while deploying Groq for ultra-low-latency deterministic sports reasoning.
