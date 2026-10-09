# Planning

## Cíl projektu

Automatizovaná Data / AI Platforma pro shromažďování a analýzu pracovních nabídek.

Smyslem projektu je:

1. naučit se Data / AI Engineering
2. prezentovat Data / AI Engineering schopnosti
3. posoudit četnost a lukrativnost jednotlivých požadovaných technologií
4. vybrat a seřadit inzeráty dle vhodnosti

## Technologie

Vybrány dle orientačního průzkumu českého trhu Data / AI Engineeringu.

1. Git, GitHub, GitHub Actions
2. Python, uv, httpx
3. PostgreSQL, Docker, Docker Compose, dbt, Parquet
4. Apache Airflow, Apache Spark / PySpark
5. Microsoft Azure, Azure Data Lake, Azure CLI, Azure Key Vault
6. Databricks, Delta Lake, Databricks SQL
7. Power BI, FastAPI
8. LLM API, embeddings, pgvector / Azure AI Search / Databricks Vector Search
9. Semantic Search, Hybrid Search, RAG, Tool calling, AI evaluation / observability
10. Terraform, MLflow, Kubernetes

## Postup fází projektu

| Fáze | Název                      | Hlavní výsledek                                    |
| ---- | -------------------------- | -------------------------------------------------- |
| 6    | SQL analytics              | První užitečné analytické otázky a reporty         |
| 7    | Data quality               | Automatické kontroly kvality dat                   |
| 8    | Data modelling / Gold      | Stabilní analytický datový model a dbt             |
| 9    | Druhý zdroj dat            | Ověření, že architektura není svázaná s jedním API |
| 10   | Orchestration              | Automatické běhy, retry, logování a monitoring     |
| 11   | Cloud foundation           | Azure a základní cloudové služby                   |
| 12   | Databricks / PySpark       | Distribuované zpracování a Delta Lake              |
| 13   | Dashboard                  | Power BI analytický dashboard                      |
| 14   | AI extraction              | Text pracovního inzerátu → strukturovaná data      |
| 15   | Embeddings / vector search | Uložení významové reprezentace inzerátů            |
| 16   | Semantic search            | Vyhledávání podle významu dotazu                   |
| 17   | Hybrid search / ranking    | Kombinace filtrů, keywordů a relevance             |
| 18   | AI assistant               | RAG, tool calling, odpovědi nad vlastními daty     |
| 19   | Production hardening       | Nasazení, bezpečnost, náklady a provoz             |
