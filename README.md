# PROJECT FOUNDATION

| Oblast           | Doporučení                                   |
| ---------------- | -------------------------------------------- |
| Zdrojový kód     | Git lokálně + GitHub jako vzdálený repozitář |
| Python prostředí | `uv`                                         |
| PostgreSQL       | Docker Compose                               |
| Konfigurace      | `.env` lokálně, `.env.example` v GitHubu     |
| Databázové změny | verzované SQL migrace                        |
| Testy            | pytest                                       |
| Kontrola kvality | Ruff                                         |
| CI               | GitHub Actions                               |
| Transformace     | nejdříve Python/SQL, později dbt             |
| Cloud            | zatím žádný                                  |
