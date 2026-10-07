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
