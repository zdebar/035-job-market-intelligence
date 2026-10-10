# Decision 09: Cross-source canonical jobs

## Identity and upsert

`job_postings` represents one posting from one source board.

The same source posting is identified by:

```text
(source_id, source_job_id)
```

Repeated downloads update the existing posting. A posting from another board
is stored separately and can be linked to the same `canonical_job`.

Existing canonical links are preserved. A later download does not automatically
move an already linked posting to another canonical job.

## Fingerprint

`content_fingerprint` is a SHA-256 hash of the advertisement description after:

1. HTML removal,
2. HTML entity decoding,
3. whitespace normalization,
4. trimming,
5. case folding.

The fingerprint does not include the source, source job ID, URL, or title. It is
used only as one signal for cross-source matching.

## Matching

For a new posting, candidates are searched only for the same company.

1. One matching content fingerprint means `algorithmic_match`.
2. Otherwise, one candidate with the same company, role, locations, and
   compatible known seniority means `algorithmic_match`.
3. No candidate means `new_canonical_job`.
4. Multiple equally strong candidates also create `new_canonical_job`.

Only `new_canonical_job` and `algorithmic_match` are currently used. LLM and
manual matching remain reserved values.

## Primary posting ranking

`job_posting_sources.selection_rank` stores the current order within one
canonical job.

- active postings receive ranks starting at `1`;
- inactive postings receive `NULL`;
- rank `1` is the primary posting;
- source priority is not used in this phase;
- ranking uses `source_updated_at DESC NULLS LAST`, falling back to
  `retrieved_at`;
- equal values use a simple completeness score;
- remaining ties use `job_posting_id ASC` for stability.

The completeness score gives one point for each available normalized element:

- role,
- seniority,
- source URL,
- at least one location,
- at least one work mode,
- at least one skill,
- salary,
- employment option.

The values of a canonical job are read from its primary posting. Values from
secondary postings are not silently merged or used as fallback values.

## Recalculation

Ranking is recalculated for every affected canonical job after a posting is
inserted, updated, or made inactive. Unaffected canonical jobs are not
recalculated.

If a canonical job has no active postings, all its posting links remain stored,
but no link has a rank and the analytical canonical record has no current
primary posting.

## Collision tests

The test suite must cover two postings from different boards belonging to the
same company:

- identical normalized descriptions match one canonical job;
- repeated download updates one posting instead of creating another;
- an inactive posting gets no rank;
- active postings get deterministic ranks;
- updating one posting recalculates only its canonical job;
- a canonical job without active postings has no primary posting.
