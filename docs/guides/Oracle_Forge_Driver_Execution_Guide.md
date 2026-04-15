

| THE ORACLE FORGE WEEKS 8–9 · TRP1 FDE PROGRAM DRIVER EXECUTION GUIDE A Complete Step-by-Step Manual for Drivers April 2026 |
| :---: |

*This guide provides a complete, step-by-step execution manual for Drivers in the Oracle Forge challenge. Drivers hold primary accountability for the running codebase, the evaluation harness, the benchmark submission, and the AI-DLC documentation. Every task below is drawn directly from the challenge brief and practitioner manual.*

| Who This Guide Is For Drivers (2 members per team). You control the keyboard and AI tool interface during mob sessions. This guide takes you from zero to benchmark submission across 20 discrete, detailed tasks. |
| :---- |

| Item | Detail |
| :---- | :---- |
| **Intermediate deadline** | Wednesday, April 15 — 21:00 UTC |
| **Final deadline** | Saturday, April 18 — 21:00 UTC |
| **Benchmark** | DataAgentBench (DAB) — 54 queries, 50 trials each |
| **Shared server** | tenai-infra (same as Week 4\) |
| **Primary AI interface** | Gemini CLI conductor via tenai-infra |

#   **PHASE 1 — STUDY & PREPARATION**  

Before writing a single line of agent code, Drivers must read and understand the four source documents that define the architecture. This is not optional background reading — it directly shapes the decisions made in Construction.

| 1 | Read the Claude Code Architecture (claude-code-source-code) |
| :---: | :---- |

### **What to do**

Navigate to the two GitHub repositories containing the leaked Claude Code source and architecture docs:

* github.com/sanbuphy/claude-code-source-code — focus on docs/en/

* github.com/chauncygu/collection-claude-code-source-code

### **What to extract**

Record these three specific findings into a shared notes document before leaving this step:

1. Three-layer MEMORY.md architecture: how the index file (MEMORY.md) points to topic files, which point to session transcripts. Understand that only the index is loaded automatically; topic files are fetched on demand.

2. autoDream memory consolidation pattern: how the agent compresses and consolidates older memory entries to prevent context overflow while retaining decision history.

3. Tool scoping philosophy: how 40+ tools are divided into tight domain boundaries so the agent never has access to more tools than the current task requires. Note the fork/worktree sub-agent spawn modes.

| Why this matters for your build Your agent's context layer architecture directly mirrors this three-layer pattern. If you understand it before building, you avoid retrofitting it later. |
| :---- |

| 2 | Read the OpenAI In-House Data Agent Writeup |
| :---: | :---- |

### **What to do**

Read the full writeup at: openai.com/index/inside-our-in-house-data-agent

### **What to extract**

4. The six-layer context architecture — understand each layer's purpose and how they stack. Your agent needs at minimum three; understanding all six tells you which three matter most.

5. Codex-powered table enrichment: the '70,000 tables' problem — how the agent populates metadata for databases so large that no human could document them manually.

6. Self-learning memory loop: how the agent writes back corrections it receives from users into a persistent corrections store that it reads at the start of each new session.

7. The closed-loop self-correction pattern: how the agent detects its own execution failures, diagnoses root cause (query error vs. join key mismatch vs. data quality), and retries with a corrected approach.

| 3 | Read the DataAgentBench Paper and Repository |
| :---: | :---- |

### **What to do**

Read the paper and explore the repository:

* Paper: arxiv.org/html/2603.20576

* Repository: github.com/ucbepic/DataAgentBench

### **What to extract — the four hard requirements**

These four requirements define every architectural decision your agent needs to make. Write one paragraph for each in your notes:

8. Multi-database integration: a single query may span PostgreSQL and MongoDB. Your agent must route sub-queries to the correct database, translate between SQL and MongoDB aggregation pipeline dialects, and merge results without data loss.

9. Ill-formatted join keys: the same customer may appear as integer 12345 in PostgreSQL and as string 'CUST-00123' in MongoDB. The agent must detect this mismatch and resolve it without being explicitly told.

10. Unstructured text transformation: some queries require extracting structured facts from free-text fields (support notes, product descriptions, reviews). The agent must perform extraction before the fact can be used in a calculation.

11. Domain knowledge requirements: some queries use terms not defined in any schema — 'churn,' 'active customer,' fiscal year boundaries, status codes. The agent must have this knowledge before the query arrives.

### **What to note about the benchmark format**

* 54 queries total across 12 datasets

* 9 domains: retail, telecom, healthcare, finance, anti-money laundering, and others

* 4 database systems: PostgreSQL, MongoDB, SQLite, DuckDB

* Best current score: PromptQL \+ Gemini 3.1 Pro at 54.3% pass@1

* Evaluation: pass@1 score, n \>= 50 trials per query

#   **PHASE 2 — AI-DLC INCEPTION**  

No Construction code is written until the Inception document exists and receives full team approval at a mob session. This is a hard gate, not a suggestion.

| 4 | Write the AI-DLC Inception Document |
| :---: | :---- |

### **What is the Inception document?**

The Inception document is the team's written commitment to what will be built, written as if the sprint is already complete. It has six mandatory sections:

### **Section 1 — Press Release (one paragraph)**

Write this in present tense as if the sprint is done. Name specifically: what was built, what it can do, why it matters. Hard to write well — that difficulty is intentional. If you cannot write this paragraph clearly, the team does not yet understand what it is building.

### **Section 2 — Honest FAQ: User (three Q\&A)**

Questions a user would ask about the product. Honest answers. Include what the agent does not do. Example questions:

* 'Can the agent answer questions across two databases at once?' — Yes / No / Under what conditions?

* 'What happens when the agent makes a mistake?' — Describe the recovery behaviour.

* 'How long does a typical query take?' — Provide an honest estimate.

### **Section 3 — Honest FAQ: Technical (three Q\&A)**

What could go wrong. What the hardest part is. What dependencies exist. Honest answers. Examples:

* 'What is the biggest risk to the timeline?' — Be specific.

* 'What does the agent do if a database is unavailable?' — Describe the failure mode.

* 'Which DAB failure category is hardest to handle?' — Name it and explain why.

### **Section 4 — Key Decisions (two to three)**

Each architectural or technical decision with the chosen option and a one-sentence reason. No decisions by default or silence. Examples:

* Context storage: AGENT.md file loaded at session start vs. database-backed retrieval. Choice and reason.

* Code execution sandbox: Local tenai-infra container vs. Cloudflare Workers. Choice and reason.

### **Section 5 — Definition of Done (five to eight items)**

Numbered, specific, verifiable. Not 'agent works' — instead: 'Agent returns the correct answer to Yelp dataset query 0 in under 15 seconds, verified by running eval/run\_query.py \--dataset yelp \--query 0.' Every item must be testable without subjective judgment.

| Critical rule Drivers write the Inception document, but the team approves it. No Driver writes it alone in Slack. It is presented at a mob session, read aloud, questioned, and approved collectively. Record the date, who approved, and the hardest question asked in planning/mob\_session\_log.md. |
| :---- |

| 5 | Run the Mob Session Inception Gate |
| :---: | :---- |

### **What to do at the mob session**

12. Driver reads the Inception document aloud to the full team.

13. Team asks the hardest questions they can think of about feasibility, risks, and definition of done.

14. Driver answers on the spot. If an answer reveals a gap, the Inception document is revised before approval.

15. Team gives explicit collective approval (verbal or thumbs up in session).

16. Driver records in planning/mob\_session\_log.md: date, names of attendees, hardest question asked, and the answer given.

Only after this record exists does Construction begin.

#   **PHASE 3 — INFRASTRUCTURE SETUP**  

Infrastructure is the foundation everything else runs on. Set it up correctly before building the agent. Do not skip steps — each one is a dependency for the next.

| 6 | Clone and Configure tenai-infra on the Shared Server |
| :---: | :---- |

### **What to do**

The tenai-infra system is the same infrastructure used in Week 4 (Brownfield Cartographer). You are not learning new tooling — you are applying familiar tooling at scale.

\# Step 1: Clone tenai-infra on the team server  
git clone https://github.com/yabebalFantaye/tenai /shared/tenai-infra  
cd /shared/tenai-infra  
   
\# Step 2: Read the README completely before doing anything else  
cat README.md  
   
\# Step 3: Follow the installation README exactly  
\# Do not deviate. If you find a gap, report it as an issue.  
   
\# Step 4: Start the persistent tmux session  
tmux new-session \-s oracle-forge  
   
\# All team members attach with:  
tmux attach \-t oracle-forge

### **What this gives you**

* Tailscale mesh networking: all team members connect from any device without VPN configuration

* Gemini CLI conductor: manages parallel AI agent sessions all team members can observe and direct

* Parallel git worktrees: run multiple experiments simultaneously without branch interference

* tmux monitoring: persistent sessions that survive disconnections

| 7 | Verify Tailscale Mesh — All Devices Connected |
| :---: | :---- |

### **What to do**

17. Each team member installs Tailscale on their personal device (laptop, mobile, tablet).

18. Each team member joins the team network using the auth key from the tenai-infra README.

19. Driver runs the verification command on the server:

tailscale status  
\# Expected output: shows all connected team devices by name  
\# Every team member's device should appear here  
\# If a device is missing, they have not joined the Tailscale network

Do not proceed to agent build until every team member can connect to the shared server. A team member who cannot connect cannot participate in mob sessions.

| 8 | Clone DataAgentBench and Load Databases |
| :---: | :---- |

### **What to do — load in this order**

Load databases in the sequence below. The benchmark provides setup scripts for each. Do not attempt to load all databases simultaneously on day one — start with PostgreSQL, which covers the majority of DAB queries.

\# Clone the DataAgentBench repository  
git clone https://github.com/ucbepic/DataAgentBench.git  
cd DataAgentBench  
   
\# Read setup guide completely before running scripts  
cat README.md  
   
\# Install Python dependencies  
pip install \-r requirements.txt  
   
\# LOAD ORDER: PostgreSQL first (covers most DAB queries)  
bash setup/load\_postgres.sh  
   
\# Then SQLite  
bash setup/load\_sqlite.sh  
   
\# Then MongoDB  
bash setup/load\_mongo.sh  
   
\# Finally DuckDB  
bash setup/load\_duckdb.sh

### **Verify your setup with the Yelp dataset**

The Yelp dataset is the recommended starting point — it contains multi-source data, nested JSON, missing values, and entity resolution challenges that mirror the full DAB problem space in a contained form.

\# Run the example query against Yelp to verify installation  
python eval/run\_query.py \--dataset yelp \--query 0  
   
\# Expected output: structured result JSON with query trace  
\# If this fails, diagnose before touching agent code

| 9 | Configure Google MCP Toolbox |
| :---: | :---- |

### **What is MCP Toolbox?**

MCP Toolbox for Databases provides the standard interface between your agent and the DAB databases. A single tools.yaml file defines all database connections. Your agent calls tools from this file via the MCP protocol rather than writing raw database drivers per database type.

\# Download the toolbox binary  
\# Check googleapis/genai-toolbox for the latest version  
export VERSION=0.30.0  
curl \-O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox  
chmod \+x toolbox  
   
\# Use the starter template from team repository  
\# File: mcp/tools.yaml  
\# This file must define connections to all four database types:  
\# PostgreSQL, SQLite, MongoDB, DuckDB  
   
\# Start the toolbox  
./toolbox \--config mcp/tools.yaml  
\# Toolbox runs on http://localhost:5000  
   
\# Verify all databases are accessible  
curl http://localhost:5000/v1/tools | python3 \-m json.tool | grep name

| Intelligence Officer handoff Intelligence Officers maintain the tools documentation in the Knowledge Base. After you configure tools.yaml, hand the connection parameters and any notes to the Intelligence Officers for kb/domain/ documentation. |
| :---- |

| 10 | Set Up the Code Execution Sandbox |
| :---: | :---- |

### **What is the sandbox for?**

The sandbox executes data transformation code outside the LLM context. It follows the same pattern used in Week 4 (Brownfield Cartographer). The agent sends a code plan to the sandbox; the sandbox executes it against the databases, runs validation, and returns structured results.

### **Option A — Local container (tenai-infra default, recommended)**

\# The tenai-infra system includes a default sandbox container  
\# See tenai-infra/sandbox/README.md for full configuration  
   
\# Start the sandbox server  
python3 sandbox/sandbox\_server.py \--port 8080  
   
\# The agent sends code to: POST /execute  
\# Returns: { result, trace, validation\_status, error\_if\_any }

### **Option B — Cloudflare Workers (free tier)**

\# Signal Corps applies for Cloudflare free tier on Day 1  
\# Once Signal Corps confirms access:  
   
npm install \-g wrangler  
wrangler login  
   
cd workers && wrangler deploy  
\# Worker URL: https://sandbox.\[team-name\].workers.dev  
   
\# Set in team .env file:  
SANDBOX\_URL=https://sandbox.\[team-name\].workers.dev

#   **PHASE 4 — CORE AGENT BUILD**  

With infrastructure confirmed and Inception approved, Construction begins. The team builds the agent at mob sessions — Driver holds the keyboard, everyone co-pilots. The agent grows incrementally: basic query first, then context layers, then self-correction.

| 11 | Build the Agent Core — Natural Language to Query |
| :---: | :---- |

### **What to build first**

Start with the simplest possible working agent: it receives a natural language question, queries one database (Yelp/PostgreSQL), and returns a result. Do not add context layers or self-correction until this baseline works.

### **Required agent interface**

Your agent must accept and return in this format (required for DAB evaluation):

\# Input format (what DAB sends to your agent):  
\# {  
\#   'question': 'Which businesses have the highest review count?',  
\#   'available\_databases': \['yelp\_postgres', 'yelp\_mongo'\],  
\#   'schema\_info': { ... }  
\# }  
   
\# Output format (what your agent must return):  
\# {  
\#   'answer': '...',  
\#   'query\_trace': \[ { db, query, result } \],  
\#   'confidence': 0.0 to 1.0  
\# }

### **Required files to commit**

* agent/AGENT.md — context file describing the agent's purpose, databases it connects to, and domain knowledge injected

* agent/tools.yaml — MCP connections to all database types

* agent/requirements.txt — all Python dependencies

* All agent source files in agent/ directory

### **Week 8 milestone**

By end of Week 8 Day 5: agent running on the shared server, handling at least two DAB database types, with basic NL-to-query working. This is the minimum for the Wednesday intermediate submission.

| 12 | Implement the Three Context Layers |
| :---: | :---- |

### **Why context layers are the bottleneck**

The Claude Code and OpenAI data agent sources converge on the same insight: the bottleneck in production data agents is not query generation — it is context. An agent that cannot find the right table, understand what a business term means, or remember what the user corrected it on, will fail on questions trivially easy for a human analyst.

### **Layer 1 — Schema and Metadata Knowledge**

Populated before the agent answers its first question. Contains:

* Schema descriptions for all connected DAB databases — table names, column names, data types

* Which tables are authoritative vs. deprecated

* How data in each table was generated (source system, ETL logic if known)

* Row count estimates, known null rates for critical columns

### **Layer 2 — Institutional and Domain Knowledge**

Answers the question: what does this data mean in this organisation's context? Contains:

* Business term definitions: what 'revenue,' 'churn,' 'active customer,' 'repeat purchase' mean in each domain

* Fiscal calendar conventions: when does Q3 start in this dataset?

* Status code meanings: which values indicate active vs. inactive accounts

* Join key format glossary: how the same entity ID appears differently across databases (provided by Intelligence Officers in kb/domain/join\_keys.md)

### **Layer 3 — Interaction Memory (Corrections Log)**

The self-learning mechanism. Contains:

* Structured log of past failures: \[query that failed\] → \[what was wrong\] → \[correct approach\]

* Successful query patterns by domain and database type

* User corrections received in prior sessions

This layer is read by the agent at the start of every new session and written to after every observed failure. It is stored in kb/corrections/ and maintained by Intelligence Officers.

### **How to inject context layers**

Context layers are injected into the agent's context window at session start via AGENT.md and the KB documents. The agent does not retrieve them on demand for Layers 1 and 2 — they are present from the first token. Layer 3 (corrections log) is also loaded at start, ensuring the agent benefits from its own history immediately.

| Minimum requirement All three layers must be implemented and demonstrably populated before the final submission. 'Implemented' means the agent reads them. 'Populated' means they contain real, tested content from the DAB databases — not placeholder text. |
| :---- |

| 13 | Implement Self-Correcting Execution |
| :---: | :---- |

### **What self-correction means**

The agent must detect execution failures, diagnose the cause, and recover without surfacing the error to the user. This is the closed-loop self-correction pattern from the OpenAI data agent writeup.

### **Four failure categories to handle**

20. Query error: the SQL or MongoDB aggregation syntax is wrong. Correction: rewrite the query with fixed syntax.

21. Join key format mismatch: the agent attempts to join integer IDs with string IDs. Correction: detect format mismatch, apply normalisation from the join key glossary, retry.

22. Database type mismatch: the agent routes a query to the wrong database type. Correction: re-route to the correct database, translate query dialect.

23. Data quality failure: the query executes but the result is empty or implausible due to data issues. Correction: inspect the data, apply known quality rules, retry with adjusted filters.

### **Implementation pattern**

def execute\_with\_recovery(query, db\_type, max\_retries=3):  
    for attempt in range(max\_retries):  
        result \= execute(query, db\_type)  
        if result.success:  
            return result  
        \# Diagnose failure  
        cause \= diagnose\_failure(result.error, query, db\_type)  
        \# Log to corrections store  
        log\_failure(query, cause)  
        \# Apply fix based on cause  
        query, db\_type \= apply\_fix(cause, query, db\_type)  
    return result  \# Return last attempt with error trace

#   **PHASE 5 — EVALUATION HARNESS**  

You cannot compete on a benchmark if you cannot tell whether your last change made the agent better or worse. The evaluation harness is not an afterthought — it is the mechanism that drives improvement across Weeks 8 and 9\.

| 14 | Build the Evaluation Harness |
| :---: | :---- |

### **What the harness must do**

This harness is the Sentinel pattern from Week 5 (Event Sourcing), applied to data agents. You are adapting what you built, not building from scratch. The harness must:

24. Trace every tool call the agent makes — record inputs, outputs, latency, database targeted

25. Record query outcomes against expected results — pass or fail, with failure mode tagged

26. Produce a pass@1 score for each run across the held-out test set

27. Run a regression suite — confirm that queries the agent previously passed still pass

28. Write a score log — every run appends to a log showing progression over time

### **Trace schema (same as Week 5\)**

\# Each trace entry records:  
{  
  'run\_id': 'uuid',  
  'timestamp': 'ISO8601',  
  'query\_id': 'DAB query identifier',  
  'question': 'natural language question',  
  'tool\_calls': \[  
    { 'tool': 'postgres\_query', 'input': '...', 'output': '...', 'latency\_ms': 320 },  
    { 'tool': 'mongo\_aggregate', 'input': '...', 'output': '...', 'latency\_ms': 180 }  
  \],  
  'answer': 'agent answer',  
  'expected': 'DAB expected answer',  
  'pass': true,  
  'failure\_mode': null  
}

### **Score log format**

\# eval/score\_log.csv — one row per run  
run\_id, timestamp, pass\_at\_1, queries\_run, regression\_pass, notes  
run\_001, 2026-04-13T10:00Z, 0.22, 54, true, first baseline  
run\_002, 2026-04-14T14:00Z, 0.31, 54, true, added KB v2 domain layer  
run\_003, 2026-04-15T09:00Z, 0.38, 54, true, join key resolver added

| Required for submission The score log must show a minimum of two data points: first run (Week 8 baseline) and final submission (Week 9). Measurable improvement between them is required for the Advanced evaluation tier. |
| :---- |

| 15 | Record First-Run Baseline Score |
| :---: | :---- |

### **What to do**

As soon as the harness is working and the agent handles at least two database types, run the full held-out evaluation and record the baseline. This is the first entry in your score log. It will almost certainly be a low score — that is expected and correct.

\# Run evaluation against held-out test set  
python eval/run\_benchmark.py \\  
  \--agent your\_agent\_module \\  
  \--trials 5 \\  
  \--output results/baseline\_run.json  
   
\# Score the results  
python eval/score.py \--results results/baseline\_run.json  
   
\# Append to score log  
\# eval/score\_log.csv — add your first row here

The baseline score is not a measure of success — it is a starting point. Every subsequent change to the agent (new KB document, new context layer, join key fix) should be followed by a harness run and a new score log entry.

| 16 | Log Agent Failures for Intelligence Officers |
| :---: | :---- |

### **The feedback loop**

This is the mechanism by which the agent improves without retraining. Every time the agent produces a wrong answer or fails to execute a query, the Driver logs the failure in a structured format. Intelligence Officers read this log and add entries to kb/corrections/. The corrections log is then read by the agent at the next session start.

### **Log format — kb/corrections/corrections\_log.md**

\#\# Failure Entry \[DATE\]  
   
\*\*Query that failed:\*\*  
'Which customer segments had declining repeat purchase rates in Q3?'  
   
\*\*What was wrong:\*\*  
Agent interpreted 'Q3' as calendar Q3 (Jul-Sep).  
The Yelp dataset uses a fiscal calendar where Q3 \= Oct-Dec.  
   
\*\*Correct approach:\*\*  
Use fiscal\_calendar.md from kb/domain/ to resolve quarter boundaries.  
Filter date column using fiscal\_q3\_start and fiscal\_q3\_end constants.  
   
\*\*Post-fix verified:\*\*  
Yes — ran eval/run\_query.py \--query 12 after adding KB entry. Passed.

Write one entry per failure. Intelligence Officers maintain the log, but Drivers write it. Speed matters: a failure logged immediately is a failure fixed for the next run.

#   **PHASE 6 — ADVERSARIAL TESTING & IMPROVEMENT**


| 17 | Run Adversarial Probes and Iterate |
| :---: | :---- |

### **What are adversarial probes?**

Adversarial probes are queries specifically designed to expose the agent's failure modes. Intelligence Officers build the probe library (15+ probes across 3+ failure categories), but Drivers run the probes and record the results. The feedback from probe runs directly improves the agent.

### **The four failure categories to probe**

29. Multi-database routing failure — query requires data from two databases; agent queries only one or fails the join.

30. Ill-formatted key mismatch — same entity appears as integer in one DB and prefixed string in another; agent joins without format resolution.

31. Unstructured text extraction failure — query requires counting or aggregating over free-text field content; agent returns raw text instead of structured result.

32. Domain knowledge gap — query uses a term not in the schema; agent uses a naive interpretation and returns a plausible but wrong answer.

### **For each probe, record in probes/probes.md**

* The exact query text

* The failure category (one of the four above)

* The expected failure mode

* The observed agent response

* The fix applied (KB update, code change, context layer addition)

* The post-fix score on this probe

### **The improvement cycle**

Each probe run follows this cycle:

33. Run the probe query against the agent.

34. Record the observed failure in the corrections log.

35. Intelligence Officers update the KB with a correction or new domain term.

36. Driver re-deploys the agent with the updated KB loaded.

37. Run the probe again and record the post-fix score.

38. Run the full harness and update the score log.

#   **PHASE 7 — BENCHMARK SUBMISSION**


| 18 | Run the Full DAB Benchmark |
| :---: | :---- |

### **When to run the full benchmark**

Run the full benchmark (54 queries, 50 trials each) only when the agent is stable enough to complete a full run without crashing. Running prematurely wastes compute and produces a score that does not reflect the agent's actual capability. The minimum state before running: all four database types connected, all three context layers populated, harness producing clean regression suite results.

\# Full benchmark run — plan for at least 2 hours  
python eval/run\_benchmark.py \\  
  \--agent your\_agent\_module \\  
  \--trials 50 \\  
  \--output results/your\_team\_results.json  
   
\# Score the results  
python eval/score.py \--results results/your\_team\_results.json  
   
\# Record in score log  
\# This is the score you will submit

| Note on trial count DAB requires n \>= 50 trials per query for the benchmark submission. During development and testing, use \--trials 5 to save time. Only use \--trials 50 for the final submission run. |
| :---- |

| 19 | Submit GitHub Pull Request to DataAgentBench |
| :---: | :---- |

### **What to prepare**

39. Copy your results JSON to the submission directory with your team name

40. Write AGENT.md describing your agent (required for the PR)

41. Fork the ucbepic/DataAgentBench repository on GitHub

42. Commit your files and open the PR

\# Prepare submission files  
cp results/your\_team\_results.json submission/team\_\[name\]\_results.json  
   
\# AGENT.md must include:  
\# \- Architecture overview (which context layers, which database types)  
\# \- Key design decisions made  
\# \- What worked and what did not  
\# \- pass@1 score and trial count  
   
\# Fork the repository on GitHub, then:  
git add submission/team\_\[name\]\_results.json AGENT.md  
git commit \-m 'Add \[Team Name\] DAB evaluation results'  
git push origin main  
   
\# Open Pull Request to ucbepic/DataAgentBench  
\# Title: '\[Team Name\] \- TRP1 FDE Programme, April 2026'  
\# Body: pass@1 score, trial count, brief architecture description

Once the PR is opened, notify Signal Corps immediately. The PR submission is a public milestone that Signal Corps should post about on X, linking to the DAB repository and noting the team's score.

#   **PHASE 8 — DOCUMENTATION & CLOSE**


| 20 | Write the AI-DLC Operations Document |
| :---: | :---- |

### **What the Operations document contains**

The Operations document is the record that survives if the codebase is deleted. It is written after Construction is complete and verified. It answers four questions:

43. What was built — describe the system as it exists, not as it was planned. If the final agent differs from the Inception document, say so explicitly.

44. What changed from the plan — list every significant deviation from the Inception document. What was harder than expected? What was easier? What was abandoned and why?

45. What the harness score is — include the score log table showing progression from first run to final submission. This is the evidence of improvement.

46. What the next sprint's Inception should address — what are the open problems? What would you build next if the sprint continued?

| Operations is a deliverable The Operations document is submitted as part of planning/ directory alongside the Inception document and mob session approval logs. A submitted agent without an Operations document is an incomplete submission. |
| :---- |

## **Final Repository Checklist**

Before submitting, verify every item below exists and is complete:

| Directory / File | Required Content |
| :---- | :---- |
| **README.md** | Team members and roles, architecture diagram, setup instructions, link to live agent |
| **agent/** | AGENT.md, tools.yaml, all source files, requirements.txt |
| **kb/architecture/** | Claude Code 3-layer memory, autoDream, tool scoping. With CHANGELOG.md \+ injection test evidence |
| **kb/domain/** | DAB schema descriptions, join key glossary, domain term definitions |
| **kb/evaluation/** | DAB query format, scoring method, four failure categories |
| **kb/corrections/** | Running structured failure log with \[query\] → \[error\] → \[fix\] entries |
| **eval/** | Harness source, score\_log.csv (2+ data points), held-out test set |
| **probes/probes.md** | 15+ adversarial probes, 3+ failure categories, fix documentation |
| **planning/** | AI-DLC Inception document(s), mob session approval log, Operations document |
| **utils/** | 3+ reusable modules with README, usage examples, and tests |
| **signal/** | engagement\_log.md, article text files, community participation log |
| **results/** | DAB results JSON, PR link, harness score log, leaderboard screenshot |

## **Submission Deadlines**

| Deadline | What is due |
| :---- | :---- |
| **Wednesday Apr 15 — 21:00 UTC** | GitHub repo \+ PDF report. Infrastructure, core agent, KB v1+v2, evaluation harness baseline, Signal Corps Week 8 posts |
| **Saturday Apr 18 — 21:00 UTC** | GitHub repo \+ PDF report \+ Demo Video. Everything from Wednesday plus adversarial probes, benchmark PR, KB v3, published articles, engagement portfolio |

## **Demo Video Requirements (max 8 minutes)**

* Live demo of agent on shared server answering at least 2 DAB queries spanning different database types

* Self-correction loop: a query that fails, the agent diagnosing and recovering in real time

* Context layers in action: agent using KB institutional knowledge to resolve an ambiguous term or ill-formatted join key

* Evaluation harness producing a score with query trace on screen

* Brief walkthrough of adversarial probe library and how a probe led to a fix

* Host on YouTube (unlisted is fine) or public Google Drive. No login required to view.

| TRP1 FDE Programme · Tenacious Intelligence Corp · April 2026 The Oracle Forge · Driver Execution Guide |
| :---: |

