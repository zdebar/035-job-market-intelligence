# Jooble CZ

## Source

- Source ID: `jooble-cz`
- Market: Czech Republic
- Format: JSON
- Access: REST API

## Official documentation

- [Jooble CZ API access](https://cz.jooble.org/api/about)
- [Jooble REST API documentation](https://jooblehelpcenter.freshdesk.com/en/support/solutions/articles/60001448238-rest-api-documentation)

## API

- Endpoint: `https://cz.jooble.org/api/{api_key}`
- Method: `POST`
- Request content type: `application/json`
- Response content type: `application/json`
- Authentication: API key in the endpoint path
- API key environment variable: `JOOBLE_API_KEY`

The API key must never be stored in Git, TOML configuration, logs or raw metadata.

## Request parameters

The shared search criteria are configured in `config/settings.toml`:

```toml
[search]
keywords = ["Data Engineer", "AI Engineer"]
locations = ["Czech Republic"]
```

Jooble-specific request options are configured in
`config/sources/jooble-cz.toml`:

```json
{
  "page": 1,
  "companysearch": false,
  "SearchMode": 0
}
```

`ResultOnPage` is intentionally omitted from the default request. This lets
Jooble apply its own default or maximum page size. For a small test request,
pass `--result-on-page 10`.

## Response fields

The response contains a job collection with fields including:

- `id`
- `title`
- `location`
- `snippet`
- `salary`
- `source`
- `type`
- `link`
- `company`
- `updated`

## API limits

The current Jooble documentation states that the free REST API plan has a
lifetime limit of 500 requests per API key. Verify the current limit before
starting recurring ingestion.

## Raw storage

Each successful response is stored unchanged in:

```text
data/01_bronze/jooble-cz/<UTC-date>/<run-id>/response.json
```

Request and response metadata are stored separately in `metadata.json`.

## Local usage

Preview the request without an API key or network call:

```bash
uv run job-market-download-jooble --dry-run
```

After adding the key to `.env`, download one page:

```bash
uv run job-market-download-jooble
```

Download only ten results for a test:

```bash
uv run job-market-download-jooble --result-on-page 10
```

## General ingestion runner

The enabled acquisition sources are listed in `config/ingestion.toml`.
Run all enabled sources with:

```bash
uv run job-market-ingest
```

Preview all configured requests without network access:

```bash
uv run job-market-ingest --dry-run
```

Run or preview only one configured source:

```bash
uv run job-market-ingest --source jooble-cz --dry-run
```
