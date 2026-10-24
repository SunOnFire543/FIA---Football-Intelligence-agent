# Security Architecture & Policies

## 1. Zero-Trust Tool Execution
- **Strict Allowlisting**: The LLM runtime (`AgentExecutor`) can only invoke explicitly registered Python handlers in `ToolRegistry`.
- **No Arbitrary Code / Shell**: No tool allows the LLM to pass arbitrary shell commands, raw SQL strings, or arbitrary HTTP URLs.
- **Typed Argument Validation**: All inputs and outputs pass through Pydantic schemas.

## 2. Secrets Management
- **Environment Variables**: API keys (`XAI_API_KEY`, `THE_ODDS_API_KEY`, `AGENTVERSE_API_KEY`) are read strictly from environment or `.env`.
- **Masking in Logs**: Secrets are never logged or echoed in exceptions. Masking helpers show only the first 3 and last 4 characters (`xai...cdef`).
- **Git Protection**: `.gitignore` strictly protects `.env`, `*.db`, and credential files.

## 3. Responsible Analytics Notice
The Football Intelligence Engine is purely an analytics, statistical modeling, and odds comparison system.
- **No Betting Execution**: No automated sportsbook login, deposits, withdrawals, or bet placement capabilities are provided or supported.
- **Explicit Advisories**: All generated analyses, parlay candidates, and value opportunities display responsible gambling advisories.
