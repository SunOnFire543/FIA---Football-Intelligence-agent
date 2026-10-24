# Data Coverage & Five-Year Pyramid Tracking

## 1. Coverage Philosophy
The Football Intelligence Engine never assumes complete global coverage unless verified. Every competition, season, and market is assigned an explicit state in the `CoverageRegistry`:

- `AVAILABLE`: Complete historical and current telemetry verified.
- `PARTIAL`: Core match results present; player props or count markets uncalibrated.
- `UNAVAILABLE`: Data missing or unsupported.
- `NOT_VERIFIED`: Provider credentials unconfirmed.
- `STALE`: Data has not been refreshed within acceptable latency limits.

## 2. Current 5-Year Coverage Matrix

| Competition Code | Name | Seasons Tracked | Match Events | Lineups | Shots / SOT | Cards / Fouls | Player Props | Coverage Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `PL` | English Premier League | 2022/23 - 2026/27 | Yes | Yes | Yes | Yes | Yes | `AVAILABLE` |
| `PD` | Spanish La Liga | 2022/23 - 2026/27 | Yes | Yes | Yes | Yes | Yes | `AVAILABLE` |
| `CL` | UEFA Champions League | 2022/23 - 2026/27 | Yes | Yes | Yes | Yes | Partial | `PARTIAL` |
| `BL1` | German Bundesliga | Ingestion Ready | - | - | - | - | - | `NOT_VERIFIED` |
| `SA` | Italian Serie A | Ingestion Ready | - | - | - | - | - | `NOT_VERIFIED` |
