I am continuing from a previous long ChatGPT thread that cannot be moved into this project. Treat the following as established context and decisions. Do not restart the career discussion from zero unless new information materially changes the recommendation.

## Career goal

My target is:

- reach roughly 160,000 CZK/month invoiced on IČO as fast as reasonably possible
- ideally work partially remote
- long-term goal is NOT to keep increasing income, but to maintain roughly that income while reducing working hours
- therefore optimize for contract rate, specialization, and future part-time/freelance flexibility rather than traditional management progression

I am based in Czechia and may later target Germany/DACH as well.

I have strong logical/technical ability and learn IT topics quickly.

I already know web development reasonably well, including:

- React
- TypeScript
- Node.js
- PostgreSQL
- REST APIs
- Git/GitHub
- basic Docker/web development concepts

Because of this, Full Stack can be used as the fastest route into commercial IT work if necessary, but the main long-term specialization should be Data Engineering → Data/AI Engineering.

## Career strategy already decided

Do not recommend switching to unrelated areas unless there is a very strong reason.

Current strategy:

1. Apply for Full Stack IČO work if this can generate commercial IT experience quickly.
2. In parallel, build real Data Engineering skills.
3. Transition into Data Engineer roles as soon as the portfolio/project is credible.
4. Prefer Data Engineer jobs at companies that also have AI/ML/LLM teams or projects.
5. Gradually move from Data Engineer → Data/AI Engineer → AI Engineer / specialist contractor.
6. Long-term specialization should enable high day rates and fewer working days per month.

Target technical direction:

- Python
- SQL
- PostgreSQL
- ETL/ELT
- data modelling
- dbt
- Airflow
- Azure
- Databricks
- PySpark
- Docker
- Git / CI/CD
- later FastAPI
- LLM APIs
- structured outputs
- embeddings
- vector search
- semantic search
- RAG
- tool calling / agents
- AI evaluation
- possibly Terraform / MLOps / LLMOps later

For the cloud/data stack, prioritize Azure + Databricks rather than learning AWS, GCP, Snowflake and Azure simultaneously.

## Main learning principle

I do NOT want to spend months doing isolated tutorials.

I want one substantial project that begins extremely simply and progressively becomes more professional and complex.

Each new technology should be added because the project creates a real reason to need it.

The project should simultaneously serve as:

- a learning vehicle
- a portfolio project
- something I can explain in interviews
- something useful enough that I may actually use it myself

## Main project

Project concept:

# IT Job Market Intelligence Platform

The platform should collect, normalize, analyse and later semantically search IT job postings, especially in Czechia and Germany.

The system should eventually answer questions like:

- how many Data Engineer vs Full Stack vs DevOps vs AI Engineer jobs exist
- what skills are most requested
- which skills commonly occur together
- junior vs medior vs senior demand
- remote / hybrid / onsite share
- IČO / contract vs employment
- salary/rate ranges
- Czechia vs Germany
- technology demand trends over 30 / 90 / 365 days
- which skills are rising or falling
- which jobs are the best fit for a specific candidate profile

## Planned project evolution

The project should evolve approximately through these stages.

### Phase 1 — Basic ingestion

Start with one job source only.

Flow:

job source
→ Python ingestion
→ PostgreSQL
→ SQL
→ simple output/dashboard

Technologies/concepts:

- Python
- requests or httpx
- REST APIs / feeds
- JSON
- pagination
- rate limits
- retries
- PostgreSQL
- SQL
- Git

Goal:
Get a working end-to-end pipeline quickly.

### Phase 2 — Raw storage / bronze layer

Do not immediately overwrite source data.

Store the original source payload.

Possible technologies:

- Azure Data Lake later
- JSON / Parquet
- Delta Lake later

Concept:

source
→ raw/bronze layer
→ processing

Goal:
Preserve original data so the pipeline can be reprocessed later.

### Phase 3 — Cleaning / normalization / silver layer

Solve realistic data problems:

- duplicates
- malformed values
- NULL handling
- inconsistent locations
- salary normalization
- currency normalization
- canonical skill names
- company normalization
- duplicate postings across multiple portals
- schema validation

Example:

ReactJS
React.js
React

→ React

Prague
Praha
Prague, Czech Republic

→ canonical location representation

Technologies/concepts:

- Python
- SQL
- later PySpark / Databricks
- validation
- normalization
- canonicalization
- deduplication
- incremental processing

### Phase 4 — Data modelling / dbt

Create a proper analytics model.

Possible tables:

- fact_jobs
- dim_company
- dim_skill
- dim_location
- dim_date
- job_skills
- salary_history
- job_snapshots

Analytics tables/views:

- daily_skill_demand
- salary_by_role
- salary_by_skill
- remote_share_by_role
- junior_jobs_by_skill
- contract_jobs_by_country
- technology_trends

Use:

- dbt
- SQL
- data modelling
- dimensional modelling
- fact/dimension concepts
- incremental models
- dbt tests

This is the gold/analytics layer.

### Phase 5 — Data quality

Add automatic checks such as:

- job_id must be unique
- salary cannot be negative
- country cannot be NULL
- dates must be valid
- foreign keys must be consistent
- row count should not unexpectedly collapse
- schema should remain valid
- critical fields should meet expected completeness

Technologies/concepts:

- dbt tests
- schema validation
- data quality
- monitoring
- possibly Great Expectations later

### Phase 6 — Orchestration

Automate pipeline execution.

Example:

06:00 ingest source A
06:10 ingest source B
06:20 validate
06:30 transform
06:40 run dbt
06:50 run data quality tests
07:00 refresh analytics

Use:

- Airflow
- DAGs
- scheduling
- dependencies
- retries
- logging
- alerts
- monitoring

### Phase 7 — Azure + Databricks

Move from a local/small setup toward a realistic cloud architecture.

Possible architecture:

job sources
→ Python ingestion
→ Azure Data Lake
→ Databricks
→ PySpark / SQL
→ Delta Lake
→ dbt
→ analytics layer

Technologies:

- Azure
- Azure Data Lake Storage
- Azure Databricks
- Databricks
- Delta Lake
- PySpark
- Databricks SQL
- possibly Azure Key Vault
- CI/CD later

Important:
Do not introduce PySpark merely for a tiny dataset. Use it when the project is ready to demonstrate distributed-data concepts and when it improves employability/portfolio value.

### Phase 8 — Dashboard / application layer

Provide standard analysis and filtering.

Possible filters:

- country
- role
- seniority
- salary
- remote/hybrid/onsite
- skill
- contract type
- company
- date range

Options:

- Power BI for BI-oriented presentation
  or
- React + TypeScript + FastAPI for a custom application

Because I already know React/TypeScript, a custom frontend may be useful, but the project should remain primarily a Data/AI Engineering portfolio project rather than becoming another frontend project.

### Phase 9 — AI extraction

Use an LLM to convert unstructured job descriptions into structured data.

Example input:

"We are looking for a senior Data Engineer with 5+ years of Python, SQL, Azure and Databricks experience."

Expected structured output:

{
"role": "Data Engineer",
"seniority": "Senior",
"years_experience": 5,
"skills": ["Python", "SQL", "Azure", "Databricks"]
}

Potential extracted fields:

- normalized role
- seniority
- required years of experience
- required skills
- optional skills
- cloud platform
- database technologies
- contract type
- language requirements
- remote/hybrid/onsite
- management responsibility
- domain/industry

Technologies/concepts:

- LLM API
- structured outputs
- JSON schema
- prompt engineering
- information extraction
- classification
- validation of LLM outputs

This should be treated as a realistic enterprise AI use case:
unstructured text → structured data.

### Phase 10 — Embeddings and vector search

Generate embeddings for job descriptions and/or normalized job summaries.

Concept:

job text
→ embedding model
→ vector
→ vector store

Possible technologies:

- pgvector
- Databricks Vector Search
- Azure AI Search
- embeddings API

Relevant concepts:

- vector embeddings
- cosine similarity
- nearest-neighbor search
- vector indexing

### Phase 11 — Semantic search

Allow searches by meaning rather than only keywords.

Example query:

"Find remote data jobs suitable for a web developer moving into Python and SQL."

The system should retrieve semantically relevant jobs even if the exact words do not occur in the posting.

Concept:

query
→ embedding
→ vector similarity search
→ relevant jobs

### Phase 12 — Hybrid search and relevance ranking

Combine:

- traditional filters
- keyword search
- semantic/vector search
- candidate skill match
- seniority fit
- remote preference
- country/location preference
- contract preference

Potential relevance model:

semantic similarity

- skill overlap
- seniority match
- remote preference
- contract preference
- location

Output:

Job A — 92% fit
Job B — 87% fit
Job C — 81% fit

Relevant concepts:

- relevance scoring
- ranking
- recommendation systems
- hybrid search
- reranking

### Phase 13 — AI assistant / RAG / tool calling

Later, allow the user to ask questions such as:

"Should I learn Databricks or Snowflake for the Czech and German market?"

The AI should not answer from generic model knowledge alone.

It should use actual platform data via tools/queries.

Possible architecture:

user question
→ LLM
→ SQL/data query tool
→ job-market data
→ reasoning/synthesis
→ grounded answer

Relevant concepts:

- RAG
- tool calling
- agents
- retrieval
- grounded generation
- AI evaluation
- LLM observability

## Medallion architecture terminology

Use these terms where appropriate:

Bronze:
raw/original source data

Silver:
cleaned, normalized, deduplicated data

Gold:
analytics-ready/business-level data

This is the Medallion Architecture pattern.

## Job-search timing

Do NOT recommend waiting until the whole project is complete.

Start applying for Data Engineer roles once I can credibly demonstrate:

- Python ingestion
- API/data acquisition
- PostgreSQL/SQL
- cleaning/validation
- deduplication
- dbt transformations
- basic analytics/dashboard

Apply more aggressively once the project also contains:

- Azure
- Databricks
- PySpark
- Airflow

Prioritize companies where:

- Data Engineering and AI/ML/LLM coexist
- Data Engineers work with AI/Data Science teams
- Python and SQL are important
- Azure/Databricks are used
- modern cloud/data stack is used
- there is room to move toward Data/AI Engineering internally
- IČO/contract and remote/hybrid work are possible

Avoid optimizing only for the first salary.

For the first Data Engineer role, stack quality and exposure to production systems / AI teams may be more valuable than an extra 10–20k CZK.

## Long-term financial strategy

The eventual goal is not:

160k → 200k → 250k while still working full time.

The desired trajectory is more like:

160k / 20 working days
→ 160k / 15 days
→ 160k / 12 days
→ possibly 160k / 10 days

This requires specialization and high day rates.

Potential eventual niches:

- Databricks specialist
- Azure/Fabric data platform specialist
- Data + enterprise AI integration
- Databricks + GenAI/RAG
- AI/data platform engineering

Germany/DACH may later be a strong market, especially if I improve German.

## How to work with me

Be pragmatic and implementation-focused.

Do not overcomplicate early stages.

Do not recommend learning every technology before starting.

Prefer:

overview
→ minimal working system
→ one realistic complication at a time
→ production-grade improvements

When suggesting technologies, explain WHY the project needs them.

If a simpler solution is enough for the current stage, prefer the simpler solution.

When current job-market data, salaries, rates, technologies or hiring demand matter, use recent sources only.

I care more about actual employability and contract-market value than academic completeness.

## Current next step

Continue from here by helping me build Phase 1 of the IT Job Market Intelligence Platform.

Start with the smallest credible version.

The first version should probably be:

one data source
→ Python ingestion
→ PostgreSQL
→ basic normalization
→ SQL queries
→ simple output

Then propose the repository structure, data model, ingestion flow and first implementation steps.

Do not jump directly into Azure/Databricks/Airflow unless there is a concrete reason to introduce them.
