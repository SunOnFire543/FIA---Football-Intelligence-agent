# Architecture & System Design: Football Intelligence Engine

## 1. System Overview
The **Football Intelligence Engine** is a specialized, memory-efficient sports analytics agent designed for Fetch-A-Thon 3.0. It bridges xAI's **Grok** reasoning capabilities with an uncompromising, deterministic statistical modeling and odds evaluation core in Python.

## 2. Logical Dataflow Architecture

```
USER REQUEST (CLI / Agent Chat Protocol via ASI:One)
        │
        ▼
   GROK REASONING & PLANNING (xAI Responses API)
        │
        ▼
   STRUCTURED EXECUTION PLAN & ALLOWLISTED TOOLS
        │
   ┌────┴──────────────────────────┬────────────────────────┐
   ▼                               ▼                        ▼
FOOTBALL DATA PROVIDER      ODDS PROVIDER          COVERAGE REGISTRY
(Demo, Football-Data.org,   (Demo, The Odds API)   (5-Year Depth Audit)
 API-Football)                     │                        │
   │                               ▼                        ▼
   ▼                      ODDS NORMALISATION       TELEMETRY VERIFICATION
FEATURE ENGINEERING       (Exact matching &        (Available / Partial /
   │                       Margin removal)          Unavailable)
   ▼                               │                        │
STATISTICAL PREDICTION ENGINE ◄────┘                        │
- Bivariate Dixon-Coles Poisson                             │
- Player Prop Per-90 Rates & Minutes                        │
- Niche Count Poisson Distributions                         │
   │                                                        │
   ▼                                                        │
EXPECTED VALUE (EV) ENGINE                                  │
- EV = p * Odds - 1                                         │
   │                                                        │
   ▼                                                        │
PARLAY INTELLIGENCE ENGINE                                  │
- 5-Leg High-Probability Candidate                          │
- 10-Leg Multi-Match Candidate                              │
- Joint Score Matrix & Dependency Modeling                  │
   │                                                        │
   ▼                                                        │
RESULT VERIFICATION & AUDIT PROVENANCE                      │
- Evidence Record & Mathematical Integrity Checks ◄─────────┘
   │
   ▼
GROK SYNTHESIS / FORMATTED REPORT
   │
   ▼
USER RESPONSE (ASI:One / CLI)
```

## 3. Strict Separation of Concerns
1. **Grok (Reasoning LLM)**:
   - Extract intent, teams, competitions, players, and markets.
   - Propose tool calls from allowlisted registry.
   - Interpret structured JSON responses.
   - Never fabricate numerical probabilities or bookmaker prices.
2. **Deterministic Layer (Python / NumPy / SQLite / SQLAlchemy)**:
   - Numerical odds comparison and vig removal.
   - Bivariate Dixon-Coles goal distribution matrix ($8 \times 8$).
   - Expected value ($EV = p \cdot O - 1$).
   - Bounded joint parlay probability calculations.
   - Walk-forward chronological backtesting without future-data leakage.
