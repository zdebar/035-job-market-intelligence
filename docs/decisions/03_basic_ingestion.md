# Basic Ingestion

## Source strategy

Primary data should come from company career pages and publicly accessible job-board
APIs provided by the ATS platform used by the company.

Job portals and aggregators are secondary sources. Their main purpose is to identify
relevant companies, roles and links to the original company career page.

## Source identity and ingestion unit

A configured source is one public company board, not only the ATS platform.

Examples:

    greenhouse_mews
    lever_ataccama
    ashby_apify

The stable sources.key identifies the board. sources.name is only a readable
label and may change without changing the source identity.

One board download creates one raw ingestion run. For Greenhouse, Lever and Ashby
the request retrieves all currently published postings on that board. Shared
keyword and location settings are not used as filters for these board-level
endpoints.

The source adapter passes the provider's public source_job_id to processing.
The same source posting is therefore recognized across repeated runs by:

    (source_id, source_job_id)

The ingestion phase only downloads and stores the response. Parsing, normalization,
canonical matching and database loading are later processing steps.

## Primary sources — company career systems

| Source | URL | Access | Status |
|---|---|---|---|
| **Greenhouse Job Board API** | [docs.greenhouse.io](https://docs.greenhouse.io/job-board.html) | Public GET API, JSON, full job content | **First implementation** |
| Lever Postings API | [github.com/lever/postings-api](https://github.com/lever/postings-api) | Public job postings, JSON | Later |
| Ashby job board/API | [developers.ashbyhq.com](https://developers.ashbyhq.com/reference/jobpostinglist) | Public job boards; API access depends on endpoint and permissions | Later |
| Company-specific career API | Individual company career site | Public API, JSON, RSS or feed where available | Case by case |

Examples of companies with Czech or Prague technology roles on these systems include
Make, Second Foundation Tech, Capco, Ataccama, Pipedrive, SatoshiLabs/Trezor and
others.

## Secondary sources — Czech job portals and aggregators

These sources are used primarily for discovery and coverage comparison. Each source
must be checked separately for its API, feed, terms and technical restrictions.

| Source | URL | Access |
|---|---|---|
| Jooble CZ | [cz.jooble.org](https://cz.jooble.org/) | REST API, JSON, API key |
| Jobstack.it | [jobstack.it](https://www.jobstack.it/) | Web |
| Jobs.cz | [jobs.cz](https://www.jobs.cz/) | Web |
| Prace.cz | [prace.cz](https://www.prace.cz/) | Web |
| Pracomat.cz | [pracomat.cz](https://www.pracomat.cz/) | Web |
| ITjobs.cz | [itjobs.cz](https://www.itjobs.cz/) | Web, RSS |
| Job-it.cz | [job-it.cz](https://job-it.cz/) | Web |
| StartupJobs.cz | [startupjobs.cz](https://www.startupjobs.cz/nabidky) | API, JSON/XML feed where available |
| No Fluff Jobs CZ | [nofluffjobs.com/cz](https://nofluffjobs.com/cz/) | Web |

## Secondary sources — international

| Source | URL | Access |
|---|---|---|
| Adzuna | [developer.adzuna.com](https://developer.adzuna.com/) | REST API, API key; Czech coverage to be verified |
| LinkedIn Jobs | [cz.linkedin.com/jobs](https://cz.linkedin.com/jobs) | Web |
| Indeed Czech Republic | [cz.indeed.com](https://cz.indeed.com/) | Web |
| Glassdoor | [glassdoor.com](https://www.glassdoor.com/Job/index.htm) | Web |
| Wellfound | [wellfound.com/location/czech-republic](https://wellfound.com/location/czech-republic) | Web |
| EURES | [eures.europa.eu](https://eures.europa.eu/) | Web |
| EuroTechJobs | [eurotechjobs.com](https://eurotechjobs.com/) | Web |

## Initial implementation order

1. Greenhouse Job Board API
2. Lever Postings API
3. Ashby job boards/API
4. Adzuna API
5. Company-specific public APIs or feeds
6. Other secondary portals and aggregators for discovery and comparison
