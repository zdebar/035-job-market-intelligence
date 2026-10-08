BEGIN;

INSERT INTO sources (name)
VALUES ('Greenhouse')
ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name)
VALUES
    ('Data Engineer'),
    ('AI Engineer'),
    ('Machine Learning Engineer'),
    ('MLOps Engineer'),
    ('Data Scientist'),
    ('Analytics Engineer'),
    ('Data Analyst'),
    ('Software Engineer'),
    ('Backend Engineer'),
    ('Platform Engineer'),
    ('DevOps Engineer'),
    ('BI Developer')
ON CONFLICT (name) DO NOTHING;

INSERT INTO skills (name)
VALUES
    ('Python'),
    ('SQL'),
    ('R'),
    ('Java'),
    ('Scala'),
    ('JavaScript'),
    ('TypeScript'),
    ('React'),
    ('PostgreSQL'),
    ('MySQL'),
    ('SQL Server'),
    ('MongoDB'),
    ('Redis'),
    ('Pandas'),
    ('NumPy'),
    ('Apache Spark'),
    ('PySpark'),
    ('Apache Kafka'),
    ('dbt'),
    ('Apache Airflow'),
    ('Databricks'),
    ('Delta Lake'),
    ('Parquet'),
    ('Azure'),
    ('Azure Data Factory'),
    ('Azure Data Lake Storage'),
    ('AWS'),
    ('Google Cloud'),
    ('Docker'),
    ('Docker Compose'),
    ('Kubernetes'),
    ('Terraform'),
    ('Linux'),
    ('Git'),
    ('GitHub Actions'),
    ('Power BI'),
    ('FastAPI'),
    ('REST API'),
    ('JSON'),
    ('Machine Learning'),
    ('Deep Learning'),
    ('Artificial Intelligence'),
    ('scikit-learn'),
    ('PyTorch'),
    ('TensorFlow'),
    ('OpenAI API'),
    ('Large Language Models'),
    ('Retrieval-Augmented Generation')
ON CONFLICT (name) DO NOTHING;

INSERT INTO seniority_levels (name, sort_order)
VALUES
    ('Intern', 10),
    ('Junior', 20),
    ('Mid-level', 30),
    ('Senior', 40),
    ('Lead', 50),
    ('Staff', 60),
    ('Principal', 70)
ON CONFLICT (name) DO NOTHING;

INSERT INTO proficiency_levels (name, sort_order)
VALUES
    ('Basic', 10),
    ('Intermediate', 20),
    ('Advanced', 30),
    ('Expert', 40)
ON CONFLICT (name) DO NOTHING;

INSERT INTO requirement_types (name, sort_order)
VALUES
    ('Required', 10),
    ('Preferred', 20),
    ('Nice to have', 30)
ON CONFLICT (name) DO NOTHING;

INSERT INTO work_modes (name)
VALUES
    ('Remote'),
    ('Hybrid'),
    ('On-site')
ON CONFLICT (name) DO NOTHING;

INSERT INTO employment_types (name)
VALUES
    ('Full-time'),
    ('Part-time'),
    ('Contract'),
    ('Internship'),
    ('Working student')
ON CONFLICT (name) DO NOTHING;

COMMIT;
