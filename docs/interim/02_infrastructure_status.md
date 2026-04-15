# 2. Infrastructure Status

_Interim report · Sprint 1 · 2026-04-15 · Team Mistral_

This section records the infrastructure standing behind the agent at the
interim submission cut-off: what is configured, what is wired up to the
running agent, and what the team deferred. Sources of truth referenced:
`DataAgentBench/docker-compose.yaml`, `agent/mcp/tools.yaml`, the tenai-infra
README at `../tenai/README.md`, and `planning/sprint_01_inception.md`.

---

## 2.1 tenai-infra running (optional)

**Status: configured locally and on the team server.** The challenge brief
marks this optional; Team Mistral set it up so mob sessions and agent
dispatches work across multiple devices.

tenai-infra is the team's infrastructure-as-code layer around Tailscale mesh
networking, tmux, and multi-CLI AI agent orchestration (Claude Code, Gemini
CLI, Codex CLI). It is the same infrastructure used in Week 4
(Brownfield Cartographer), per the Practitioner Manual. The repository
lives at `/home/neba/tenx/week8-9/tenai`.

**What is installed and active:**

| Layer | Tool | Purpose in Sprint 1 |
|---|---|---|
| Networking | Tailscale (WireGuard) | Zero-config mesh connectivity between team devices |
| Remote access | Mosh + tmux | Resilient shell, persistent mob-session sessions |
| AI orchestration | Claude Code, Gemini CLI, Codex CLI | Dispatched into isolated git worktrees |
| Orchestration | tenai conductor / orchestrator | Task generation, dispatch, monitoring, auto-merge |
| Device mgmt | `make onboard` / `make sync HOST=x` | Onboard devices; rsync + Docker rebuild per device |
| Config | `config/local.yaml` (gitignored) | Devices, orgs, repos — deep-merged over defaults |

Onboarding was performed via `make onboard` on each device (local workstation
and shared server). Each device has its own SQLite store at
`~/.tenai/devices/{name}.db` for task, subtask, and job state.

**Why it is marked optional in this challenge:** per Sprint 1 Inception
decision 4, the agent's facilitator-accessible access path is a FastAPI REST
endpoint on the shared server, not the tenai webapp. tenai-infra underpins
mob-session collaboration and agent dispatch, but the interim agent does not
depend on it for evaluation. Tenai coverage is revisited in Sprint 2.

---

## 2.2 Tailscale mesh verified (optional)

**Status: verified.** Tailscale is the networking substrate that tenai-infra
sits on top of. All team devices join the same tailnet using the
`TAILSCALE_AUTH_KEY` from the team `.env`, and `tailscale status` on the
shared server lists every team member's device. Device-to-device
connectivity is used during mob sessions so any Driver can pair into the
shared tmux session from any machine.

**Verification routine:**

```bash
tailscale status            # shows all connected team devices by name
tenai_devices               # tenai shell alias — list mesh devices
tenai_check                 # verify installed tools on this device
```

**Firewall note:** tenai-infra onboarding deliberately does not enable a
host-level firewall or alter SSH port configuration on cloud instances
(Security Groups are used instead). This matches the "Firewall Safety"
guidance in the tenai README.

---

## 2.3 DAB databases loaded

**Status: loaded for Sprint 1 scope (`query_bookreview` + `query_yelp`).**
The other 10 DAB datasets are prepared on disk and in the compose file, but
only bookreview and yelp are actively exercised end-to-end in the interim
evaluation (see `eval/scores/score_log.jsonl`).

### Compose topology (`DataAgentBench/docker-compose.yaml`)

The team replaced the skeleton compose file from
`docs/guides/DAB_SETUP.md` with a production-oriented compose that mounts
real DAB dataset directories and auto-restores MongoDB dumps:

| Service | Image | Container | Port mapping | Role |
|---|---|---|---|---|
| `python-data` | `python-data:3.12` (built from `DataAgentBench/Dockerfile`) | — | — | DAB code-execution sandbox image |
| `postgres` | `postgres:17` | `dab-postgres` | `5433:5432` | PostgreSQL server for DAB datasets |
| `mongodb` | `mongo:7` | `dab-mongodb` | `27018:27017` | MongoDB server for DAB datasets |
| `mongo-init` | `mongo:7` | `dab-mongo-init` | — | One-shot: runs `mongorestore` on each dump dir after `mongodb` is healthy |

Non-standard host ports (`5433`, `27018`) are used so the DAB stack does not
collide with any other Postgres/Mongo instance on the workstation.

### Credentials and persistence

| Service | User | Password | Default DB | Volume |
|---|---|---|---|---|
| `dab-postgres` | `postgres` | `trp-mistral` | `dab` | named volume `pgdata` |
| `dab-mongodb` | `mistral` | `trp-mistral` | — (auth via admin) | named volume `mongodata` |

Data is persisted across container restarts via named volumes (`pgdata`,
`mongodata`). Health is verified via `pg_isready` (Postgres) and
`db.adminCommand('ping')` (Mongo) healthchecks.

### Mounted dataset directories

**PostgreSQL (read-only mounts for SQL-file loading):**

- `query_bookreview/query_dataset` → `/data/bookreview`
- `query_googlelocal/query_dataset` → `/data/googlelocal`
- `query_PANCANCER_ATLAS/query_dataset` → `/data/pancancer`
- `query_PATENTS/query_dataset` → `/data/patents`
- `query_crmarenapro/query_dataset` → `/data/crmarenapro`

These are mounted inside the container so any SQL dump file (e.g.
`books_info.sql`) can be loaded via `psql -f /data/<name>/file.sql` without
copying files in.

**MongoDB (dump directories for `mongorestore`):**

- `query_yelp/query_dataset/yelp_business` → `/data/yelp_business`
- `query_agnews/query_dataset/agnews_articles` → `/data/agnews_articles`

The `mongo-init` service iterates `/dumps/*/*/` and runs `mongorestore` on
each subdirectory, using the inner directory name as the target database
(so `yelp_business/yelp_db/` restores into the `yelp_db` database). The
service is idempotent — if a target database already contains data, it is
skipped. This auto-restore was added specifically to avoid the "DB empty
after container recreation" failure mode that the team hit on Day 1.

### SQLite and DuckDB (no containers)

SQLite and DuckDB are file-based and live directly under each dataset's
`query_dataset/` folder (e.g. `query_bookreview/query_dataset/review_query.db`,
`query_yelp/query_dataset/yelp_user.db`). No server is required; the agent
reads them through the MCP Toolbox `sqlite-sql` driver or (for DuckDB) the
Flask app path with optional MotherDuck attachment.

### Git LFS and the 5 GB file

Dataset `.db` / `.duckdb` / `.sql` files are stored in Git LFS. The team
ran `git lfs install` then `git lfs pull` to materialise the files after
clone. One dataset file (`patent_publication.db`, ~5 GB) exceeds LFS limits
and is fetched separately via `bash download.sh` per the DAB README.
Verification step is `ls -lh query_<name>/query_dataset/` showing MB-scale
files rather than ~100-byte pointer stubs.

### Dataset status vs. Sprint 1 scope

| Dataset | Engine(s) | Loaded | Used in Sprint 1 eval |
|---|---|---|---|
| `query_bookreview` | Postgres + SQLite | Yes | **Yes** — passing at both baseline and submission |
| `query_yelp` | MongoDB (+ DuckDB for ratings) | Yes | **Yes** — passing at submission (`run_1`) |
| `query_agnews` | MongoDB + SQLite | Restored via `mongo-init` | Not yet — Sprint 2 |
| `query_googlelocal`, `query_PANCANCER_ATLAS`, `query_PATENTS`, `query_crmarenapro` | Postgres (+ file DBs) | SQL mounted, Postgres load pending | Not yet — Sprint 2 |
| `query_stockindex`, `query_stockmarket`, `query_GITHUB_REPOS`, `query_DEPS_DEV_V1`, `query_music_brainz_20k` | SQLite / DuckDB (file-based) | Files present | Not yet — Sprint 2 |

### How to bring the stack up

```bash
cd /home/neba/tenx/week8-9/DataAgentBench
docker compose up -d                        # starts postgres, mongodb, mongo-init
docker compose build python-data            # builds the sandbox image
docker ps --filter "name=dab-"              # expect dab-postgres + dab-mongodb (dab-mongo-init exits 0)
```

---

## 2.4 MCP Toolbox configured

**Status: `agent/mcp/tools.yaml` written and sized to Sprint 1 scope;
DuckDB wiring deferred.**

The Google GenAI MCP Toolbox is the standard interface between the agent
and DAB databases. A single `tools.yaml` defines sources, tools, and
toolsets; the agent calls tools via the MCP protocol instead of writing
raw drivers per engine.

### Binary

```bash
export VERSION=0.30.0
curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
chmod +x toolbox
./toolbox --config agent/mcp/tools.yaml    # listens on http://localhost:5000
curl http://localhost:5000/v1/tools | python3 -m json.tool | grep name
```

### Sources (`agent/mcp/tools.yaml`)

| Source ID | Kind | Connection | Backs |
|---|---|---|---|
| `dab-postgres-bookreview` | postgres | `${PG_HOST}:${PG_PORT}`, db `bookreview_db`, user/password from env | bookreview PG half |
| `dab-sqlite-bookreview` | sqlite | file path `${SQLITE_BOOKREVIEW_PATH}` | bookreview SQLite half |
| `dab-mongo-yelp` | mongodb | `${MONGO_URI}` | yelp Mongo half |

Connection parameters are taken from the team `.env` so the same `tools.yaml`
works against the Docker stack (ports 5433 / 27018) or any other backing
instance — nothing is hard-coded.

### Tools

| Tool | Kind | Purpose | Template / payload |
|---|---|---|---|
| `postgres-bookreview` | `postgres-sql` | Read-only SQL on `books_info` (Amazon book metadata: `title`, `author`, `price`, `rating_number`, `book_id`) | `{{.query}}` |
| `sqlite-bookreview` | `sqlite-sql` | Read-only SQL on `review` (Amazon reviews: `rating`, `title`, `text`, `purchase_id`, `review_time`, `helpful_vote`, `verified_purchase`) | `{{.query}}` |
| `mongo-yelp-business` | `mongodb-find` | Yelp `business` collection (metadata only — no star rating on this collection) | `filterJson` string |
| `mongo-yelp-aggregate` | `mongodb-aggregate` | Read-only aggregation pipeline over `yelp_db.business` | `pipelineJson` array |

### Toolsets

Toolsets are named bundles the agent can request by capability:

- `dab-all` — all four tools
- `dab-bookreview` — `postgres-bookreview` + `sqlite-bookreview`
- `dab-yelp` — `mongo-yelp-business` + `mongo-yelp-aggregate`
- `dab-relational` — `postgres-bookreview` + `sqlite-bookreview`

### Domain facts encoded in tool descriptions

The tool descriptions are written to prevent the two most expensive mistakes
we hit during smoke testing. Both are also documented in
`kb/domain/join_key_glossary.md`, but keeping them in the tool descriptions
means they land in the agent's tool-picker context automatically:

- **bookreview join**: `books_info.book_id` (Postgres) joins to
  `review.purchase_id` (SQLite). The field is named `purchase_id` but is a
  book foreign key, not a purchase identifier.
- **yelp ratings split**: `yelp_db.business` (Mongo) does **not** contain
  per-business star ratings. Rating math requires the DuckDB `review.rating`
  table. The MongoDB tool description calls this out explicitly so the agent
  does not attempt aggregation over a non-existent `stars` field.

### What is deferred

- **DuckDB via MotherDuck.** A YAML comment block in `tools.yaml` documents
  the intended future source (`kind: duckdb` or MotherDuck `md://` URI), but
  no DuckDB source or tool is wired up for the interim. DuckDB files are
  currently read by the Flask app path, with optional
  `MOTHERDUCK_TOKEN` + `DUCKDB_LOCAL_USE_MOTHERDUCK=1` for attaching the
  local DuckDB file to a MotherDuck workspace.
- **Second-dataset tools.** Extending coverage to the remaining 10 DAB
  datasets means adding one source + one tool per engine per dataset. That
  is Sprint 2 work; the pattern is established by the bookreview and yelp
  definitions above.

---

## Summary

| Area | Interim status |
|---|---|
| tenai-infra | Configured locally and on server (optional, not on the evaluation path) |
| Tailscale mesh | Verified; all team devices on the tailnet |
| DAB databases | Postgres + MongoDB running via `docker-compose.yaml`, auto-restore for Mongo dumps; bookreview and yelp exercised end-to-end; SQL loads for the other 4 Postgres datasets pending Sprint 2 |
| MCP Toolbox | `tools.yaml` wired for bookreview (PG + SQLite) and yelp (Mongo); 4 tools, 4 toolsets; DuckDB source deferred |

The infrastructure was deliberately sized to the Sprint 1 definition of
done (two DAB datasets, all four engine types covered across the two), not
the full 12-dataset benchmark. Expanding to the remaining datasets uses the
same compose mounts, the same MCP Toolbox source/tool pattern, and the
same MongoDB auto-restore service — no new infrastructure shape is required.
