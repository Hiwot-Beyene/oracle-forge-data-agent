# DataAgentBench Setup Guide

> Based on the TRP1 Practitioner Manual and the official DAB repository README.
> Target: get all 12 DAB datasets loaded and a first test query running.

---

## Prerequisites

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Git LFS | any | `git lfs version` |
| Docker | 28.x+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Python | 3.12 | `python3 --version` |

PostgreSQL and MongoDB run as Docker containers (see Step 4).
SQLite and DuckDB are file-based — no server install required.

---

## Step 1 — Clone the Repository

DAB uses Git LFS for large database files. Enable LFS before cloning:

```bash
git lfs install
git clone https://github.com/ucbepic/DataAgentBench.git
cd DataAgentBench
```

One database file (`patent_publication.db`, ~5 GB) exceeds LFS limits.
Download it separately:

```bash
bash download.sh
```

This places the file at `query_PATENTS/query_dataset/patent_publication.db`.

If you already have the repo cloned, verify LFS files were pulled:

```bash
git lfs pull
```

---

## Step 2 — Install Python Dependencies

A pinned `requirements.txt` is already generated in the DAB repo root.
Use a venv and pip:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Key packages in the requirements: `psycopg2-binary` (PostgreSQL), `pymongo` (MongoDB),
`duckdb` (DuckDB), `docker` (sandbox execution), `openai`/`litellm` (LLM clients),
`pandas`, `pyarrow`, `python-dotenv`.

---

## Step 3 — Build the Docker Sandbox Image

DAB executes agent-generated Python code inside a Docker container for safety:

```bash
docker build -t python-data:3.12 .
```

Verify it works:

```bash
docker run --rm python-data:3.12 python -c "import pandas; print(pandas.__version__)"
```

---

## Step 4 — Start Database Servers (Docker)

Both PostgreSQL and MongoDB run as Docker containers. Create a
`docker-compose.dab.yml` in the DAB repo root (or the oracle-forge project root):

```yaml
services:
  postgres:
    image: postgres:17
    container_name: dab-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test
    volumes:
      - dab-pgdata:/var/lib/postgresql/data

  mongo:
    image: mongo:7
    container_name: dab-mongo
    restart: unless-stopped
    ports:
      - "27017:27017"
    volumes:
      - dab-mongodata:/data/db

volumes:
  dab-pgdata:
  dab-mongodata:
```

Start both services:

```bash
docker compose -f docker-compose.dab.yml up -d
```

### Verify

```bash
# PostgreSQL
pg_isready -h 127.0.0.1 -p 5432
# Expected: 127.0.0.1:5432 - accepting connections

# MongoDB
docker exec dab-mongo mongosh --eval "db.runCommand({ping:1})" --quiet
# Expected: { ok: 1 }
```

### Stop / restart

```bash
docker compose -f docker-compose.dab.yml down      # stop
docker compose -f docker-compose.dab.yml up -d      # restart
docker compose -f docker-compose.dab.yml down -v    # stop and delete data volumes
```

---

## Step 5 — Load Datasets

### Overview of datasets by database type

| Database Type | Datasets |
|--------------|----------|
| PostgreSQL | bookreview, crmarenapro, googlelocal, pancancer_atlas, patents |
| MongoDB | agnews, yelp |
| SQLite | agnews, bookreview, crmarenapro, deps_dev_v1, github_repos, googlelocal, music_brainz_20k, patents, stockindex, stockmarket |
| DuckDB | crmarenapro, deps_dev_v1, github_repos, music_brainz_20k, pancancer_atlas, stockindex, stockmarket, yelp |

**TRP recommended load order:** PostgreSQL first, then SQLite (automatic), then MongoDB, then DuckDB (automatic).

### 5a — Load PostgreSQL databases

Each dataset with PostgreSQL has `.sql` dump files in its `query_dataset/` folder.
Load them into the Docker container using `psql`:

```bash
# Example: bookreview
psql -U postgres -h 127.0.0.1 -f query_bookreview/query_dataset/books_info.sql

# Example: googlelocal
psql -U postgres -h 127.0.0.1 -f query_googlelocal/query_dataset/*.sql

# Repeat for each PostgreSQL dataset.
# Check each dataset's db_config.yaml for the exact database name and files.
```

Alternatively, copy the SQL file into the container:

```bash
docker cp query_bookreview/query_dataset/books_info.sql dab-postgres:/tmp/
docker exec dab-postgres psql -U postgres -f /tmp/books_info.sql
```

**Important:** Read the `db_config.yaml` in each dataset folder to know:
- Which database name to use
- Which files to load
- Connection parameters

Example `db_config.yaml` structure:
```yaml
db_clients:
  postgres_db:
    type: postgres
    db_name: bookreview
    sql_file: query_dataset/books_info.sql
```

### 5b — Load MongoDB datasets

Datasets using MongoDB (`agnews`, `yelp`) have BSON or JSON data in their
`query_dataset/` folders. Check each dataset's `db_config.yaml` for import details:

```bash
# Check what MongoDB needs
cat query_agnews/db_config.yaml
cat query_yelp/db_config.yaml
```

Use `mongoimport` or `mongorestore` against the Docker container:

```bash
# Example: import a JSON collection
docker exec -i dab-mongo mongoimport --db <db_name> --collection <collection> --file /dev/stdin < path/to/data.json
```

### 5c — SQLite and DuckDB (no action needed)

These operate directly on `.db` / `.duckdb` files in each dataset's
`query_dataset/` folder. Paths are resolved automatically from `db_config.yaml`.

---

## Step 6 — Configure Environment Variables

Create a `.env` file in the DAB repository root:

```bash
cat > .env << 'EOF'
# PostgreSQL (Docker container)
PG_HOST=127.0.0.1
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_DB=test

# MongoDB (Docker container)
MONGO_URI=mongodb://localhost:27017/

# LLM API Keys (add the ones you need)
AZURE_API_BASE=
AZURE_API_KEY=
AZURE_API_VERSION=
GEMINI_API_KEY=
TOGETHER_API_KEY=
EOF
```

The password `postgres` matches the `POSTGRES_PASSWORD` set in the Docker Compose file.
Change both if you use a different password.

Default values are defined in `common_scaffold/tools/db_utils/db_config.py`.
The `.env` overrides them.

---

## Step 7 — Verify Setup with a Test Query

The TRP docs recommend starting with **Yelp** (covers multi-source data, nested JSON,
missing values, entity resolution). For a quick smoke test, **bookreview** is simpler:

```bash
python run_agent.py \
    --dataset bookreview \
    --query_id 1 \
    --llm gpt-5-mini \
    --iterations 100 \
    --use_hints \
    --root_name run_0
```

Logs are saved under:

```
query_bookreview/query1/logs/data_agent/run_0/
├── exec_tool_work_dir/     # Docker working directory
├── final_agent.json        # Full agent trajectory + stats
├── llm_calls.jsonl         # All LLM API calls
└── tool_calls.jsonl        # All tool calls
```

---

## Step 8 — Validate Results

### Single run validation

```python
from pathlib import Path
import json

run_dir = Path("query_bookreview/query1/logs/data_agent/run_0")
with open(run_dir / "final_agent.json") as f:
    result = json.load(f)

print("Answer:", result["final_result"])
print("Termination:", result["terminate_reason"])
```

### Pass@1 accuracy (requires 50 runs)

```python
from python_script.avg_accuracy import avg_acc
print(avg_acc("bookreview", "gpt-5-mini"))
```

---

## Step 9 — Using a Custom LLM (e.g., Claude)

DAB ships with support for Azure GPT, Gemini, and Together AI. To add Claude or
another model, edit `common_scaffold/DataAgent.py` around line 76:

```python
if "gpt" in deployment_name.lower():
    self.client = AzureOpenAI(...)
elif "claude" in deployment_name.lower():
    # Add your Claude client here
    from anthropic import Anthropic
    self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
else:
    raise ValueError(f"Unsupported deployment name: {deployment_name}")
```

Also update `common_scaffold/prompts/prompt_builder.py` to handle your model's
tool call format.

---

## Full Benchmark Run (for submission)

Run all 54 queries with 50 trials each (plan for 2+ hours):

```bash
# Run across all datasets and queries
# Adjust --llm to your model
python run_agent.py \
    --dataset <dataset_name> \
    --query_id <query_id> \
    --llm <your-model> \
    --iterations 100 \
    --root_name run_<N>
```

Repeat for all datasets/queries/runs. Collect results into a single JSON:

```json
[
  {
    "dataset": "bookreview",
    "query": "1",
    "run": "0",
    "answer": "<agent_generated_answer>"
  }
]
```

Submit via PR to `ucbepic/DataAgentBench`:
- Title: `[Team Name] — TRP1 FDE Programme, April 2026`
- Include: results JSON, AGENT.md with architecture description, pass@1 score

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `git lfs pull` gives errors | Run `git lfs install` then `git lfs pull` again |
| PostgreSQL connection refused | Check container is running: `docker ps \| grep dab-postgres`, then `pg_isready -h 127.0.0.1` |
| MongoDB connection refused | Check container is running: `docker ps \| grep dab-mongo` |
| Docker build fails | Ensure Docker daemon is running: `sudo systemctl start docker` |
| `patent_publication.db` missing | Run `bash download.sh` (requires `gdown`: `pip install gdown`) |
| Python import errors | Activate the venv: `source venv/bin/activate` and run `pip install -r requirements.txt` |

---

## References

| Resource | URL |
|----------|-----|
| DAB Repository | https://github.com/ucbepic/DataAgentBench |
| DAB Paper | https://arxiv.org/abs/2603.20576 |
| DAB Leaderboard | https://ucbepic.github.io/DataAgentBench/ |
| Google MCP Toolbox | https://github.com/googleapis/genai-toolbox |
| TRP1 Practitioner Manual | `docs/trp/TRP1 Week 8-9 Practitioner Manual_ The Oracle Forge of Data Agent.md` |
