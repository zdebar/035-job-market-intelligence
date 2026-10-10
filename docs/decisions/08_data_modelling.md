# Decision 08: Data Modelling / Gold / dbt

## Scope

dbt vytvori pouze analytickou vrstvu nad existujici PostgreSQL databazi.
Provozni tabulky, ingestion ani extrakce se v teto fazi nemeni.

Vsechny prvni dbt modely budou materializovane jako `view` v schema `analytics`.

## Business grain

| Oblast | Grain | Vyklad |
| --- | --- | --- |
| `job_posting` | jeden radek na jeden inzerat z jednoho boardu | `job_postings.id` |
| `canonical_job` | jeden radek na jednu logickou pracovni prilezitost | pocita se pres `DISTINCT canonical_job_id` |
| skill bridge | jeden radek na jednu vazbu posting-skill | jeden posting muze mit mnoho skills |
| location bridge | jeden radek na jednu vazbu posting-location | jeden posting muze mit mnoho lokaci |
| work mode bridge | jeden radek na jednu vazbu posting-work-mode | jeden posting muze mit vice work modes |
| dimension | jeden radek na jednu referencni entitu | firma, role, source nebo seniority |

`fct_job_postings` nebude obsahovat M:N hodnoty jako JSON pole objektu.
Tyto vztahy budou reprezentovany bridge modely.

Primarni posting canonical jobu se zatim neurcuje.

## Staging models

Staging model je tenka analyticka vrstva nad jednim nebo malo zdroji.
Pouziva se pro premenovani sloupcu, sjednoceni typu a odstraneni technickeho sumu.
Nema obsahovat dashboardove agregace.

| Model | Grain | Zdroj |
| --- | --- | --- |
| `stg_job_postings` | jeden radek na `job_postings.id` | `job_postings` + canonical vazba |
| `stg_job_posting_sources` | jeden radek na jednu vazbu posting-canonical | `job_posting_sources` |
| `stg_job_skill_requirements` | jeden radek na jednu vazbu posting-skill | `job_skill_requirements` |
| `stg_job_posting_locations` | jeden radek na jednu vazbu posting-location | `job_posting_locations` |
| `stg_job_posting_work_modes` | jeden radek na jednu vazbu posting-work-mode | `job_posting_work_modes` |

## Dimensions

| Model | Grain | Obsah |
| --- | --- | --- |
| `dim_company` | jedna firma | `company_id`, `company_name` |
| `dim_role` | jedna canonical role | `role_id`, `role_name` |
| `dim_source` | jeden source board | `source_id`, `source_key`, `source_name` |
| `dim_seniority` | jedna seniority level | `seniority_id`, `seniority_name`, `sort_order` |

Zatim nevytvarime `dim_date`, protoze nepotrebujeme historicke snapshoty ani
slozite casove hierarchie.

## Fact model

### `fct_job_postings`

Grain: jeden radek na jeden zdrojovy inzerat.

Obsahuje pouze skalarni hodnoty, zejmena:

- `job_posting_id`,
- `canonical_job_id`,
- `company_id`, `role_id`, `source_id`, `seniority_id`,
- `status`,
- `source_published_at`, `retrieved_at`, `last_seen_at`,
- URL a salary hodnoty potrebne pro analytiku.

Pocet inzeratu se pocita jako `COUNT(*)`.
Pocet logickych pracovnich prilezitosti se pocita jako
`COUNT(DISTINCT canonical_job_id)`.

Zatim nevytvarime samostatny `fct_canonical_jobs`. Neexistuje primarni posting
ani dalsi stabilni atribut canonical jobu, ktery by takovy model vyzadoval.

## Bridge models

| Model | Grain | Zdroj |
| --- | --- | --- |
| `bridge_job_posting_skills` | jeden posting + jeden skill | `stg_job_skill_requirements` |
| `bridge_job_posting_locations` | jeden posting + jedna location | `stg_job_posting_locations` |
| `bridge_job_posting_work_modes` | jeden posting + jeden work mode | `stg_job_posting_work_modes` |

Bridge model je analyticka podoba existujici spojovaci tabulky. Nemusi byt
nova fyzicka PostgreSQL tabulka; prvni implementace bude dbt `view`.

## Out of scope

- primarni listing canonical jobu,
- historicke salary snapshoty,
- slowly changing dimensions,
- incremental materializace,
- `dim_date`,
- samostatny fact model canonical jobs,
- agregace urcene pouze pro jeden dashboard.

Tyto veci se pridaji az po konkretnim analytickem pozadavku.
