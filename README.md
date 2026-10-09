# Job Market Intelligence

Data engineering project for collecting, transforming and analysing IT job-market data.

## Stack

Python · `uv` · PostgreSQL · Docker · Azure · Databricks · Power BI

## Quick start

```bash
uv sync
cp .env.example .env
uv run job-market-intelligence
```

Run all local checks:

```bash
bash scripts/check.sh
```

## Data sources

Configured:

- Greenhouse Job Board API — public GET API, JSON, full job content

Planned Czech sources:

- Jobstack.it, Jobs.cz, Prace.cz, Pracomat.cz, ITjobs.cz
- Job-it.cz, StartupJobs.cz, No Fluff Jobs CZ

Planned international sources:

- LinkedIn Jobs, Indeed, Glassdoor, Wellfound
- EURES, EuroTechJobs

The detailed source list is in [docs/decisions/03_basic_ingestion.md](docs/decisions/03_basic_ingestion.md).

## Data acquisition

Shared search criteria are configured in `config/settings.toml`.
The enabled sources and their configurations are defined in `config/ingestion.toml`.

Run all enabled sources:

```bash
uv run job-market-ingest
```

Preview requests without network access:

```bash
uv run job-market-ingest --dry-run
```

Run or preview only Greenhouse:

```bash
uv run job-market-ingest --source greenhouse --dry-run
```

Greenhouse uses public board tokens and does not require an API key or password.

## Raw parsing

Apply the next migration to an existing database that already has `001`, `002` and `003`:

```bash
docker compose exec -T postgres \
  sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < db/migrations/004_simplify_compensation.sql
```

Parse all new raw runs into PostgreSQL:

```bash
uv run job-market-parse
```

Preview discovered raw runs without a database connection:

```bash
uv run job-market-parse --dry-run
```

The runner records each processed run in `raw_ingestion_runs` and skips runs
with status `processed`. Failed runs can be retried by running the command again.

Run all SQL data-quality checks:

```bash
uv run job-market-quality
```

## Branch guide

- `main` — stable version
- `feature/<name>` — new functionality
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation changes

Start new work from the latest `main`:

```bash
git switch main
git pull
git switch -c feature/<name>
```

Run checks before committing. Merge completed work into `main` through a pull request.

## Project structure

```text
src/          application code
tests/        automated tests
db/           migrations and seeds
sql/          analytical SQL
docs/         project documentation and decisions
data/         local data layers (ignored by Git)
```

The project is currently in the foundation and setup phase.
