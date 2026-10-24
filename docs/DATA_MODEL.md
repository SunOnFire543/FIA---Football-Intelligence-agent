# Database & Storage Schema

## 1. Storage Architecture
- **Local / Development**: Embedded SQLite (`data/football_intel.db`).
- **Production**: PostgreSQL compatible via SQLAlchemy declarative models.
- **Memory Optimization**: Bounded queries, explicit foreign keys, indexes on `(fixture_id, kickoff_time, season)`.

## 2. Table Schemas

### `competitions`
- `id` (VARCHAR(64), PK): e.g. `PL`, `PD`, `CL`
- `name` (VARCHAR(128))
- `country` (VARCHAR(64))
- `division` (INTEGER)
- `is_cup` (BOOLEAN)
- `provider` (VARCHAR(32))

### `teams`
- `id` (VARCHAR(64), PK): e.g. `ARS`, `CHE`, `MCI`
- `name` (VARCHAR(128))
- `short_name` (VARCHAR(32))
- `competition_id` (VARCHAR(64), FK)
- `stadium` (VARCHAR(128))

### `fixtures`
- `id` (VARCHAR(64), PK): e.g. `FIX_ARS_CHE_2026`
- `competition_id` (VARCHAR(64), FK)
- `season` (VARCHAR(16))
- `kickoff_time` (DATETIME, Indexed)
- `home_team_id` (VARCHAR(64), FK)
- `home_team_name` (VARCHAR(128))
- `away_team_id` (VARCHAR(64), FK)
- `away_team_name` (VARCHAR(128))
- `status` (VARCHAR(32))
- `home_score` (INTEGER, Nullable)
- `away_score` (INTEGER, Nullable)

### `bookmaker_odds`
- `id` (INTEGER, PK, Auto-increment)
- `fixture_id` (VARCHAR(64), FK, Indexed)
- `bookmaker` (VARCHAR(64))
- `market` (VARCHAR(64))
- `selection` (VARCHAR(64))
- `threshold` (FLOAT, Nullable)
- `decimal_odds` (FLOAT)
- `observed_at` (DATETIME, Indexed)
- `is_live` (BOOLEAN)

### `evidence_records`
- `record_id` (VARCHAR(64), PK)
- `fixture_id` (VARCHAR(64), FK, Indexed)
- `competition_id` (VARCHAR(64))
- `prediction_timestamp` (DATETIME)
- `data_cutoff_timestamp` (DATETIME)
- `model_version` (VARCHAR(32))
- `payload_json` (TEXT)
- `verification_passed` (BOOLEAN)
