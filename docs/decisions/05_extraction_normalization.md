# Decision 05: Extraction and normalization

## Purpose

This phase converts one raw provider response into normalized operational records.
It does not replace the original advertisement text.

## Processing flow

    raw response
      -> source adapter
      -> ParsedJobPosting
      -> validation
      -> job_posting upsert
      -> canonical assignment
      -> ranking refresh

The source adapter knows the provider response shape. Shared HTTP, validation,
normalization, storage and database behavior stays in common modules.

## Job posting identity

One operational job_posting represents one provider posting from one board.
Its identity is:

    (source_id, source_job_id)

Repeated downloads update that row. They do not create another posting. A posting
from a different board is a separate row, even when it is later linked to the
same canonical job.

job_posting contains normalized values for querying and the complete original
advertisement for inspection. The original text is not destructively cleaned and
detected aliases are not stored as raw matches.

## Normalization

Aliases map provider values to project values, for example:

    React.js, ReactJS -> React
    work from home, remote -> remote

Unknown or absent values remain NULL where the schema allows it. Validation
rejects invalid records or fields before database insertion according to the
configured limits.

content_fingerprint is calculated from the normalized advertisement text.
Its exact algorithm and matching rules are defined in
09_cross_source_canonical_jobs.md.

## Canonical assignment

Canonical assignment happens during the database write, in the same transaction
as the posting upsert:

1. Upsert the posting by (source_id, source_job_id).
2. Preserve an existing canonical link.
3. For a new link, search candidates only for the same company.
4. Prefer one exact content-fingerprint match.
5. Otherwise use the company, role, locations and compatible known seniority.
6. Link one unambiguous candidate with algorithmic_match.
7. If there is no candidate or there are equally strong candidates, create a
   new_canonical_job.
8. Recalculate posting ranks for the affected canonical job.

The current implementation uses only new_canonical_job and algorithmic_match.
LLM and manual matching are reserved for later.

Canonical matching is an operational loading concern, not a dbt transformation.
dbt reads the resulting canonical links and builds the analytical layer.
