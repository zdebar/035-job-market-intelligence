# IT Job Market Intelligence Platform — plán postupu

# 1. Project settings

## 1.4 Navrhnout adresářovou strukturu

- [ ] Vytvořit `src/` strukturu pro vlastní Python kód.
- [ ] Vytvořit `tests/unit/`.
- [ ] Vytvořit `tests/integration/`.
- [ ] Vytvořit `tests/fixtures/`.
- [ ] Vytvořit `db/migrations/`.
- [ ] Vytvořit `sql/reports/`.
- [ ] Vytvořit `.github/workflows/`.

## 1.5 Nastavit konfiguraci

- [ ] Přidat `.env.example` s názvy potřebných proměnných.
- [ ] Přidat skutečný `.env` do `.gitignore`.
- [ ] Nedávat hesla, tokeny ani connection stringy do zdrojového kódu.
- [ ] Rozlišit lokální, testovací a budoucí cloudové nastavení.

## 1.6 Přidat základní nástroje kvality

- [ ] Přidat formatter/linter.
- [ ] Nastavit minimální pravidla pro Python kód.
- [ ] Přidat pytest.
- [ ] Přidat základní příkaz, kterým lze spustit všechny lokální kontroly.

## 1.7 Přidat základní dokumentaci

- [ ] Napsat README: účel, lokální instalace, spuštění, testy.
- [ ] Popsat, co znamenají Bronze, Silver a Gold vrstvy.
- [ ] Popsat způsob práce s branchemi a commity.
- [ ] Přidat sekci „Jak projekt spustit na čistém počítači“.

## 1.8 Výstup fáze

- [ ] Nový počítač dokáže projekt připravit podle README.
- [ ] Změna v Pythonu se projeví bez ručního nastavování prostředí.
- [ ] Žádná tajná hodnota není v Git historii.
- [ ] Projekt lze commitnout a poslat na GitHub.

---

# 2. Database foundation

## 2.1 Spustit lokální PostgreSQL

- [ ] Přidat `compose.yaml` pouze s PostgreSQL službou.
- [ ] Nastavit persistentní volume.
- [ ] Nastavit healthcheck.
- [ ] Nastavit databázi, uživatele a heslo přes lokální konfiguraci.
- [ ] Ověřit, že databáze funguje po restartu Dockeru.

Docker zde není produkční platforma. Je to opakovatelný lokální způsob, jak spustit stejnou databázi bez ruční instalace.

## 2.2 Zavést SQL migrace

- [ ] Vytvořit tabulku `schema_migrations`.
- [ ] Přidat první číslovanou migraci.
- [ ] Přidat příkaz `migrate`.
- [ ] Zajistit, že již použitá migrace se nespustí znovu.
- [ ] Nikdy neupravovat migraci, která už byla použita.
- [ ] Každou změnu databáze řešit novou migrací.

## 2.3 Navrhnout tabulku běhů ingestionu

První tabulka může evidovat:

- identifikátor běhu,
- zdroj,
- čas začátku a konce,
- počet stažených záznamů,
- počet nových záznamů,
- počet aktualizovaných záznamů,
- stav běhu,
- chybovou zprávu.

## 2.4 Navrhnout minimální tabulku pracovních nabídek

První verze může obsahovat:

- interní ID,
- název zdroje,
- ID nabídky ve zdroji,
- URL,
- název pozice,
- společnost,
- původní lokaci,
- remote flag nebo typ práce,
- původní datum zveřejnění,
- čas posledního stažení.

Zatím není nutné navrhovat kompletní star-schema s mnoha dimenzemi.

## 2.5 Výstup fáze

- [ ] PostgreSQL lze spustit jedním příkazem.
- [ ] Migrace vytvoří databázi z prázdného stavu.
- [ ] Databáze se dá znovu vytvořit bez ručního klikání.
- [ ] Schéma je verzované v GitHubu.

---

# 3. Basic ingestion

## 3.1 Vytvořit adapter pro první zdroj

- [ ] Oddělit HTTP komunikaci od zbytku aplikace.
- [ ] Definovat jednotný interní formát nabídky.
- [ ] Přidat konfiguraci URL zdroje.
- [ ] Stáhnout jednu stránku výsledků.
- [ ] Vypsat počet přijatých záznamů.

Zdrojový adapter nesmí obsahovat SQL logiku. Jeho úkolem je pouze získat data a převést odpověď na interní strukturu.

## 3.2 Přidat spolehlivé HTTP chování

- [ ] Nastavit timeout.
- [ ] Přidat kontrolu HTTP chyb.
- [ ] Přidat omezený počet retry pokusů.
- [ ] Přidat čekání mezi retry.
- [ ] Respektovat rate limit zdroje.
- [ ] Logovat URL, stránku a výsledek bez citlivých údajů.

## 3.3 Přidat stránkování

- [ ] Zpracovat první stránku.
- [ ] Zpracovat další stránku podle odpovědi zdroje.
- [ ] Nastavit maximální počet stránek pro jeden běh.
- [ ] Správně skončit na poslední stránce.
- [ ] Zabránit nekonečnému stránkování.

## 3.4 Přidat idempotentní ingestion

- [ ] Používat stabilní ID nabídky ze zdroje.
- [ ] Nepřidávat stejný inzerát při opakovaném běhu dvakrát.
- [ ] Rozlišit nový záznam a aktualizaci existujícího záznamu.
- [ ] Ukládat čas stažení odděleně od času zveřejnění.

## 3.5 Výstup fáze

- [ ] Příkaz stáhne data z jednoho zdroje.
- [ ] Příkaz umí pracovat s více stránkami.
- [ ] Selhání API je čitelné a kontrolované.
- [ ] Opakovaný běh nezpůsobuje nekontrolované duplikáty.

---

# 4. Raw storage / Bronze layer

## 4.1 Zachovat původní payload

- [ ] Uložit celý JSON payload každého běhu.
- [ ] Přidat identifikátor běhu a číslo stránky.
- [ ] Zachovat čas stažení.
- [ ] Zachovat zdrojovou URL.
- [ ] Uložit payload před normalizací.

V lokální fázi může být Bronze vrstva tvořena JSON soubory a/nebo JSONB sloupcem v PostgreSQL. Důležité je, aby původní data nebyla přepsána normalizovanou verzí.

## 4.2 Navrhnout reprocessing

- [ ] Umět spustit normalizaci nad již uloženým payloadem.
- [ ] Nevolat API znovu, pokud se pouze mění normalizační pravidlo.
- [ ] Evidovat verzi nebo čas normalizační logiky.
- [ ] Oddělit stažení dat od transformace dat.

## 4.3 Rozhodnout, kdy přidat Parquet

- [ ] Začít s JSON, protože je přímo podobný API odpovědi.
- [ ] Přidat Parquet až při potřebě efektivnějšího analytického zpracování.
- [ ] Nepřidávat Delta Lake jen kvůli názvu Bronze layer.

## 4.4 Výstup fáze

- [ ] Každý běh je dohledatelný.
- [ ] Původní payload lze znovu načíst.
- [ ] Změna normalizace nevyžaduje nové stažení dat.

---

# 5. Cleaning / Normalization / Silver layer

## 5.1 Normalizovat základní hodnoty

- [ ] Odstranit přebytečné mezery.
- [ ] Normalizovat prázdné hodnoty na `NULL`.
- [ ] Normalizovat názvy společností.
- [ ] Zachovat původní hodnotu tam, kde může být užitečná pro kontrolu.

## 5.2 Normalizovat lokace

- [ ] Oddělit město od původního textu lokace.
- [ ] Sjednotit Praha / Prague / Praha, Czech Republic.
- [ ] Sjednotit München / Munich.
- [ ] Přidat zemi pouze tehdy, pokud je inference dostatečně spolehlivá.
- [ ] Neznámou zemi raději ponechat jako `NULL` než ji hádat.

## 5.3 Normalizovat pracovní režim

- [ ] Rozlišit remote.
- [ ] Rozlišit hybrid.
- [ ] Rozlišit onsite.
- [ ] Rozlišit neuvedený režim.
- [ ] Zachovat původní hodnotu pro pozdější kontrolu.

## 5.4 Normalizovat typ pozice

- [ ] Pracovní poměr.
- [ ] IČO / contract, pokud je ze zdroje rozpoznatelný.
- [ ] Internship.
- [ ] Working student.
- [ ] Ostatní nebo neznámý typ.

## 5.5 Přidat deterministickou extrakci dovedností

- [ ] Vytvořit první slovník aliasů.
- [ ] Sjednotit například `React`, `React.js`, `ReactJS`.
- [ ] Sjednotit například `Node`, `Node.js`, `NodeJS`.
- [ ] Rozlišit skutečné zmínky od náhodných částí slov.
- [ ] Ukládat původní text i normalizované dovednosti.

Zatím nepoužívat LLM. První verze má ukázat, co lze spolehlivě zvládnout běžným kódem.

## 5.6 Detekovat duplicity

- [ ] Duplicita podle ID zdroje.
- [ ] Duplicita podle URL.
- [ ] Připravit fingerprint z názvu, společnosti, lokace a popisu.
- [ ] Rozlišit stejnou nabídku z různých zdrojů.
- [ ] Ukládat důvod označení záznamu jako duplicity.

## 5.7 Výstup fáze

- [ ] Existuje stabilní Silver tabulka.
- [ ] Normalizace je opakovatelná.
- [ ] Lze vysvětlit, jak vznikla každá odvozená hodnota.
- [ ] Duplicity nejsou pouze ručně mazány.

---

# 6. SQL analytics

## 6.1 Vytvořit první reporty

- [ ] Počet nabídek podle role.
- [ ] Počet nabídek podle lokality.
- [ ] Počet nabídek podle země.
- [ ] Podíl remote / hybrid / onsite.
- [ ] Nejčastější dovednosti.
- [ ] Počet nabídek podle typu pracovního vztahu.

## 6.2 Přidat časový pohled

- [ ] Počet nových nabídek za den.
- [ ] Vývoj za posledních 30 dní.
- [ ] Vývoj za posledních 90 dní.
- [ ] Odlišit datum zveřejnění od data stažení.

## 6.3 Přidat čitelný výstup

- [ ] CLI report v tabulce nebo CSV.
- [ ] Parametry pro zemi, roli a časové období.
- [ ] Stabilní SQL dotazy uložené v repozitáři.
- [ ] Ukázkové výsledky v README.

## 6.4 Výstup fáze

- [ ] Systém odpovídá na první analytické otázky.
- [ ] Reporty lze opakovaně spustit.
- [ ] Každý report má jasně popsanou definici metriky.

---

# 7. Data quality

## 7.1 Základní validační pravidla

- [ ] ID nabídky není `NULL`.
- [ ] ID nabídky je unikátní v rámci zdroje.
- [ ] Název pozice není prázdný.
- [ ] Zdrojová URL má platný formát.
- [ ] Datum není v nesmyslném rozsahu.
- [ ] Země používá platný ISO kód, pokud je vyplněná.

## 7.2 Kontroly běhu ingestionu

- [ ] Běh skončil v očekávaném stavu.
- [ ] Počet přijatých záznamů není neočekávaně nulový.
- [ ] Počet záznamů dramaticky neklesl bez vysvětlení.
- [ ] API odpověď má očekávané klíče.
- [ ] Neznámá změna schématu API je zaznamenána.

## 7.3 Testy

- [ ] Unit testy pro normalizaci.
- [ ] Unit testy pro stránkování.
- [ ] Testy pro retry a API chyby.
- [ ] Integrační test s PostgreSQL.
- [ ] Test opakovaného ingestionu.
- [ ] Test reprocessingu Bronze dat.

## 7.4 Výstup fáze

- [ ] Chybné nebo podezřelé údaje jsou odhaleny automaticky.
- [ ] CI spustí testy při Pull Requestu.
- [ ] Selhání testů zabrání sloučení změny do `main`.

---

# 8. Data modelling / Gold layer / dbt

## 8.1 Stabilizovat business pojmy

- [ ] Definovat, co je „job posting“.
- [ ] Definovat, co je „new job“.
- [ ] Definovat, co je „remote job“.
- [ ] Definovat, co je „Data Engineer role“.
- [ ] Definovat, jak se počítá skill demand.

## 8.2 Navrhnout analytický model

Možné pozdější tabulky:

- `fact_jobs`,
- `dim_company`,
- `dim_skill`,
- `dim_location`,
- `dim_date`,
- `job_skills`,
- `job_snapshots`,
- `salary_history`.

Nemusíme je vytvořit všechny najednou. Každá tabulka musí odpovídat konkrétní analytické potřebě.

## 8.3 Přidat dbt

- [ ] Nainstalovat dbt až po stabilizaci Silver vrstvy.
- [ ] Vytvořit staging modely.
- [ ] Vytvořit analytické modely.
- [ ] Přidat dokumentaci sloupců.
- [ ] Přidat dbt tests.
- [ ] Rozlišit source, staging, intermediate a marts.
- [ ] Přidat incremental model až tehdy, když bude mít smysl.

## 8.4 Výstup fáze

- [ ] Business metriky jsou definované.
- [ ] Gold vrstva je oddělená od raw a Silver vrstvy.
- [ ] dbt modely lze spustit od začátku nad čistou databází.

---

# 9. Druhý zdroj dat

## 9.1 Přidat druhý adapter

- [ ] Vybrat druhý zdroj s odlišným formátem.
- [ ] Zachovat stejný interní datový kontrakt.
- [ ] Nemíchat specifika zdroje do obecné normalizace.
- [ ] Přidat testovací fixture pro druhý zdroj.

## 9.2 Sjednotit zdroje

- [ ] Přidat source registry.
- [ ] Evidovat původ každého záznamu.
- [ ] Řešit duplicity napříč zdroji.
- [ ] Porovnat úplnost a kvalitu obou zdrojů.

## 9.3 Výstup fáze

- [ ] Přidání nového zdroje nevyžaduje přepis databázové vrstvy.
- [ ] Reporty fungují nad oběma zdroji.

---

# 10. Orchestration

Airflow nepřidávat pouze proto, že je v seznamu technologií. Nejprve musí existovat pipeline s více závislými kroky, kterou má smysl plánovat.

## 10.1 Připravit pipeline kroky

- [ ] `extract`.
- [ ] `store_raw`.
- [ ] `normalize`.
- [ ] `load_silver`.
- [ ] `run_quality_checks`.
- [ ] `build_gold`.
- [ ] `publish_report`.

## 10.2 Přidat Airflow

- [ ] Spustit Airflow lokálně.
- [ ] Vytvořit první DAG.
- [ ] Nastavit závislosti mezi kroky.
- [ ] Nastavit retry.
- [ ] Nastavit timeout.
- [ ] Přidat logování.
- [ ] Přidat alert při neúspěšném běhu.
- [ ] Zajistit idempotentní opakování úlohy.

## 10.3 Výstup fáze

- [ ] Pipeline lze naplánovat.
- [ ] Selhání jedné úlohy je viditelné.
- [ ] Opakování běhu nevytváří nekontrolované duplicity.

---

# 11. Cloud foundation — Azure

## 11.1 Základy Azure

- [ ] Vytvořit Azure účet/subscription podle dostupnosti.
- [ ] Nastavit resource group.
- [ ] Naučit se Azure Portal pouze jako vizualizační rozhraní.
- [ ] Naučit se Azure CLI pro opakovatelné operace.
- [ ] Nastavit tagging a rozpočtové limity.
- [ ] Rozumět základním nákladům jednotlivých služeb.

## 11.2 Přidat cloudové úložiště

- [ ] Vytvořit Azure Storage Account.
- [ ] Vytvořit Data Lake Storage Gen2 filesystem.
- [ ] Navrhnout složky pro Bronze, Silver a Gold.
- [ ] Nastavit lokální přístup přes bezpečné credentials.
- [ ] Necommitovat secrets do GitHubu.

## 11.3 Přidat CI/CD základ

- [ ] GitHub Actions spouští testy.
- [ ] GitHub Actions vytvoří artefakt nebo image.
- [ ] Oddělit build, test a deploy.
- [ ] Deployovat nejdříve do testovacího prostředí.
- [ ] Přidat manuální schválení pro produkční prostředí.

## 11.4 Výstup fáze

- [ ] Projekt umí pracovat s Azure úložištěm.
- [ ] Je jasné, co běží lokálně a co v Azure.
- [ ] Náklady jsou kontrolovatelné.

---

# 12. Databricks / PySpark / Delta Lake

## 12.1 Důvod pro PySpark

- [ ] Změřit velikost dat a čas lokálního zpracování.
- [ ] Identifikovat transformaci vhodnou pro distribuované zpracování.
- [ ] Popsat, proč běžný Python/SQL už nestačí nebo proč je PySpark relevantní pro portfolio.

PySpark nepřidávat k malému datasetu jen kvůli technologii. Přidáme ho ve chvíli, kdy ukáže skutečný rozdíl nebo má jasnou portfolio hodnotu.

## 12.2 Základní Databricks workflow

- [ ] Vytvořit workspace.
- [ ] Připojit data z Azure Data Lake.
- [ ] Načíst JSON nebo Parquet.
- [ ] Vytvořit PySpark DataFrame.
- [ ] Provést základní transformaci.
- [ ] Uložit výsledek jako Delta table.
- [ ] Spustit SQL dotaz nad Delta table.

## 12.3 Delta a medallion architektura

- [ ] Bronze Delta data.
- [ ] Silver Delta data.
- [ ] Gold analytická data.
- [ ] Přidat schema evolution jen s jasným důvodem.
- [ ] Porovnat lokální PostgreSQL řešení s cloudovým řešením.

## 12.4 Výstup fáze

- [ ] Umět vysvětlit, proč je použitý Databricks.
- [ ] Umět vysvětlit rozdíl mezi SQL, Pythonem a PySparkem.
- [ ] Umět popsat cestu dat od API až po Delta table.

---

# 13. Dashboard / Analytics presentation

## 13.1 Připravit stabilní analytické rozhraní

- [ ] Vybrat sadu metrik.
- [ ] Definovat filtry.
- [ ] Připravit views nebo Gold tabulky pro dashboard.
- [ ] Zkontrolovat rychlost dotazů.
- [ ] Zajistit, že dashboard nepřepočítává složité transformace při každém načtení.

## 13.2 Vybrat nástroj

### Power BI

Vhodné pro BI orientovanou prezentaci, datové modelování a portfolio ukázku analytiky.

### React + FastAPI

Vhodné později, pokud bude potřeba vlastní aplikace, filtrování a interaktivní uživatelské rozhraní.

První dashboard by měl zůstat analytický. Neměl by se změnit v další rozsáhlý frontendový projekt.

## 13.3 Minimální dashboard

- [ ] Počet nabídek v čase.
- [ ] Nejžádanější dovednosti.
- [ ] Role podle země.
- [ ] Remote share.
- [ ] Filtr data, země, role a skillu.

## 13.4 Portfolio checkpoint

Po této fázi je vhodný čas začít aktivně reagovat na Data Engineer pozice, pokud projekt současně prokazuje:

- Python ingestion,
- API práci,
- PostgreSQL a SQL,
- čištění dat,
- deduplikaci,
- základní modelování,
- dbt nebo ekvivalentní transformační vrstvu,
- jednoduchý dashboard.

---

# 14. AI extraction

## 14.1 Definovat strukturovaný výstup

- [ ] Normalizovaná role.
- [ ] Seniorita.
- [ ] Požadované roky zkušeností.
- [ ] Povinné dovednosti.
- [ ] Volitelné dovednosti.
- [ ] Cloud platforma.
- [ ] Databázové technologie.
- [ ] Jazykové požadavky.
- [ ] Remote/hybrid/onsite.
- [ ] Typ kontraktu.

## 14.2 Přidat LLM extraction

- [ ] Vybrat model/API.
- [ ] Připravit prompt.
- [ ] Použít JSON schema nebo structured output.
- [ ] Validovat výsledek mimo LLM.
- [ ] Ukládat původní text, prompt verzi a výsledek.
- [ ] Evidovat chyby a nejednoznačné výsledky.
- [ ] Přidat retry s limitem.

## 14.3 Vyhodnotit kvalitu

- [ ] Vytvořit ručně zkontrolovaný vzorek.
- [ ] Porovnat LLM výstup s očekávaným výsledkem.
- [ ] Měřit přesnost jednotlivých polí.
- [ ] Porovnat LLM extraction s deterministickou extrakcí.
- [ ] Rozhodnout, která pole jsou dostatečně spolehlivá pro analytiku.

## 14.4 Výstup fáze

- [ ] Unstructured job description se převádí na validovaný JSON.
- [ ] Neplatný výstup se nedostane nekontrolovaně do Gold vrstvy.
- [ ] Lze vysvětlit cenu, rychlost a kvalitu AI extrakce.

---

# 15. Embeddings / vector search

## 15.1 Připravit text pro embedding

- [ ] Vybrat, zda embedovat celý popis nebo normalizovaný souhrn.
- [ ] Odstranit duplicitní nebo technický šum.
- [ ] Evidovat verzi embedding modelu.
- [ ] Evidovat datum generování embeddingu.

## 15.2 Vybrat první vector store

Možnosti k pozdějšímu porovnání:

- pgvector v PostgreSQL,
- Azure AI Search,
- Databricks Vector Search.

Začít jednodušší variantou a cloudovou variantu přidat až při potřebě.

## 15.3 Ověřit základní podobnost

- [ ] Vygenerovat embedding pro několik nabídek.
- [ ] Vygenerovat embedding pro testovací dotaz.
- [ ] Spočítat podobnost.
- [ ] Ručně zkontrolovat výsledky.
- [ ] Změřit latenci a cenu.

---

# 16. Semantic search

## 16.1 Základní vyhledávání

- [ ] Uživatel zadá textový dotaz.
- [ ] Dotaz se převede na embedding.
- [ ] Vyhledají se nejbližší nabídky.
- [ ] Výsledky se zobrazí včetně důvodu relevance.

## 16.2 Přidat klasické filtry

- [ ] Země.
- [ ] Město.
- [ ] Remote režim.
- [ ] Seniorita.
- [ ] Role.
- [ ] Skill.
- [ ] Typ kontraktu.
- [ ] Časové období.

Semantic search nemá nahrazovat všechny běžné SQL filtry. Má je doplňovat.

---

# 17. Hybrid search / relevance ranking

## 17.1 Definovat relevance skóre

Možné složky:

- sémantická podobnost,
- překryv dovedností,
- seniority fit,
- remote preference,
- země/lokalita,
- typ pracovního vztahu.

## 17.2 Přidat transparentní ranking

- [ ] Každá složka skóre má definici.
- [ ] Váhy jsou konfigurovatelné.
- [ ] Uživatel může vidět, proč nabídka skončila vysoko.
- [ ] Ranking je otestovaný na ručně připravených dotazech.
- [ ] Výsledky nejsou označovány jako přesné procento shody bez vysvětlení.

## 17.3 Výstup fáze

```text
dotaz + filtry
→ keyword search
→ semantic search
→ skill/seniority matching
→ ranking
→ vysvětlené výsledky
```

---

# 18. AI assistant / RAG / Tool Calling

## 18.1 Připravit bezpečné datové nástroje

- [ ] Nástroj pro agregace podle role.
- [ ] Nástroj pro agregace podle skillu.
- [ ] Nástroj pro trend v čase.
- [ ] Nástroj pro porovnání zemí.
- [ ] Nástroj pro vyhledání relevantních inzerátů.
- [ ] Omezit povolené SQL operace.
- [ ] Zakázat libovolné destruktivní SQL přes uživatelský dotaz.

## 18.2 Přidat RAG workflow

```text
otázka uživatele
→ rozpoznání záměru
→ volba nástroje
→ SQL / vector retrieval
→ výsledná data
→ syntéza odpovědi
→ uvedení zdroje a omezení
```

## 18.3 Přidat evaluaci

- [ ] Vytvořit sadu referenčních otázek.
- [ ] Kontrolovat správnost použitých dat.
- [ ] Kontrolovat, zda odpověď neobsahuje nepodložené závěry.
- [ ] Kontrolovat správnost SQL dotazu.
- [ ] Logovat latenci, cenu a chyby.
- [ ] Přidat observability pro AI kroky.

## 18.4 Výstup fáze

- [ ] Asistent odpovídá nad skutečnými projektovými daty.
- [ ] Odpověď není založena pouze na obecných znalostech modelu.
- [ ] Uživatel vidí, z jakých dat závěr vychází.

---

# 19. Production hardening

## 19.1 Provozní připravenost

- [ ] Centralizované logování.
- [ ] Monitoring běhů pipeline.
- [ ] Alerting.
- [ ] Retry a dead-letter strategie.
- [ ] Backup databáze.
- [ ] Obnova ze zálohy.
- [ ] Dokumentace incidentu.

## 19.2 Bezpečnost

- [ ] Secrets mimo Git.
- [ ] Minimální oprávnění služeb.
- [ ] Oddělení vývoje, testu a produkce.
- [ ] Rotace secrets.
- [ ] Audit přístupů.
- [ ] Ověření licencí a podmínek zdrojů dat.

## 19.3 Náklady

- [ ] Rozpočet Azure.
- [ ] Limity cloudových služeb.
- [ ] Náklady LLM extraction.
- [ ] Náklady embeddingů.
- [ ] Náklady Databricks clusterů.
- [ ] Rozhodnutí, co se má vypínat mimo pracovní dobu.
