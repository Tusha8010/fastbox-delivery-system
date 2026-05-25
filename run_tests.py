"""
run_tests.py
============
Runs delivery_system.py against the base case and all 10 provided test cases,
printing a concise summary table.

Usage:
    python run_tests.py
"""

import json
import os
import sys
from delivery_system import parse_input, assign_packages, simulate_deliveries, find_best_agent, build_report

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_cases")
BASE_CASE = os.path.join(os.path.dirname(__file__), "base_case.json")


def run_case(path: str, label: str) -> dict:
    with open(path) as f:
        data = json.load(f)

    warehouses, agents, packages = parse_input(data)
    agent_packages = assign_packages(packages, agents, warehouses)
    results = simulate_deliveries(agent_packages, agents, warehouses, add_delays=False)
    best = find_best_agent(results)
    report = build_report(results, best)
    return report


def print_report(label: str, report: dict):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    for aid in sorted(k for k in report if k != "best_agent"):
        r = report[aid]
        pkg_list = ", ".join(r["packages"]) if r["packages"] else "—"
        print(
            f"  {aid}:  {r['packages_delivered']} pkg(s)  "
            f"dist={r['total_distance']:7.2f}  "
            f"efficiency={r['efficiency']:7.2f}  "
            f"[{pkg_list}]"
        )
    print(f"  ★ Best agent: {report['best_agent']}")

    delivered = sum(v["packages_delivered"] for k, v in report.items() if k != "best_agent")
    print(f"  Total delivered: {delivered}")


if __name__ == "__main__":
    # Base case
    if os.path.exists(BASE_CASE):
        r = run_case(BASE_CASE, "BASE CASE (base_case.json)")
        print_report("BASE CASE (base_case.json)", r)

    # Numbered test cases
    test_dir = os.path.join(os.path.dirname(__file__), "test_cases")
    for i in range(1, 11):
        path = os.path.join(test_dir, f"test_case_{i}.json")
        if os.path.exists(path):
            r = run_case(path, f"TEST CASE {i}")
            print_report(f"TEST CASE {i}", r)
        else:
            print(f"\n[SKIP] {path} not found")

    print("\nAll test cases completed.")
