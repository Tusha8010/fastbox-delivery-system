"""
FastBox Delivery System Simulator
==================================
Simulates one day of logistics operations for the fictional company FastBox.

Assignment: Python Developer – Nexgensis Technologies Pvt. Ltd.

Assumptions documented here (as required by the assignment):
-----------------------------------------------------------------
1. INPUT FORMAT FLEXIBILITY: The assignment PDF shows warehouses/agents as a plain dict
   (e.g. "W1": [0,0]) while base_case.json uses a list-of-objects format
   (e.g. {"id":"W1","location":[0,0]}). The test cases use the dict format.
   This code auto-detects and handles BOTH formats so all inputs work.

2. PACKAGE KEY: PDF uses "warehouse", base_case.json uses "warehouse_id".
   Both are supported automatically.

3. AGENT ASSIGNMENT: Each package is assigned to the nearest agent based on
   Euclidean distance from the agent's current position to the package's warehouse.
   After assignment, the agent's position does NOT update mid-assignment-phase —
   all assignments are computed based on original positions (batch assignment).
   This is the most standard interpretation for this type of problem.

4. DELIVERY ROUTE PER AGENT: An agent with multiple packages travels:
     current_pos → warehouse_A → destination_A → warehouse_B → destination_B → ...
   Packages are delivered in the order they were assigned (FIFO by package id).
   Each leg's distance is added to total_distance.

5. EFFICIENCY: Defined as total_distance / packages_delivered (distance per package).
   Lower is better (more efficient). Best agent = lowest efficiency score.
   If no packages are delivered, efficiency is 0.0 to avoid division by zero.

6. TIE-BREAKING: If two agents are equidistant from a warehouse, the agent with
   the lexicographically smaller ID is chosen (e.g. A1 before A2).

7. BONUS FEATURES IMPLEMENTED:
   - Random delivery delays (each package has a random 0–30 min delay)
   - ASCII route visualization
   - Export top performer to CSV
"""

import json
import math
import csv
import random
import argparse
import sys
from typing import Any


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def euclidean(p1: list[float], p2: list[float]) -> float:
    """Return the Euclidean distance between two 2D points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def parse_input(data: dict) -> tuple[dict, dict, list]:
    """
    Parse the input JSON into normalised dicts/lists.

    Handles two input formats:
      - Dict format:  {"warehouses": {"W1": [x,y], ...}, "agents": {...}, "packages": [...]}
      - List format:  {"warehouses": [{"id":"W1","location":[x,y]}, ...], ...}

    Returns:
        warehouses: {id: [x, y]}
        agents:     {id: [x, y]}
        packages:   [{"id": ..., "warehouse": ..., "destination": [...]}]
    """
    # --- warehouses ---
    raw_w = data["warehouses"]
    if isinstance(raw_w, dict):
        warehouses = {k: list(v) for k, v in raw_w.items()}
    else:  # list of objects
        warehouses = {w["id"]: list(w["location"]) for w in raw_w}

    # --- agents ---
    raw_a = data["agents"]
    if isinstance(raw_a, dict):
        agents = {k: list(v) for k, v in raw_a.items()}
    else:
        agents = {a["id"]: list(a["location"]) for a in raw_a}

    # --- packages ---
    packages = []
    for p in data["packages"]:
        warehouse_key = p.get("warehouse") or p.get("warehouse_id")
        packages.append({
            "id": p["id"],
            "warehouse": warehouse_key,
            "destination": list(p["destination"]),
        })

    return warehouses, agents, packages


# ---------------------------------------------------------------------------
# Core simulation logic
# ---------------------------------------------------------------------------

def assign_packages(
    packages: list[dict],
    agents: dict,
    warehouses: dict,
) -> dict[str, list[dict]]:
    """
    Assign each package to the nearest agent (by Euclidean distance
    from agent's starting position to the package's warehouse).

    Tie-breaking: lexicographically smaller agent ID wins.

    Returns:
        agent_packages: {agent_id: [package, ...]}  (in assignment order)
    """
    # Initialise empty assignment lists for every agent
    agent_packages: dict[str, list[dict]] = {aid: [] for aid in agents}

    for pkg in packages:
        warehouse_loc = warehouses[pkg["warehouse"]]

        # Find the nearest agent to this warehouse
        best_agent = None
        best_dist = float("inf")

        for aid, aloc in sorted(agents.items()):  # sorted for deterministic tie-breaking
            d = euclidean(aloc, warehouse_loc)
            if d < best_dist:
                best_dist = d
                best_agent = aid

        agent_packages[best_agent].append(pkg)

    return agent_packages


def simulate_deliveries(
    agent_packages: dict[str, list[dict]],
    agents: dict,
    warehouses: dict,
    add_delays: bool = False,
) -> dict[str, dict]:
    """
    Simulate the delivery routes for all agents.

    Route per agent (FIFO order over their assigned packages):
        start → warehouse_i → destination_i  (repeated for each package)

    Args:
        agent_packages: output of assign_packages()
        agents:         {id: [x, y]}  (starting positions)
        warehouses:     {id: [x, y]}
        add_delays:     if True, add random 0-30 min delay per package (bonus feature)

    Returns:
        results: {
            agent_id: {
                "packages_delivered": int,
                "total_distance": float,
                "efficiency": float,
                "route": [(label, x, y), ...],   # for visualisation
                "delivered_ids": [str, ...],
                "total_delay_minutes": int,       # only if add_delays=True
            }
        }
    """
    results = {}

    for aid, pkgs in agent_packages.items():
        current_pos = list(agents[aid])  # start at agent's home position
        total_dist = 0.0
        route = [("START", current_pos[0], current_pos[1])]
        total_delay = 0

        for pkg in pkgs:
            wh_loc = warehouses[pkg["warehouse"]]
            dest_loc = pkg["destination"]

            # Leg 1: agent → warehouse
            leg1 = euclidean(current_pos, wh_loc)
            total_dist += leg1
            route.append((f"WH:{pkg['warehouse']}", wh_loc[0], wh_loc[1]))

            # Leg 2: warehouse → destination
            leg2 = euclidean(wh_loc, dest_loc)
            total_dist += leg2
            route.append((f"DEST:{pkg['id']}", dest_loc[0], dest_loc[1]))

            current_pos = dest_loc  # agent is now at destination

            # Bonus: random delay
            if add_delays:
                delay = random.randint(0, 30)
                total_delay += delay

        n = len(pkgs)
        efficiency = round(total_dist / n, 2) if n > 0 else 0.0

        entry = {
            "packages_delivered": n,
            "total_distance": round(total_dist, 2),
            "efficiency": efficiency,
            "route": route,
            "delivered_ids": [p["id"] for p in pkgs],
        }
        if add_delays:
            entry["total_delay_minutes"] = total_delay

        results[aid] = entry

    return results


def find_best_agent(results: dict[str, dict]) -> str:
    """
    Return the agent ID with the lowest efficiency score
    (smallest distance-per-package = most efficient).

    Agents with zero packages are excluded. Tie-breaking: lexicographic ID.
    """
    eligible = {aid: v for aid, v in results.items() if v["packages_delivered"] > 0}
    if not eligible:
        return ""
    return min(eligible, key=lambda aid: (eligible[aid]["efficiency"], aid))


def build_report(results: dict[str, dict], best_agent: str) -> dict:
    """
    Build the final report dict (matches the format shown in the assignment).
    """
    report = {}
    for aid, v in sorted(results.items()):
        report[aid] = {
            "packages_delivered": v["packages_delivered"],
            "total_distance": v["total_distance"],
            "efficiency": v["efficiency"],
            "packages": v["delivered_ids"],
        }
    report["best_agent"] = best_agent
    return report


# ---------------------------------------------------------------------------
# Bonus: ASCII route visualiser
# ---------------------------------------------------------------------------

def ascii_visualise(results: dict[str, dict], agents: dict, warehouses: dict) -> str:
    """
    Draw a simple ASCII map (80×30 grid) showing agent start positions,
    warehouses, and delivery destinations.
    """
    WIDTH, HEIGHT = 79, 29

    # Collect all coordinates for normalisation
    all_pts = (
        list(agents.values())
        + list(warehouses.values())
    )
    for v in results.values():
        for _, x, y in v["route"]:
            all_pts.append([x, y])

    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)

    def to_grid(x, y):
        """Map world coordinates to grid indices."""
        gx = int((x - min_x) / max(max_x - min_x, 1) * (WIDTH - 1))
        gy = HEIGHT - 1 - int((y - min_y) / max(max_y - min_y, 1) * (HEIGHT - 1))
        return gx, gy

    # Build grid
    grid = [["." for _ in range(WIDTH)] for _ in range(HEIGHT)]

    # Mark warehouses
    for wid, wloc in warehouses.items():
        gx, gy = to_grid(*wloc)
        grid[gy][gx] = "W"

    # Mark agent start positions
    for aid, aloc in agents.items():
        gx, gy = to_grid(*aloc)
        grid[gy][gx] = aid[1]  # e.g. "1" for A1

    # Mark destinations
    for v in results.values():
        for label, x, y in v["route"]:
            if label.startswith("DEST:"):
                gx, gy = to_grid(x, y)
                if grid[gy][gx] == ".":
                    grid[gy][gx] = "*"

    lines = ["+" + "-" * WIDTH + "+"]
    for row in grid:
        lines.append("|" + "".join(row) + "|")
    lines.append("+" + "-" * WIDTH + "+")
    lines.append("Legend: W=Warehouse  1-9=Agent_Start  *=Delivery_Destination")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bonus: Export top performer to CSV
# ---------------------------------------------------------------------------

def export_top_performer_csv(report: dict, path: str = "top_performer.csv") -> None:
    """Export the best agent's stats to a CSV file."""
    best = report["best_agent"]
    if not best:
        print("No deliveries made; nothing to export.")
        return

    data = report[best]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["agent_id", "packages_delivered", "total_distance", "efficiency", "packages"])
        writer.writerow([
            best,
            data["packages_delivered"],
            data["total_distance"],
            data["efficiency"],
            ";".join(data["packages"]),
        ])
    print(f"Top performer exported to {path}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(input_path: str, output_path: str = "report.json", bonus: bool = True) -> dict:
    """
    Full pipeline: read → parse → assign → simulate → report → save.

    Args:
        input_path:  path to input JSON file
        output_path: path where report.json will be saved
        bonus:       whether to run bonus features

    Returns:
        The report dict (also saved to output_path)
    """
    # Step 1: Read and parse the JSON file
    print(f"Reading input from: {input_path}")
    with open(input_path, "r") as f:
        raw_data = json.load(f)

    warehouses, agents, packages = parse_input(raw_data)
    print(f"  Warehouses : {len(warehouses)}")
    print(f"  Agents     : {len(agents)}")
    print(f"  Packages   : {len(packages)}")

    # Step 2: Assign each package to the nearest agent
    print("\nAssigning packages to nearest agents...")
    agent_packages = assign_packages(packages, agents, warehouses)
    for aid, pkgs in sorted(agent_packages.items()):
        ids = [p["id"] for p in pkgs]
        print(f"  {aid} → {ids if ids else '(no packages)'}")

    # Step 3: Simulate delivery and compute distances
    print("\nSimulating deliveries...")
    add_delays = bonus  # random delays are a bonus feature
    results = simulate_deliveries(agent_packages, agents, warehouses, add_delays=add_delays)

    # Step 4: Find best agent and build report
    best_agent = find_best_agent(results)
    report = build_report(results, best_agent)

    # Step 5: Save report to report.json
    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)
    print(f"\nReport saved to: {output_path}")

    # Print summary
    print("\n--- Delivery Report ---")
    for aid in sorted(k for k in report if k != "best_agent"):
        r = report[aid]
        delay_info = ""
        if add_delays and "total_delay_minutes" in results[aid]:
            delay_info = f"  delay={results[aid]['total_delay_minutes']}min"
        print(
            f"  {aid}: {r['packages_delivered']} pkg(s), "
            f"dist={r['total_distance']:.2f}, "
            f"efficiency={r['efficiency']:.2f}{delay_info}"
        )
    print(f"  Best agent: {best_agent}")

    # Bonus: ASCII visualisation
    if bonus:
        print("\n--- ASCII Route Map ---")
        print(ascii_visualise(results, agents, warehouses))

        # Bonus: Export top performer
        export_top_performer_csv(report)

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FastBox Delivery System Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="data.json",
        help="Path to input JSON file (default: data.json)",
    )
    parser.add_argument(
        "-o", "--output",
        default="report.json",
        help="Path for the output report JSON (default: report.json)",
    )
    parser.add_argument(
        "--no-bonus",
        action="store_true",
        help="Disable bonus features (delays, ASCII map, CSV export)",
    )
    args = parser.parse_args()

    if not args.input:
        print("Error: please provide an input JSON file.")
        sys.exit(1)

    run(args.input, args.output, bonus=not args.no_bonus)
