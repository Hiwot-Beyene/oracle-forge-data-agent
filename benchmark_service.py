from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eval.challenge_contract import append_contract_jsonl, build_challenge_contract
from eval.scorer import load_validate_fn, score_answer


def _writable_under_app_results(app_root: Path, filename: str) -> Path:
    """Prefer ``results/``; fall back to ``var/benchmark_outputs`` if not writable."""
    for base in (app_root / "results", app_root / "var" / "benchmark_outputs"):
        try:
            base.mkdir(parents=True, exist_ok=True)
            probe = base / ".write_probe"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return base / filename
        except OSError:
            continue
    return app_root / filename

UNAVAILABLE_ANSWER = "UNAVAILABLE: insufficient evidence from available tools/data."


@dataclass(frozen=True)
class BenchmarkQuery:
    dataset_slug: str
    dataset_dir: str
    query_name: str
    query_number: int
    question: str
    query_dir: Path


class BenchmarkService:
    def __init__(self, dab_root: Path, app_root: Path) -> None:
        self.dab_root = dab_root
        self.app_root = app_root
        self.results_dir = app_root / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.rows_log = self.results_dir / "benchmark_submission_rows.jsonl"
        self.ops_log = self.results_dir / "benchmark_ops_log.jsonl"
        self.debug_log = self.results_dir / "benchmark_debug.log"
        self._validate_fn = load_validate_fn(dab_root)

    def discover_catalog(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for dataset_path in sorted(self.dab_root.glob("query_*")):
            if not dataset_path.is_dir():
                continue
            queries = self._discover_queries_for_dataset(dataset_path.name)
            if not queries:
                continue
            out.append(
                {
                    "dataset_slug": dataset_path.name.replace("query_", "", 1),
                    "dataset_dir": dataset_path.name,
                    "query_count": len(queries),
                    "queries": [
                        {
                            "query_name": q.query_name,
                            "query_number": q.query_number,
                            "question": q.question,
                        }
                        for q in queries
                    ],
                }
            )
        return out

    def _discover_queries_for_dataset(self, dataset_dir: str) -> list[BenchmarkQuery]:
        base = self.dab_root / dataset_dir
        slug = dataset_dir.replace("query_", "", 1)
        rows: list[BenchmarkQuery] = []
        for qdir in sorted(base.glob("query*")):
            if not qdir.is_dir() or not qdir.name.startswith("query"):
                continue
            tail = qdir.name[5:]
            if not tail.isdigit():
                continue
            query_json = qdir / "query.json"
            if not query_json.is_file():
                continue
            question = ""
            try:
                raw = json.loads(query_json.read_text(encoding="utf-8"))
                if isinstance(raw, str):
                    question = raw
                elif isinstance(raw, dict):
                    question = str(raw.get("query") or raw.get("question") or "").strip()
                else:
                    question = str(raw).strip()
            except json.JSONDecodeError:
                question = query_json.read_text(encoding="utf-8").strip()
            rows.append(
                BenchmarkQuery(
                    dataset_slug=slug,
                    dataset_dir=dataset_dir,
                    query_name=qdir.name,
                    query_number=int(tail),
                    question=question,
                    query_dir=qdir.resolve(),
                )
            )
        return rows

    def _write_challenge_contract_if_enabled(
        self,
        final_path: Path,
        query: BenchmarkQuery,
        run_name: str,
        *,
        validation_is_valid: bool | None = None,
    ) -> None:
        flag = (os.getenv("BENCHMARK_WRITE_CONTRACT") or "").strip().lower()
        if flag not in ("1", "true", "yes"):
            return
        try:
            contract = build_challenge_contract(
                final_path,
                extra={
                    "dataset": query.dataset_slug,
                    "query_id": str(query.query_number),
                    "run_name": run_name,
                    "source": "benchmark_service.run_single_trial",
                },
                validation_is_valid=validation_is_valid,
            )
            out = _writable_under_app_results(self.app_root, "challenge_contracts.jsonl")
            append_contract_jsonl(contract, out)
        except Exception as exc:  # noqa: BLE001
            self._append_debug(
                {
                    "event": "challenge_contract_write_failed",
                    "error": str(exc),
                    "final_agent": str(final_path),
                }
            )

    def get_query(self, dataset_slug: str, query_number: int) -> BenchmarkQuery | None:
        dataset_dir = f"query_{dataset_slug}"
        for q in self._discover_queries_for_dataset(dataset_dir):
            if q.query_number == query_number:
                return q
        return None

    def next_run_index(self, query: BenchmarkQuery) -> int:
        run_root = (query.query_dir / "logs" / "data_agent").resolve()
        run_root.mkdir(parents=True, exist_ok=True)
        max_seen = -1
        for p in run_root.iterdir():
            if not p.is_dir():
                continue
            m = re.fullmatch(r"run_(\d+)", p.name)
            if not m:
                continue
            max_seen = max(max_seen, int(m.group(1)))
        return max_seen + 1

    def run_single_trial(
        self,
        query: BenchmarkQuery,
        *,
        llm: str,
        iterations: int,
        use_hints: bool = True,
    ) -> dict[str, Any]:
        print(
            f"[benchmark-service] run_single_trial start "
            f"dataset={query.dataset_slug} query={query.query_number} llm={llm} iterations={iterations}"
        )
        stages = self._init_stages()
        stages["SelectQuery"] = "success"
        stages["AllocateRun"] = "running"
        run_idx = self.next_run_index(query)
        run_name = f"run_{run_idx}"
        trace_root = (query.query_dir / "logs" / "data_agent" / run_name).resolve()
        stages["AllocateRun"] = "success"

        stages["ExecuteAgent"] = "running"
        eff_iterations = max(1, int(iterations))
        if query.dataset_slug == "yelp" and eff_iterations < 72:
            prev = eff_iterations
            eff_iterations = 72
            print(
                "[benchmark-service] Yelp needs many tool rounds (query_db + execute_python); "
                f"raising iterations from {prev} to {eff_iterations} (UI requested={iterations})."
            )
        cmd = [
            sys.executable,
            str(self.dab_root / "run_agent.py"),
            "--dataset",
            query.dataset_slug,
            "--query_id",
            str(query.query_number),
            "--llm",
            llm,
            "--iterations",
            str(eff_iterations),
            "--root_name",
            run_name,
        ]
        if use_hints:
            cmd.append("--use_hints")
        print(
            f"[benchmark-service] selected dataset={query.dataset_slug} query={query.query_number} "
            f"run_index={run_idx} run_name={run_name}"
        )
        print(
            "[benchmark-service] execute command="
            + " ".join(cmd)
        )
        run_env = os.environ.copy()
        # Ensure Oracle Forge KB loads (agent/context_loader.py); cwd alone is not enough.
        run_env["ORACLE_FORGE_ROOT"] = str(self.app_root.resolve())
        # Stream child output to disk — capture_output=True buffers unbounded stdout/stderr in RAM
        # and can OOM-kill the Flask/UI process on long runs (ERR_EMPTY_RESPONSE in the browser).
        trace_root.mkdir(parents=True, exist_ok=True)
        console_log = trace_root / "run_agent_console.log"
        with console_log.open("w", encoding="utf-8", errors="replace") as logf:
            proc = subprocess.run(
                cmd,
                cwd=str(self.dab_root),
                env=run_env,
                stdout=logf,
                stderr=subprocess.STDOUT,
                check=False,
            )
        log_tail = ""
        try:
            log_tail = console_log.read_text(encoding="utf-8", errors="replace")[-1200:]
        except OSError:
            pass
        self._append_debug(
            {
                "event": "run_agent_completed",
                "dataset": query.dataset_slug,
                "query": query.query_number,
                "run_name": run_name,
                "llm": llm,
                "iterations": eff_iterations,
                "iterations_requested": iterations,
                "command": cmd,
                "exit_code": proc.returncode,
                "console_log": str(console_log),
                "log_tail": log_tail,
            }
        )
        if proc.returncode != 0:
            stages["ExecuteAgent"] = "failed"
            print(
                f"[benchmark-service] run_agent failed "
                f"dataset={query.dataset_slug} query={query.query_number} run={run_name} "
                f"exit_code={proc.returncode}"
            )
            err = (log_tail.strip() or f"run_agent failed (exit {proc.returncode}); see {console_log}")
            bundle_dir = self._persist_forge_trial_bundle(
                query,
                run_idx,
                run_name,
                trace_root if trace_root.is_dir() else None,
                stages=stages,
                ok=False,
                error=err,
                extras={"run_agent_exit_code": proc.returncode},
            )
            return {
                "ok": False,
                "run_index": run_idx,
                "run_name": run_name,
                "stages": stages,
                "error": err,
                "forge_results_dir": str(bundle_dir),
            }
        stages["ExecuteAgent"] = "success"

        final_path = (query.query_dir / "logs" / "data_agent" / run_name / "final_agent.json").resolve()
        routing_trace = self._collect_routing_trace(final_path.parent)
        if not final_path.is_file():
            stages["ValidateAnswer"] = "failed"
            print(
                f"[benchmark-service] missing final_agent "
                f"dataset={query.dataset_slug} query={query.query_number} run={run_name}"
            )
            err = f"Missing final_agent.json at {final_path}"
            bundle_dir = self._persist_forge_trial_bundle(
                query,
                run_idx,
                run_name,
                final_path.parent if final_path.parent.is_dir() else None,
                stages=stages,
                ok=False,
                error=err,
                extras={"routing_trace": routing_trace},
            )
            return {
                "ok": False,
                "run_index": run_idx,
                "run_name": run_name,
                "stages": stages,
                "error": err,
                "routing_trace": routing_trace,
                "forge_results_dir": str(bundle_dir),
            }

        stages["ValidateAnswer"] = "running"
        data = json.loads(final_path.read_text(encoding="utf-8"))
        kb_diag = self._read_kb_diagnostics(data)
        evidence_diag = self._collect_evidence_summary(final_path.parent)
        raw_answer = (data.get("final_result") or "").strip()
        answer, answer_diag = self._normalize_answer_for_submission(raw_answer)
        terminate_reason = str(data.get("terminate_reason") or "")
        llm_diag = self._read_llm_diagnostics(final_path.parent / "llm_calls.jsonl")
        unsupported = self._is_unsupported_answer(answer, answer_diag, evidence_diag)
        if unsupported:
            answer = UNAVAILABLE_ANSWER
            answer_diag["forced_unavailable"] = True
            answer_diag["unsupported_reason"] = unsupported
        answer_status = self._answer_status(answer, answer_diag)
        if answer_diag.get("is_tool_call_payload"):
            stages["ValidateAnswer"] = "failed"
            detail = (
                "Model returned a tool-call payload as plain text (not a final answer). "
                f"terminate_reason={terminate_reason}. "
                f"LLM diagnostics: {llm_diag.get('summary', 'n/a')}. "
                f"See debug log: {self.debug_log}"
            )
            self._append_debug(
                {
                    "event": "run_rejected_tool_payload_answer",
                    "dataset": query.dataset_slug,
                    "query": query.query_number,
                    "run_name": run_name,
                    "terminate_reason": terminate_reason,
                    "raw_answer_preview": raw_answer[:600],
                    "answer_diagnostics": answer_diag,
                    "llm_diagnostics": llm_diag,
                    "routing_trace": routing_trace,
                    "final_agent": str(final_path),
                }
            )
            print(
                f"[benchmark-service] rejected tool payload answer "
                f"dataset={query.dataset_slug} query={query.query_number} run={run_name}"
            )
            self._write_challenge_contract_if_enabled(final_path, query, run_name, validation_is_valid=None)
            bundle_dir = self._persist_forge_trial_bundle(
                query,
                run_idx,
                run_name,
                final_path.parent,
                stages=stages,
                ok=False,
                error=detail,
                extras={
                    "diagnostics": llm_diag,
                    "routing_trace": routing_trace,
                    "kb_context": kb_diag,
                    "evidence": evidence_diag,
                    "answer_diagnostics": answer_diag,
                    "terminate_reason": terminate_reason,
                    "raw_answer_preview": raw_answer[:1200],
                },
            )
            return {
                "ok": False,
                "run_index": run_idx,
                "run_name": run_name,
                "stages": stages,
                "error": detail,
                "diagnostics": llm_diag,
                "routing_trace": routing_trace,
                "kb_context": kb_diag,
                "evidence": evidence_diag,
                "forge_results_dir": str(bundle_dir),
            }
        if answer_diag.get("is_placeholder_answer"):
            stages["ValidateAnswer"] = "failed"
            detail = (
                f"Answer looks like placeholder text ({answer!r}); rejecting this trial. "
                f"terminate_reason={terminate_reason}. "
                f"LLM diagnostics: {llm_diag.get('summary', 'n/a')}."
            )
            self._append_debug(
                {
                    "event": "run_rejected_placeholder_answer",
                    "dataset": query.dataset_slug,
                    "query": query.query_number,
                    "run_name": run_name,
                    "terminate_reason": terminate_reason,
                    "raw_answer_preview": raw_answer[:600],
                    "answer_diagnostics": answer_diag,
                    "llm_diagnostics": llm_diag,
                    "routing_trace": routing_trace,
                    "final_agent": str(final_path),
                }
            )
            self._write_challenge_contract_if_enabled(final_path, query, run_name, validation_is_valid=None)
            bundle_dir = self._persist_forge_trial_bundle(
                query,
                run_idx,
                run_name,
                final_path.parent,
                stages=stages,
                ok=False,
                error=detail,
                extras={
                    "diagnostics": llm_diag,
                    "routing_trace": routing_trace,
                    "kb_context": kb_diag,
                    "evidence": evidence_diag,
                    "answer_diagnostics": answer_diag,
                    "terminate_reason": terminate_reason,
                    "raw_answer_preview": raw_answer[:1200],
                },
            )
            return {
                "ok": False,
                "run_index": run_idx,
                "run_name": run_name,
                "stages": stages,
                "error": detail,
                "diagnostics": llm_diag,
                "routing_trace": routing_trace,
                "kb_context": kb_diag,
                "evidence": evidence_diag,
                "forge_results_dir": str(bundle_dir),
            }

        if not answer and terminate_reason in {"no_tool_call", "llm_empty_or_malformed_response", "return_answer"}:
            stages["ValidateAnswer"] = "failed"
            detail = (
                f"Empty answer with terminate_reason={terminate_reason}. "
                f"LLM diagnostics: {llm_diag.get('summary', 'n/a')}. "
                f"See debug log: {self.debug_log}"
            )
            self._append_debug(
                {
                    "event": "run_rejected_empty_answer",
                    "dataset": query.dataset_slug,
                    "query": query.query_number,
                    "run_name": run_name,
                    "terminate_reason": terminate_reason,
                    "llm_diagnostics": llm_diag,
                    "routing_trace": routing_trace,
                    "final_agent": str(final_path),
                }
            )
            print(
                f"[benchmark-service] rejected empty answer "
                f"dataset={query.dataset_slug} query={query.query_number} run={run_name} "
                f"terminate_reason={terminate_reason} diag={llm_diag.get('summary')}"
            )
            self._write_challenge_contract_if_enabled(final_path, query, run_name, validation_is_valid=None)
            bundle_dir = self._persist_forge_trial_bundle(
                query,
                run_idx,
                run_name,
                final_path.parent,
                stages=stages,
                ok=False,
                error=detail,
                extras={
                    "diagnostics": llm_diag,
                    "routing_trace": routing_trace,
                    "kb_context": kb_diag,
                    "evidence": evidence_diag,
                    "terminate_reason": terminate_reason,
                },
            )
            return {
                "ok": False,
                "run_index": run_idx,
                "run_name": run_name,
                "stages": stages,
                "error": detail,
                "diagnostics": llm_diag,
                "routing_trace": routing_trace,
                "kb_context": kb_diag,
                "evidence": evidence_diag,
                "forge_results_dir": str(bundle_dir),
            }
        vr = score_answer(self._validate_fn, query.query_dir, answer)
        stages["ValidateAnswer"] = "success"

        stages["SaveRow"] = "running"
        row = {
            "dataset": query.dataset_slug,
            "query": str(query.query_number),
            "run": run_idx,
            "run_name": run_name,
            "answer": answer,
        }
        ops = {
            **row,
            "trace_dir": str(final_path.parent),
            "raw_answer": raw_answer,
            "is_valid": bool(vr.get("is_valid")),
            "validate_reason": vr.get("reason"),
            "final_agent": str(final_path),
            "terminate_reason": terminate_reason,
            "duration": data.get("duration"),
            "llm_diagnostics": llm_diag,
            "answer_diagnostics": answer_diag,
            "routing_trace": routing_trace,
            "kb_context": kb_diag,
            "evidence": evidence_diag,
            "answer_status": answer_status,
        }
        bundle_dir = self._persist_forge_trial_bundle(
            query,
            run_idx,
            run_name,
            final_path.parent,
            stages=stages,
            ok=True,
            error=None,
            row=row,
            ops=ops,
        )
        ops["forge_results_dir"] = str(bundle_dir)
        self._append_jsonl(self.rows_log, row)
        self._append_jsonl(self.ops_log, ops)
        self._append_debug(
            {
                "event": "trial_routing_trace",
                "dataset": query.dataset_slug,
                "query": query.query_number,
                "run_name": run_name,
                "routing_trace": routing_trace,
                "is_valid": bool(vr.get("is_valid")),
            }
        )
        self._write_challenge_contract_if_enabled(
            final_path,
            query,
            run_name,
            validation_is_valid=bool(vr.get("is_valid")),
        )
        stages["SaveRow"] = "success"
        print(
            f"[benchmark-service] run_single_trial ok "
            f"dataset={query.dataset_slug} query={query.query_number} run={run_name} "
            f"is_valid={ops['is_valid']} answer_status={answer_status} "
            f"kb_loaded={kb_diag.get('kb_context_loaded')} terminate_reason={terminate_reason}"
        )
        return {
            "ok": True,
            "run_index": run_idx,
            "run_name": run_name,
            "stages": stages,
            "row": row,
            "ops": ops,
            "routing_trace": routing_trace,
            "kb_context": kb_diag,
            "evidence": evidence_diag,
            "answer_status": answer_status,
            "forge_results_dir": str(bundle_dir),
        }

    def run_one_best_of_k(
        self,
        query: BenchmarkQuery,
        *,
        llm: str,
        iterations: int,
        use_hints: bool = True,
        k: int = 3,
    ) -> dict[str, Any]:
        trials = max(1, int(k))
        results: list[dict[str, Any]] = []
        for _ in range(trials):
            item = self.run_single_trial(query, llm=llm, iterations=iterations, use_hints=use_hints)
            results.append(item)
            if bool(((item.get("ops") or {}).get("is_valid"))):
                break
        best_trial = self._select_best_trial(results)
        best_result = next((r for r in results if r.get("run_name") == (best_trial or {}).get("run_name")), results[-1] if results else None)
        self._append_debug(
            {
                "event": "run_one_best_of_k",
                "dataset": query.dataset_slug,
                "query": query.query_number,
                "k": trials,
                "attempted_trials": len(results),
                "best_trial": best_trial,
            }
        )
        return {
            "attempted_trials": len(results),
            "results": results,
            "best_trial": best_trial,
            "best_result": best_result,
        }

    def run_until_target(
        self,
        query: BenchmarkQuery,
        *,
        target_trials: int,
        llm: str,
        iterations: int,
        use_hints: bool = True,
    ) -> dict[str, Any]:
        if target_trials < 1:
            target_trials = 1
        completed = self._count_run_dirs(query)
        remaining = max(0, target_trials - completed)
        print(
            f"[benchmark-service] run_until_target start "
            f"dataset={query.dataset_slug} query={query.query_number} completed={completed} "
            f"target={target_trials} remaining={remaining}"
        )
        results = []
        while completed < target_trials:
            item = self.run_single_trial(query, llm=llm, iterations=iterations, use_hints=use_hints)
            results.append(item)
            # Strict benchmark-safe policy: keep running trials even if one attempt fails.
            completed += 1
        best_trial = self._select_best_trial(results)
        self._append_debug(
            {
                "event": "run_until_best_trial",
                "dataset": query.dataset_slug,
                "query": query.query_number,
                "target_trials": target_trials,
                "attempted_trials": len(results),
                "best_trial": best_trial,
            }
        )
        print(
            f"[benchmark-service] run_until_target end "
            f"dataset={query.dataset_slug} query={query.query_number} completed={completed} target={target_trials}"
        )
        return {
            "completed_runs": completed,
            "target_trials": target_trials,
            "attempted_trials": len(results),
            "results": results,
            "best_trial": best_trial,
        }

    def export_submission_json(self) -> dict[str, Any]:
        rows = self._read_rows_latest_unique()
        rows_sorted = sorted(rows, key=lambda r: (r["dataset"], int(r["query"]), int(r["run"])))
        out_name = f"dab_submission_{self._timestamp_tag()}.json"
        out_path = self.results_dir / out_name
        out_path.write_text(json.dumps(rows_sorted, indent=2) + "\n", encoding="utf-8")

        coverage = self.compute_coverage(rows_sorted)
        print(f"[benchmark-service] export_submission_json rows={len(rows_sorted)} path={out_path}")
        return {"path": str(out_path), "rows": len(rows_sorted), "coverage": coverage}

    def compute_coverage(self, rows: list[dict[str, Any]] | None = None, target_trials: int = 5) -> dict[str, Any]:
        if rows is None:
            rows = self._read_rows_latest_unique()
        have: dict[tuple[str, int], set[int]] = {}
        for row in rows:
            key = (str(row["dataset"]), int(row["query"]))
            have.setdefault(key, set()).add(int(row["run"]))

        missing = []
        total_expected = 0
        total_present = 0
        for ds in self.discover_catalog():
            slug = ds["dataset_slug"]
            for q in ds["queries"]:
                qn = int(q["query_number"])
                seen = have.get((slug, qn), set())
                total_expected += target_trials
                total_present += len([x for x in seen if x < target_trials])
                needed = [i for i in range(target_trials) if i not in seen]
                if needed:
                    missing.append({"dataset": slug, "query": qn, "missing_runs": needed})
        return {
            "target_trials": target_trials,
            "total_expected_rows": total_expected,
            "total_present_rows": total_present,
            "missing_count": len(missing),
            "missing": missing,
        }

    def _read_rows_latest_unique(self) -> list[dict[str, Any]]:
        if not self.rows_log.is_file():
            return []
        rows = []
        for line in self.rows_log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        by_key: dict[tuple[str, str, int], dict[str, Any]] = {}
        for row in rows:
            key = (str(row["dataset"]), str(row["query"]), int(row["run"]))
            by_key[key] = {
                "dataset": str(row["dataset"]),
                "query": str(row["query"]),
                "run": int(row["run"]),
                "answer": str(row.get("answer", "")),
            }
        return list(by_key.values())

    def _normalize_answer_for_submission(self, answer: str) -> tuple[str, dict[str, Any]]:
        cleaned = (answer or "").strip()
        low = cleaned.lower()
        is_placeholder = low in {"none", "null", "nil", "n/a", "na", "unknown", "no answer"}
        diag = {
            "is_tool_call_payload": False,
            "was_fenced_json": False,
            "contains_tool_outputs_block": "tool_outputs" in low,
            "is_placeholder_answer": is_placeholder,
        }
        if cleaned.startswith("```"):
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
            if m:
                cleaned = m.group(1).strip()
                diag["was_fenced_json"] = True

        parsed: dict[str, Any] | None = None
        try:
            obj = json.loads(cleaned)
            if isinstance(obj, dict):
                parsed = obj
        except json.JSONDecodeError:
            # Accept leading JSON object even if followed by extra text.
            start = cleaned.find("{")
            if start != -1:
                try:
                    obj, _ = json.JSONDecoder().raw_decode(cleaned[start:])
                    if isinstance(obj, dict):
                        parsed = obj
                except json.JSONDecodeError:
                    parsed = None

        if (parsed and "tool" in parsed and "args" in parsed) or diag["contains_tool_outputs_block"]:
            diag["is_tool_call_payload"] = True
            return "", diag
        if is_placeholder:
            return "", diag
        return cleaned, diag

    def _forge_trial_dir(self, query: BenchmarkQuery, run_name: str) -> Path:
        """``results/<dataset_slug>/query<n>/<run_name>/`` (mirrors DAB ``run_k`` naming)."""
        base = (self.results_dir / query.dataset_slug / f"query{query.query_number}" / run_name).resolve()
        base.mkdir(parents=True, exist_ok=True)
        return base

    @staticmethod
    def _truncate_preview(val: Any, limit: int) -> Any:
        if val is None:
            return None
        s = val if isinstance(val, str) else json.dumps(val, default=str)
        if len(s) <= limit:
            return val if isinstance(val, str) else s
        return s[: limit - 3] + "..."

    def _summarize_llm_turn(self, row: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {
            "timestamp": row.get("timestamp"),
            "start_time": row.get("start_time"),
            "end_time": row.get("end_time"),
            "duration_sec": row.get("duration"),
            "model": row.get("model"),
        }
        resp = row.get("response") or {}
        choices = resp.get("choices") or []
        if choices:
            ch0 = choices[0] or {}
            out["finish_reason"] = ch0.get("finish_reason")
            out["native_finish_reason"] = ch0.get("native_finish_reason")
            msg = ch0.get("message") or {}
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                out["assistant_text_preview"] = self._truncate_preview(content, 800)
            planned: list[dict[str, Any]] = []
            for tc in msg.get("tool_calls") or []:
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function") or {}
                name = str(fn.get("name") or "")
                raw_args = fn.get("arguments")
                planned.append(
                    {
                        "name": name,
                        "arguments_preview": self._truncate_preview(raw_args, 1200),
                    }
                )
            if planned:
                out["planned_tools"] = planned
        return out

    def _summarize_tool_execution(self, row: dict[str, Any]) -> dict[str, Any]:
        tool_name = str(row.get("tool_name") or "")
        result = row.get("result") if isinstance(row.get("result"), dict) else {}
        preview = str((result or {}).get("preview") or "")
        out: dict[str, Any] = {
            "tool_name": tool_name,
            "wall_time_sec": row.get("time"),
            "start": row.get("start"),
            "end": row.get("end"),
            "success": bool((result or {}).get("success")) if isinstance(result, dict) else None,
            "result_preview": self._truncate_preview(preview, 1500),
        }
        args = row.get("args")
        if isinstance(args, dict):
            args_out = dict(args)
            if "code" in args_out:
                args_out["code"] = self._truncate_preview(str(args_out.get("code") or ""), 6000)
            if "query" in args_out:
                args_out["query"] = self._truncate_preview(str(args_out.get("query") or ""), 4000)
            out["args"] = args_out
        return out

    def _build_iteration_steps_from_trace(self, trace_dir: Path) -> list[dict[str, Any]]:
        llm_path = trace_dir / "llm_calls.jsonl"
        tool_path = trace_dir / "tool_calls.jsonl"
        llm_rows: list[dict[str, Any]] = []
        if llm_path.is_file():
            for line in llm_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    llm_rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        tool_rows: list[dict[str, Any]] = []
        if tool_path.is_file():
            for line in tool_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    tool_rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        n = max(len(llm_rows), len(tool_rows))
        steps: list[dict[str, Any]] = []
        for i in range(n):
            step: dict[str, Any] = {"iteration": i + 1}
            if i < len(llm_rows):
                step["llm_turn"] = self._summarize_llm_turn(llm_rows[i])
            if i < len(tool_rows):
                step["tool_execution"] = self._summarize_tool_execution(tool_rows[i])
            steps.append(step)
        return steps

    def _persist_forge_trial_bundle(
        self,
        query: BenchmarkQuery,
        run_idx: int,
        run_name: str,
        trace_dir: Path | None,
        *,
        stages: dict[str, str],
        ok: bool,
        error: str | None = None,
        row: dict[str, Any] | None = None,
        ops: dict[str, Any] | None = None,
        extras: dict[str, Any] | None = None,
    ) -> Path:
        bundle_dir = self._forge_trial_dir(query, run_name)
        dab_trace = None
        if trace_dir is not None and trace_dir.is_dir():
            dab_trace = str(trace_dir.resolve())
        ops_out = dict(ops) if ops else None
        if ops_out is not None:
            ops_out["forge_results_dir"] = str(bundle_dir)
        trial_payload: dict[str, Any] = {
            "forge_bundle_version": 1,
            "dataset": query.dataset_slug,
            "query": query.query_number,
            "query_dir": str(query.query_dir),
            "run_index": run_idx,
            "run_name": run_name,
            "ok": ok,
            "stages": dict(stages),
            "error": error,
            "dab_trace_dir": dab_trace,
            "forge_results_dir": str(bundle_dir),
            "row": row,
            "ops": ops_out,
        }
        if extras:
            trial_payload["extras"] = extras
        (bundle_dir / "trial.json").write_text(
            json.dumps(trial_payload, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        steps = self._build_iteration_steps_from_trace(trace_dir) if dab_trace else []
        with (bundle_dir / "iteration_steps.jsonl").open("w", encoding="utf-8") as f:
            for step in steps:
                f.write(json.dumps(step, default=str) + "\n")
        return bundle_dir

    def _read_llm_diagnostics(self, llm_log_path: Path) -> dict[str, Any]:
        if not llm_log_path.is_file():
            return {"summary": "llm_log_missing"}
        lines = [ln for ln in llm_log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if not lines:
            return {"summary": "llm_log_empty"}
        try:
            row = json.loads(lines[-1])
        except json.JSONDecodeError:
            return {"summary": "llm_log_invalid_json"}
        resp = row.get("response") or {}
        choices = resp.get("choices") or []
        if not choices:
            return {"summary": "no_choices", "response_model": resp.get("model")}
        ch0 = choices[0]
        native = ch0.get("native_finish_reason")
        finish = ch0.get("finish_reason")
        msg = ch0.get("message") or {}
        return {
            "summary": f"finish_reason={finish}, native_finish_reason={native}, content_is_null={msg.get('content') is None}",
            "finish_reason": finish,
            "native_finish_reason": native,
            "response_model": resp.get("model"),
        }

    def _collect_routing_trace(self, run_dir: Path) -> dict[str, Any]:
        out: dict[str, Any] = {
            "run_dir": str(run_dir),
            "tool_call_count": 0,
            "tool_sequence": [],
            "db_routes": [],
            "execute_python_failures": 0,
            "return_answer_count": 0,
            "llm_turns": 0,
            "malformed_function_call_turns": 0,
        }
        tool_path = run_dir / "tool_calls.jsonl"
        if tool_path.is_file():
            for line in tool_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tool_name = str(row.get("tool_name") or "")
                if not tool_name:
                    continue
                out["tool_call_count"] += 1
                out["tool_sequence"].append(tool_name)
                if tool_name == "execute_python":
                    res = row.get("result") or {}
                    if isinstance(res, dict) and not bool(res.get("success")):
                        out["execute_python_failures"] += 1
                if tool_name == "return_answer":
                    out["return_answer_count"] += 1
                args = row.get("args") or {}
                val_args = row.get("val_args") or {}
                db_name = args.get("db_name") if isinstance(args, dict) else None
                db_type = val_args.get("db_type") if isinstance(val_args, dict) else None
                query_text = args.get("query") if isinstance(args, dict) else None
                if db_name:
                    out["db_routes"].append(
                        {
                            "tool": tool_name,
                            "db_name": str(db_name),
                            "db_type": str(db_type or ""),
                            "query_preview": str(query_text or "")[:180],
                        }
                    )
        llm_path = run_dir / "llm_calls.jsonl"
        if llm_path.is_file():
            for line in llm_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                out["llm_turns"] += 1
                resp = row.get("response") or {}
                choices = resp.get("choices") or []
                if choices:
                    native = str((choices[0] or {}).get("native_finish_reason") or "")
                    if native.upper() == "MALFORMED_FUNCTION_CALL":
                        out["malformed_function_call_turns"] += 1
        return out

    def _collect_evidence_summary(self, run_dir: Path) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "query_db_calls": 0,
            "query_db_success_calls": 0,
            "query_db_nonempty_results": 0,
            "query_db_empty_results": 0,
            "query_db_error_results": 0,
            "execute_python_calls": 0,
            "execute_python_success_calls": 0,
            "execute_python_nonempty_results": 0,
            "execute_python_error_results": 0,
        }
        tool_path = run_dir / "tool_calls.jsonl"
        if not tool_path.is_file():
            return summary
        for line in tool_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            tname = str(row.get("tool_name") or "")
            if tname == "query_db":
                summary["query_db_calls"] += 1
                result = row.get("result") or {}
                ok = bool(result.get("success")) if isinstance(result, dict) else False
                if ok:
                    summary["query_db_success_calls"] += 1
                preview = str((result or {}).get("preview") or "")
                if not ok:
                    summary["query_db_error_results"] += 1
                elif preview in {"[]", "{}", "", "null"}:
                    summary["query_db_empty_results"] += 1
                else:
                    summary["query_db_nonempty_results"] += 1
            elif tname == "execute_python":
                summary["execute_python_calls"] += 1
                result = row.get("result") or {}
                ok = bool(result.get("success")) if isinstance(result, dict) else False
                preview = str((result or {}).get("preview") or "")
                if not ok:
                    summary["execute_python_error_results"] += 1
                    continue
                summary["execute_python_success_calls"] += 1
                if preview in {"[]", "{}", "", "null"} or not preview.strip():
                    continue
                summary["execute_python_nonempty_results"] += 1
        return summary

    def _read_kb_diagnostics(self, final_agent: dict[str, Any]) -> dict[str, Any]:
        md = (final_agent.get("runtime_metadata") or {}).get("kb_context") or {}
        if isinstance(md, dict):
            return {
                "dataset": md.get("dataset"),
                "kb_context_loaded": bool(md.get("kb_context_loaded")),
                "kb_context_marker_present": bool(md.get("kb_context_marker_present")),
                "kb_context_chars": int(md.get("kb_context_chars") or 0),
            }
        return {
            "dataset": None,
            "kb_context_loaded": False,
            "kb_context_marker_present": False,
            "kb_context_chars": 0,
        }

    def _is_unsupported_answer(
        self,
        answer: str,
        answer_diag: dict[str, Any],
        evidence_diag: dict[str, Any],
    ) -> str | None:
        if answer_diag.get("is_placeholder_answer"):
            return "placeholder_answer"
        if not answer.strip():
            return "empty_answer"
        if answer.upper().startswith("UNAVAILABLE:"):
            return None
        q_ok = int(evidence_diag.get("query_db_success_calls", 0) or 0)
        q_ne = int(evidence_diag.get("query_db_nonempty_results", 0) or 0)
        py_ok = int(evidence_diag.get("execute_python_success_calls", 0) or 0)
        py_ne = int(evidence_diag.get("execute_python_nonempty_results", 0) or 0)
        if q_ok == 0 and py_ok == 0:
            return "no_successful_query_db_or_execute_python"
        if q_ne == 0 and py_ne == 0:
            return "no_nonempty_results_from_query_db_or_execute_python"
        speculative_markers = ("probably", "likely", "might", "guess", "assume", "maybe")
        low = answer.lower()
        if any(tok in low for tok in speculative_markers):
            return "speculative_language_detected"
        return None

    def _answer_status(self, answer: str, answer_diag: dict[str, Any]) -> str:
        if answer_diag.get("forced_unavailable") or answer.upper().startswith("UNAVAILABLE:"):
            return "unavailable_insufficient_evidence"
        if not answer.strip():
            return "empty"
        return "answered"

    def _select_best_trial(self, results: list[dict[str, Any]]) -> dict[str, Any] | None:
        candidates = [r for r in results if isinstance(r, dict)]
        if not candidates:
            return None
        valid = [r for r in candidates if bool(((r.get("ops") or {}).get("is_valid")))]
        pool = valid if valid else candidates
        pool.sort(
            key=lambda r: (
                0 if bool((r.get("ops") or {}).get("is_valid")) else 1,
                0 if bool(r.get("ok")) else 1,
                float((r.get("ops") or {}).get("duration") or 1e12),
                int(r.get("run_index") or 1e9),
            )
        )
        top = pool[0]
        return {
            "run_name": top.get("run_name"),
            "run_index": top.get("run_index"),
            "ok": bool(top.get("ok")),
            "is_valid": bool((top.get("ops") or {}).get("is_valid")),
            "answer": (top.get("row") or {}).get("answer"),
            "validate_reason": (top.get("ops") or {}).get("validate_reason"),
            "terminate_reason": (top.get("ops") or {}).get("terminate_reason"),
            "routing_trace": top.get("routing_trace"),
        }

    def _count_run_dirs(self, query: BenchmarkQuery) -> int:
        run_root = (query.query_dir / "logs" / "data_agent").resolve()
        if not run_root.is_dir():
            return 0
        n = 0
        for p in run_root.iterdir():
            if p.is_dir() and re.fullmatch(r"run_(\d+)", p.name):
                n += 1
        return n

    @staticmethod
    def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def _append_debug(self, row: dict[str, Any]) -> None:
        row_out = {"ts": self._timestamp_tag(), **row}
        self.debug_log.parent.mkdir(parents=True, exist_ok=True)
        with self.debug_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row_out) + "\n")

    @staticmethod
    def _timestamp_tag() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    @staticmethod
    def _init_stages() -> dict[str, str]:
        return {
            "SelectQuery": "pending",
            "AllocateRun": "pending",
            "ExecuteAgent": "pending",
            "ValidateAnswer": "pending",
            "SaveRow": "pending",
        }

