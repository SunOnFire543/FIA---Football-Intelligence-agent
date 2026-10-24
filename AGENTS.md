# AGENTS.md - Durable Project Rules for Football Intelligence Engine

## 1. Project Philosophy & Core Mandates
- **Domain**: High-performance, probabilistic Football Analytics & Odds Intelligence Engine.
- **LLM Role**: Grok (official xAI API, Responses API, configurable model e.g. `grok-4.7`). Grok handles intent extraction, tool planning, reasoning over structured outputs, and evidence-backed synthesis.
- **Deterministic Separation**: Grok NEVER invents data, probabilities, odds, or statistical values. All mathematical calculations, probability models, odds normalisation, expected-value metrics, and parlay generation are performed strictly by the deterministic Python application layer.
- **Fail-Safe & Fallback-Free**: If data or credentials are missing or uncalibrated, explicitly report `INSUFFICIENT_DATA` or abstain. Never silently invent numbers or fall back to an unverified secondary LLM.
- **Security & Privacy**: Never log or commit API keys (`XAI_API_KEY`, etc.). Passwords and credentials must reside only in environment variables. Do not execute arbitrary user or LLM code.
- **No Betting Execution**: This is an intelligence and analytics platform. No betting placement, deposit, withdrawal, or sportsbook account actions are supported. Include responsible gambling advisories.

## 2. Directory Layout & Architecture
```
football-intelligence/
├── app/
│   ├── agent/             # Grok client (xAI Responses API), planner, tool registry, executor, response builder
│   ├── config/            # Typed settings via pydantic-settings / pydantic
│   ├── data/              # Multi-provider adapters (Football-Data, The Odds API, API-Football), normalisation, ingestion
│   ├── db/                # SQLAlchemy models, SQLite/PostgreSQL session, migrations
│   ├── features/          # Team and player statistical feature engineering
│   ├── models/            # Poisson & Dixon-Coles match models, player props, niche count models, probability validator
│   ├── odds/              # Odds normalisation, comparison across bookmakers, vig removal, expected-value engine
│   ├── parlays/           # 5-leg and 10-leg candidate generators, joint probability & dependency models, quote validator
│   ├── evaluation/        # Walk-forward chronological backtesting, Brier score, log loss, calibration, ROI
│   ├── verification/      # Result verification, compact evidence records, data provenance
│   ├── schemas/           # Pydantic schemas for requests, responses, tool inputs/outputs
│   ├── fetch/             # Fetch.ai Agentverse / ACP / ASI:One integration layer
│   └── main.py            # CLI and application entrypoint
├── docs/                  # Architecture, Build Status, Data Sources, Methodology, Fetch.ai Setup
├── tests/                 # Unit, integration, and mock fixtures
└── scripts/               # Ingestion, demo, and evaluation scripts
```

## 3. Coding & Data Standards
- **Memory Efficiency**: Ingest in chunks, use bounded database queries and pagination, and avoid loading massive 5-year raw payloads into memory. Context sent to Grok must be structured summaries, not raw databases.
- **Type Safety**: Enforce Pydantic models for all tool inputs, outputs, and internal message passing.
- **Mathematical Integrity**: All probabilities must satisfy $p \in [0, 1]$, outcome spaces must sum to $1.0 \pm 10^{-5}$, and dependent same-match legs must never be calculated using naive independence multiplication.
- **Temporal Integrity**: Strictly respect prediction cutoffs to avoid future-data leakage in all backtests and evaluations.
- **Documentation**: Keep `docs/BUILD_STATUS.md` updated with actual test status, verified providers, and implementation phases.
