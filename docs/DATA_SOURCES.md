# Data Sources & Multi-Provider Architecture

## 1. Supported Providers

### 1.1 Football Data Providers
| Provider | Role | Endpoints Used | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Demo Provider** | Baseline / Testing | Local 5-Year Telemetry Fixtures | **Active & Verified** | High-fidelity multi-season match, player, and lineup datasets. |
| **Football-Data.org** | Production League Data | `/competitions`, `/matches` | **Implemented** | Free/Tier-1 API key supported. Covers major European leagues. |
| **API-Football** | Deep Event Telemetry | `/leagues`, `/fixtures`, `/players` | **Implemented** | RapidAPI / Direct key supported. Covers cards, fouls, and lineups. |

### 1.2 Bookmaker Odds Providers
| Provider | Role | Endpoints Used | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Demo Odds Provider** | Multi-Bookmaker Baseline | Verified quotes (Bet365, Pinnacle, Unibet) | **Active & Verified** | Realistically priced quotes across 1X2, Totals, DC, BTTS, Player props. |
| **The Odds API** | Live Aggregated Odds | `/sports/{sport}/odds` | **Implemented** | Active API key supported. Normalises decimal odds and margins. |

### 1.3 Web Intelligence & Grounding Providers
| Provider | Role | Integration | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Groq Browser Search** | Real-Time News & Citations | Built-in `browser_search` (`openai/gpt-oss-120b`) | **Active & Verified** | Live web search executed on Groq infrastructure. Automatic citations extraction and source hierarchy classification. |
| **Source Classifier** | Evidentiary Quality Audit | Local approved-source registry | **Active & Verified** | Post-search validation into Tier 1 (Official), Tier 2 (Licensed Data), Tier 3 (Established Publications), and Tier 4/5 (Secondary/Community). |

---

## 2. Adapter Pattern
All providers implement typed abstract base classes:
- `BaseFootballDataProvider` in `app/data/providers/base.py`
- `BaseOddsProvider` in `app/odds/providers/base.py`

This ensures that adding new providers (e.g. Opta, Sportmonks, Betfair Exchange) requires zero modifications to the prediction or parlay engines.
