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

- Jooble CZ — REST API, JSON, API key

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

Preview requests without using the network or API keys:

```bash
uv run job-market-ingest --dry-run
```

Run or preview only one source:

```bash
uv run job-market-ingest --source jooble-cz --dry-run
```

Run the Jooble adapter directly:

```bash
uv run job-market-download-jooble --dry-run
```

For a small test request, limit the result count:

```bash
uv run job-market-download-jooble --dry-run --result-on-page 10
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
