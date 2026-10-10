# Decision 04: Raw storage

## Purpose

Raw storage preserves the provider response before parsing or normalization.
It is the reproducible input for later processing and debugging.

## Layout

Each board and run has its own directory:

    data/01_bronze/<source_key>/<date>/<run_id>/
      response.json
      metadata.json

The run_id is explicit and unique. A repeated download is a new run and does
not overwrite an earlier response, even when the payload is identical.

## Metadata

metadata.json contains at least:

- run_id
- source key
- download timestamp
- HTTP method and URL
- request parameters
- payload SHA-256
- payload size
- record count

Secrets and authorization headers are never stored in raw metadata.

## Processing boundary

Raw storage does not:

- remove or rewrite fields
- normalize aliases
- deduplicate postings
- assign postings to canonical jobs

A changed provider response format is handled by a source adapter. The original
response remains available, so the adapter can be fixed and the run reprocessed.

The provider's public job identifier is read during parsing and is not generated
by raw storage.
