#!/usr/bin/env python3
"""Standalone latency and resilience measurement CLI for GridWise preliminary.

Measures p50, p90, p95, p99 over >= 20 calls against a target service,
cycling through public sample cases, reporting cold-start explicitly,
tracking failures (non-200, timeout, malformed body), and evaluating
against rubric latency bands.

Usage:
    python tests/latency.py --url <base> [--n 30] [--concurrency 1] [--cases tests/fixtures/public_cases.json] [--json out.json] [--timeout 30]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import pathlib
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PERCENTILE_METHOD_DESC = (
    "Linear interpolation between closest ranks (k = (n - 1) * p, "
    "Hyndman-Fan Type 7 / NumPy linear default, identical to tests/harness.py)"
)

SUPPORTED_DIRECTIVE_TYPES = (
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
)

REQUIRED_TOP_LEVEL_FIELDS = (
    "scenario_id",
    "directive_interpretation",
    "hourly_plan",
    "total_grid_kwh",
    "total_cost_bdt",
    "peak_grid_kwh",
    "plan_summary",
)

REQUIRED_INTERPRETATION_FIELDS = (
    "note_index",
    "applies",
    "directive_type",
    "structured_adjustment",
    "explanation",
)

REQUIRED_PLAN_FIELDS = (
    "hour",
    "grid_kwh",
    "solar_used_kwh",
    "battery_action",
    "battery_kwh",
    "battery_energy_after_kwh",
)


def discover_optimize_route(routes_dir: pathlib.Path | None = None) -> tuple[str, bool]:
    """Read backend/routes/ (READ-ONLY) to find the declared optimize endpoint.

    Defaults to spec-mandated /optimize-energy (problem.md section 15).
    """
    if routes_dir is None:
        routes_dir = ROOT / "backend" / "routes"

    if routes_dir.is_dir():
        for p in routes_dir.glob("*.py"):
            try:
                content = p.read_text(encoding="utf-8")
                matches = re.findall(r'@\w+\.post\s*\(\s*["\']([^"\']+)["\']', content)
                for m in matches:
                    if "optimize" in m:
                        return m, True
            except Exception:
                continue

    return "/optimize-energy", False


def check_body_well_formed(
    body: Any, scenario_id: str, expected_note_count: int
) -> tuple[bool, str | None]:
    """Verify that a 200 response body strictly conforms to the expected contract."""
    if not isinstance(body, dict):
        return False, "Response body is not a JSON object"

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in body:
            return False, f"Missing top-level field '{field}'"

    if body.get("scenario_id") != scenario_id:
        return (
            False,
            f"scenario_id '{body.get('scenario_id')}' does not match expected '{scenario_id}'",
        )

    for num_field in ("total_grid_kwh", "total_cost_bdt", "peak_grid_kwh"):
        val = body.get(num_field)
        if not isinstance(val, (int, float)) or isinstance(val, bool) or not math.isfinite(val):
            return False, f"Top-level field '{num_field}' is not a finite number ({val!r})"

    dirs = body.get("directive_interpretation")
    if not isinstance(dirs, list):
        return False, "directive_interpretation is not a list"
    if len(dirs) != expected_note_count:
        return (
            False,
            f"directive_interpretation length {len(dirs)} != expected {expected_note_count}",
        )

    for i, d in enumerate(dirs):
        if not isinstance(d, dict):
            return False, f"directive_interpretation[{i}] is not a dict"
        for k in REQUIRED_INTERPRETATION_FIELDS:
            if k not in d:
                return False, f"directive_interpretation[{i}] missing field '{k}'"

        idx = d.get("note_index")
        if not isinstance(idx, int) or isinstance(idx, bool):
            return False, f"directive_interpretation[{i}].note_index must be integer"

        applies = d.get("applies")
        if not isinstance(applies, bool):
            return False, f"directive_interpretation[{i}].applies must be boolean"

        dtype = d.get("directive_type")
        if dtype not in SUPPORTED_DIRECTIVE_TYPES:
            return False, f"directive_interpretation[{i}] unsupported type '{dtype}'"

        adj = d.get("structured_adjustment")
        # Hard invariant: no_op <=> applies is False <=> structured_adjustment is None
        if dtype == "no_op":
            if applies is not False:
                return False, f"directive_interpretation[{i}]: no_op requires applies=false"
            if adj is not None:
                return False, f"directive_interpretation[{i}]: no_op requires adjustment=null"
        else:
            if applies is not True:
                return False, f"directive_interpretation[{i}]: {dtype} requires applies=true"
            if not isinstance(adj, dict):
                return False, f"directive_interpretation[{i}]: {dtype} requires adjustment dict"

    plan = body.get("hourly_plan")
    if not isinstance(plan, list) or len(plan) != 24:
        return False, f"hourly_plan must be a list of exactly 24 entries (got {type(plan)})"

    for i, p in enumerate(plan):
        if not isinstance(p, dict):
            return False, f"hourly_plan[{i}] is not an object"
        for k in REQUIRED_PLAN_FIELDS:
            if k not in p:
                return False, f"hourly_plan[{i}] missing field '{k}'"
        if p.get("hour") != i:
            return False, f"hourly_plan[{i}].hour {p.get('hour')} != {i}"
        if p.get("battery_action") not in ("charge", "discharge", "idle"):
            return False, f"hourly_plan[{i}] invalid battery_action '{p.get('battery_action')}'"
        for num_k in ("grid_kwh", "solar_used_kwh", "battery_kwh", "battery_energy_after_kwh"):
            v = p.get(num_k)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
                return False, f"hourly_plan[{i}].{num_k} is not a finite number"

    return True, None


def make_call(
    url: str, payload: dict, timeout: float = 30.0
) -> dict[str, Any]:
    """Issues one HTTP POST request using urllib.request.

    Returns dict containing status, latency, error details, and failure categorization.
    Never raises an unhandled exception.
    """
    req_body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    t0 = time.perf_counter()
    status_code: int | None = None
    body: dict | None = None
    is_timeout = False
    is_non_200 = False
    is_malformed = False
    error_msg: str | None = None
    well_formed = False

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = time.perf_counter() - t0
            status_code = resp.status
            raw = resp.read().decode("utf-8")

            if latency >= timeout:
                is_timeout = True
                error_msg = f"Response wall-clock time exceeded timeout ceiling ({latency:.3f}s >= {timeout}s)"
            else:
                try:
                    body = json.loads(raw)
                except Exception as e:
                    is_malformed = True
                    error_msg = f"HTTP 200 returned invalid JSON: {e}"

                if body is not None:
                    scenario_id = payload.get("scenario_id", "")
                    note_count = len(payload.get("operator_notes", []))
                    ok, mal_reason = check_body_well_formed(body, scenario_id, note_count)
                    if ok:
                        well_formed = True
                    else:
                        is_malformed = True
                        error_msg = mal_reason

    except urllib.error.HTTPError as e:
        latency = time.perf_counter() - t0
        status_code = e.code
        is_non_200 = True
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        error_msg = f"HTTP {e.code}: {raw[:150]}"
    except urllib.error.URLError as e:
        latency = time.perf_counter() - t0
        if isinstance(e.reason, (socket.timeout, TimeoutError)) or "timed out" in str(e.reason).lower():
            is_timeout = True
            error_msg = f"Request timed out after {latency:.3f}s: {e.reason}"
        else:
            error_msg = f"URL error: {e.reason}"
    except (socket.timeout, TimeoutError):
        latency = time.perf_counter() - t0
        is_timeout = True
        error_msg = f"Connection timed out after {latency:.3f}s"
    except Exception as e:
        latency = time.perf_counter() - t0
        error_msg = f"Request failed: {e}"

    if status_code is not None and status_code != 200:
        is_non_200 = True

    return {
        "status_code": status_code,
        "latency_sec": latency,
        "body": body,
        "is_timeout": is_timeout,
        "is_non_200": is_non_200,
        "is_malformed": is_malformed,
        "well_formed": well_formed,
        "error_msg": error_msg,
    }


def compute_percentile(sorted_sample: list[float], p: float) -> float:
    """Linear interpolation between closest ranks (k = (n - 1) * p).

    Identical to tests/harness.py compute_latency_stats implementation.
    """
    n = len(sorted_sample)
    if n == 0:
        return 0.0
    if n == 1:
        return sorted_sample[0]
    k = (n - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_sample[int(k)]
    return sorted_sample[f] * (c - k) + sorted_sample[c] * (k - f)


def classify_latency_band(latency_sec: float) -> tuple[str, float]:
    """Classify latency against problem.md section 12 bands:

    p95 <= 5.0s  -> Band 1 (3.0 pts)
    > 5-15s      -> Band 2 (2.0 pts)
    > 15-30s     -> Band 3 (1.0 pts)
    > 30s        -> Band 4 (0.0 pts, failure)
    """
    if latency_sec <= 5.0:
        return "Band 1 (<=5.0s)", 3.0
    elif latency_sec <= 15.0:
        return "Band 2 (>5-15s)", 2.0
    elif latency_sec <= 30.0:
        return "Band 3 (>15-30s)", 1.0
    else:
        return "Band 4 (>30s, failure)", 0.0


def run_latency_benchmark(
    base_url: str,
    endpoint: str | None = None,
    n_calls: int = 30,
    concurrency: int = 1,
    cases_file: str | pathlib.Path = "tests/fixtures/public_cases.json",
    timeout: float = 30.0,
    json_out: str | pathlib.Path | None = None,
) -> int:
    """Executes the latency measurement benchmark. Returns exit code (0 on full success)."""
    cases_path = pathlib.Path(cases_file)
    if not cases_path.is_file():
        sys.stderr.write(f"Error: Cases file not found: {cases_path}\n")
        return 2

    try:
        data = json.loads(cases_path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"Error reading cases JSON: {e}\n")
        return 2

    cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(cases, list) or not cases:
        sys.stderr.write(f"Error: No cases array found in {cases_path}\n")
        return 2

    if endpoint is None:
        endpoint, found = discover_optimize_route()
        if not found:
            endpoint = "/optimize-energy"

    full_url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")

    # Ensure n is at least 20 per rubric requirement
    if n_calls < 20:
        print(f"[Notice] Rubric requires at least 20 scored calls. Elevating --n from {n_calls} to 20.")
        n_calls = 20

    print("=" * 80)
    print("           GRIDWISE LATENCY AND RESILIENCE BENCHMARK INSTRUMENT           ")
    print("=" * 80)
    print(f" Target Endpoint:   {full_url}")
    print(f" Cases File:        {cases_path} ({len(cases)} cases available)")
    print(f" Requested Calls:   {n_calls} scored calls (+ 2 discarded warmup calls)")
    print(f" Concurrency Level: {concurrency} {'(Sequential)' if concurrency == 1 else '(Concurrent Threads)'}")
    print(f" Per-Call Timeout:  {timeout:.1f}s (Hard challenge ceiling)")
    print("=" * 80)

    # 1. Warmup Phase (2 discarded calls)
    print("\n--- Phase 1: Warmup & Cold-Start Evaluation (2 Discarded Calls) ---")
    warmup_results: list[dict[str, Any]] = []
    for w_idx in range(2):
        c = cases[w_idx % len(cases)]
        cid = c.get("id") or c.get("scenario_id") or f"WARM-{w_idx+1}"
        payload = c.get("input", c)
        is_cold = (w_idx == 0)
        label = "Warmup #1 (COLD START)" if is_cold else "Warmup #2"

        print(f"  Issuing {label} [{cid}] ... ", end="", flush=True)
        res = make_call(full_url, payload, timeout=timeout)
        warmup_results.append(res)
        status_text = f"HTTP {res['status_code']}" if res["status_code"] else "NO_STATUS"
        wf_text = "WELL-FORMED" if res["well_formed"] else "MALFORMED/ERROR"
        print(f"{res['latency_sec']:.3f}s | {status_text} | {wf_text}")
        if res["error_msg"]:
            print(f"    Notice: {res['error_msg']}")

    cold_call = warmup_results[0]
    cold_band, cold_pts = classify_latency_band(cold_call["latency_sec"])
    print(f"\n[Cold-Start Analysis]")
    print(f"  Cold-start call latency: {cold_call['latency_sec']:.4f}s")
    print(f"  Status: {cold_call['status_code']} | Well-formed: {cold_call['well_formed']}")
    print(f"  Rubric band if cold-start was included in p95: {cold_band} ({cold_pts:.1f}/3.0 pts)")
    print("  -> EXCLUDED from scored sample to prevent cold-start contamination of steady-state p50.")

    # 2. Scored Calls Phase
    mode_label = "Sequential (Concurrency 1)" if concurrency == 1 else f"Concurrent (Concurrency {concurrency})"
    print(f"\n--- Phase 2: Scored Execution ({n_calls} Calls, {mode_label}) ---")
    scored_calls: list[dict[str, Any]] = []

    prepared_tasks = []
    for i in range(n_calls):
        c = cases[i % len(cases)]
        cid = c.get("id") or c.get("scenario_id") or f"CASE-{i+1}"
        payload = c.get("input", c)
        prepared_tasks.append((i, cid, payload))

    if concurrency == 1:
        for idx, cid, payload in prepared_tasks:
            call_num = idx + 1
            print(f"  [{call_num:02d}/{n_calls}] Calling {cid:<15} ... ", end="", flush=True)
            res = make_call(full_url, payload, timeout=timeout)
            res["call_index"] = call_num
            res["case_id"] = cid
            scored_calls.append(res)
            st_text = f"HTTP {res['status_code']}" if res["status_code"] else "NO_STATUS"
            if res["well_formed"]:
                print(f"OK ({res['latency_sec']:.3f}s)")
            else:
                err_short = (res["error_msg"] or "Failed")[:40]
                print(f"FAIL ({st_text}, {res['latency_sec']:.3f}s) - {err_short}")
    else:
        print(f"  Dispatching {n_calls} calls across {concurrency} worker threads...")
        start_bench = time.perf_counter()

        def _worker(task: tuple[int, str, dict]) -> dict[str, Any]:
            idx, cid, payload = task
            call_res = make_call(full_url, payload, timeout=timeout)
            call_res["call_index"] = idx + 1
            call_res["case_id"] = cid
            return call_res

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_task = {executor.submit(_worker, t): t for t in prepared_tasks}
            completed_count = 0
            for fut in concurrent.futures.as_completed(future_to_task):
                completed_count += 1
                r = fut.result()
                scored_calls.append(r)
                st_text = f"HTTP {r['status_code']}" if r["status_code"] else "ERR"
                wf_str = "OK" if r["well_formed"] else "ERR"
                print(f"    [{completed_count:02d}/{n_calls}] Call #{r['call_index']} ({r['case_id']}): {wf_str} in {r['latency_sec']:.3f}s ({st_text})")

        total_bench_wall = time.perf_counter() - start_bench
        print(f"  All {n_calls} concurrent calls completed in {total_bench_wall:.2f}s wall-clock time.")
        scored_calls.sort(key=lambda x: x["call_index"])

    # 3. Categorize Failures
    count_non_200 = 0
    count_timeouts = 0
    count_malformed = 0
    count_other_err = 0

    valid_latencies: list[float] = []
    all_latencies: list[float] = []

    for r in scored_calls:
        lat = r["latency_sec"]
        all_latencies.append(lat)
        if r["is_timeout"]:
            count_timeouts += 1
        elif r["is_non_200"]:
            count_non_200 += 1
        elif r["is_malformed"]:
            count_malformed += 1
        elif not r["well_formed"]:
            count_other_err += 1
        else:
            valid_latencies.append(lat)

    total_failures = count_non_200 + count_timeouts + count_malformed + count_other_err
    total_calls = len(scored_calls)
    total_clean = len(valid_latencies)

    # 4. Latency Statistics Calculation
    # Note requirement 5: A fast error is not a fast response. If any calls failed,
    # statistics are computed strictly on valid calls or explicitly flagged.
    sample_to_analyze = valid_latencies if valid_latencies else all_latencies
    sorted_sample = sorted(sample_to_analyze)
    n_sample = len(sorted_sample)

    min_val = sorted_sample[0] if n_sample else 0.0
    max_val = sorted_sample[-1] if n_sample else 0.0
    mean_val = (sum(sorted_sample) / n_sample) if n_sample else 0.0
    p50_val = compute_percentile(sorted_sample, 0.50)
    p90_val = compute_percentile(sorted_sample, 0.90)
    p95_val = compute_percentile(sorted_sample, 0.95)
    p99_val = compute_percentile(sorted_sample, 0.99)

    p50_band, p50_pts = classify_latency_band(p50_val)
    p95_band, p95_pts = classify_latency_band(p95_val)

    # 5. Output Reporting
    print("\n" + "=" * 80)
    print(f"                      LATENCY & RELIABILITY RESULTS ({mode_label.upper()})                      ")
    print("=" * 80)

    print("\n[Call Execution & Integrity Summary]")
    print(f"  Total Scored Calls Issued:  {total_calls}")
    print(f"  Successful (200 + Valid):   {total_clean} / {total_calls} ({(total_clean/total_calls*100):.1f}%)")
    print(f"  Total Failures:             {total_failures}")
    print(f"    - Non-200 Responses:      {count_non_200}")
    print(f"    - Timeouts (>= {timeout:.1f}s):      {count_timeouts}")
    print(f"    - Malformed Bodies:       {count_malformed}")
    print(f"    - Other Errors:           {count_other_err}")

    if total_failures > 0:
        print("\n  [!] CRITICAL INTEGRITY WARNING:")
        print(f"      {total_failures} call(s) failed. A run whose calls failed CANNOT claim rubric")
        print("      latency points. Fast errors are excluded from flattering steady-state percentiles.")

    print("\n[Percentile Statistics]")
    print(f"  Sample Size:        {n_sample} {'valid calls' if total_clean else 'calls (ALL ERRORED)'}")
    print(f"  Percentile Method:  {PERCENTILE_METHOD_DESC}")
    print("-" * 80)
    print(f"  Min:   {min_val:>7.4f}s")
    print(f"  p50:   {p50_val:>7.4f}s  | Rubric: {p50_band:<22} | Implied Points: {p50_pts:.1f}/3.0")
    print(f"  p90:   {p90_val:>7.4f}s")
    print(f"  p95:   {p95_val:>7.4f}s  | Rubric: {p95_band:<22} | Implied Points: {p95_pts:.1f}/3.0")
    print(f"  p99:   {p99_val:>7.4f}s")
    print(f"  Max:   {max_val:>7.4f}s")
    print(f"  Mean:  {mean_val:>7.4f}s")
    print("-" * 80)

    # Prominently print failure count right beside latency summary
    print("\n[Rubric Latency Scorecard Entry]")
    fail_summary_str = f"{total_failures} failures ({count_non_200} non-200, {count_timeouts} timeouts, {count_malformed} malformed)"
    if total_failures == 0:
        print(f"  p50 = {p50_val:.3f}s | p95 = {p95_val:.3f}s | Failures: 0 [CLEAN]")
        print(f"  Classification: {p95_band} -> {p95_pts:.1f}/3.0 latency points implied")
    else:
        print(f"  p50 = {p50_val:.3f}s | p95 = {p95_val:.3f}s | Failures: {fail_summary_str} [INVALIDATED]")
        print(f"  Classification: Band 4 (Disqualified due to {total_failures} failures) -> 0.0/3.0 points")

    if json_out:
        out_path = pathlib.Path(json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        json_payload = {
            "meta": {
                "base_url": base_url,
                "endpoint": endpoint,
                "full_url": full_url,
                "n_calls": n_calls,
                "concurrency": concurrency,
                "timeout_sec": timeout,
                "cases_file": str(cases_path),
                "timestamp": time.time(),
                "percentile_method": PERCENTILE_METHOD_DESC,
            },
            "cold_start": {
                "warmup_1_cold_latency_sec": warmup_results[0]["latency_sec"],
                "warmup_1_status": warmup_results[0]["status_code"],
                "warmup_1_well_formed": warmup_results[0]["well_formed"],
                "warmup_2_latency_sec": warmup_results[1]["latency_sec"],
                "warmup_2_status": warmup_results[1]["status_code"],
                "warmup_2_well_formed": warmup_results[1]["well_formed"],
            },
            "failures": {
                "total_failures": total_failures,
                "non_200": count_non_200,
                "timeouts": count_timeouts,
                "malformed_body": count_malformed,
                "other_errors": count_other_err,
            },
            "latency": {
                "sample_count": n_sample,
                "min": round(min_val, 4),
                "p50": round(p50_val, 4),
                "p90": round(p90_val, 4),
                "p95": round(p95_val, 4),
                "p99": round(p99_val, 4),
                "max": round(max_val, 4),
                "mean": round(mean_val, 4),
                "p50_band": p50_band,
                "p50_pts": p50_pts,
                "p95_band": p95_band,
                "p95_pts": p95_pts if total_failures == 0 else 0.0,
            },
            "calls": [
                {
                    "call_index": r["call_index"],
                    "case_id": r["case_id"],
                    "status_code": r["status_code"],
                    "latency_sec": round(r["latency_sec"], 4),
                    "well_formed": r["well_formed"],
                    "error_msg": r["error_msg"],
                }
                for r in scored_calls
            ],
        }
        out_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
        print(f"\nBenchmark JSON saved to: {out_path}")

    print("=" * 80)

    # Exit 0 only if every scored call returned 200 with a well-formed body
    if total_failures == 0 and total_clean == n_calls:
        print("Final Status: PASS (100% successful requests with valid bodies)")
        return 0
    else:
        print(f"Final Status: FAIL ({total_failures} failure(s) detected)")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GridWise Standalone Latency and Resilience Benchmark CLI"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Target base URL of the service (e.g. http://127.0.0.1:8130)",
    )
    parser.add_argument(
        "--n",
        dest="n_calls",
        type=int,
        default=30,
        help="Number of scored calls to execute (default: 30, minimum 20)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of concurrent worker threads (default: 1, sequential)",
    )
    parser.add_argument(
        "--cases",
        default="tests/fixtures/public_cases.json",
        help="Path to fixture cases JSON file (default: tests/fixtures/public_cases.json)",
    )
    parser.add_argument(
        "--json",
        dest="json_out",
        default=None,
        help="Optional output file path to write JSON benchmark scorecard",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Override endpoint path (default: discover from backend/routes/, else /optimize-energy)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-request timeout ceiling in seconds (default: 30.0s)",
    )

    args = parser.parse_args(argv)
    return run_latency_benchmark(
        base_url=args.url,
        endpoint=args.endpoint,
        n_calls=args.n_calls,
        concurrency=args.concurrency,
        cases_file=args.cases,
        timeout=args.timeout,
        json_out=args.json_out,
    )


if __name__ == "__main__":
    sys.exit(main())
