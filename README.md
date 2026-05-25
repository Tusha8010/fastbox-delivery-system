# FastBox Delivery System

**Assignment:** Python Developer – Nexgensis Technologies Pvt. Ltd.

---

## Overview

A logistics simulator for the fictional delivery company **FastBox**. Given a set of warehouses, delivery agents, and packages (all specified in a JSON file), the system:

1. Assigns each package to the **nearest agent** (Euclidean distance from agent to the package's warehouse)
2. Simulates the delivery route for each agent and computes total distance travelled
3. Generates a **report** showing packages delivered, total distance, and efficiency per agent
4. Identifies the **most efficient agent** (lowest distance per package)
5. Saves the report to `report.json`

---

## Project Structure

```
fastbox_delivery/
├── delivery_system.py    # Main simulator (CLI entry point)
├── run_tests.py          # Batch runner for all test cases
├── data.json             # Sample input (base_case)
├── base_case.json        # Original base case
├── report.json           # Generated output (after running)
├── top_performer.csv     # Generated CSV of best agent (bonus)
└── test_cases/
    ├── test_case_1.json
    ├── ...
    └── test_case_10.json
```

---

## Requirements

- Python 3.10+ (uses `list[...]` type hints)
- No external dependencies — pure standard library

---

## Usage

### Run on a single input file

```bash
python delivery_system.py data.json
```

This reads `data.json`, runs the simulation, prints a report to stdout, saves `report.json`, and (bonus) saves `top_performer.csv`.

**Options:**

```
positional argument:  path to input JSON (default: data.json)
-o / --output         path for output report (default: report.json)
--no-bonus            disable bonus features (random delays, ASCII map, CSV export)
```

Examples:

```bash
# Run with default file names
python delivery_system.py

# Run with a specific test case, no bonus
python delivery_system.py test_cases/test_case_3.json --no-bonus -o tc3_report.json
```

### Run all test cases

```bash
python run_tests.py
```

Runs every test case and prints a summary table for each.

---

## Input Format

The simulator accepts **two JSON formats** (auto-detected):

**Format A — dict style (used by test cases 1–10):**
```json
{
  "warehouses": { "W1": [0, 0], "W2": [50, 75] },
  "agents":     { "A1": [5, 5], "A2": [60, 60] },
  "packages": [
    { "id": "P1", "warehouse": "W1", "destination": [30, 40] }
  ]
}
```

**Format B — list style (used by base_case.json):**
```json
{
  "warehouses": [{ "id": "W1", "location": [0, 0] }],
  "agents":     [{ "id": "A1", "location": [5, 5] }],
  "packages": [
    { "id": "P1", "warehouse_id": "W1", "destination": [30, 40] }
  ]
}
```

---

## Output Format (`report.json`)

```json
{
    "A1": {
        "packages_delivered": 2,
        "total_distance": 121.21,
        "efficiency": 60.61,
        "packages": ["P1", "P4"]
    },
    "A3": {
        "packages_delivered": 1,
        "total_distance": 14.14,
        "efficiency": 14.14,
        "packages": ["P3"]
    },
    "best_agent": "A3"
}
```

- `efficiency` = `total_distance / packages_delivered` (lower = more efficient)
- `best_agent` = agent with the lowest efficiency score

---

## Algorithm

### Package Assignment
Each package is individually assigned to the nearest available agent:

```
for each package P:
    warehouse_location = warehouses[P.warehouse]
    best_agent = argmin over agents of euclidean(agent.location, warehouse_location)
    assign P to best_agent
```

All assignments are computed from **original agent positions** (batch assignment, not sequential). Tie-breaking uses lexicographic agent ID order.

### Delivery Route
Each agent delivers their packages in assignment order:

```
current_pos = agent.start_location
for each assigned package P:
    travel: current_pos → P.warehouse   (add distance)
    travel: P.warehouse → P.destination (add distance)
    current_pos = P.destination
```

---

## Assumptions & Design Decisions

All ambiguous scenarios were resolved with the most logical engineering approach:

| # | Assumption | Rationale |
|---|-----------|-----------|
| 1 | **Dual input format support** — both dict and list-of-objects JSON formats are handled | The PDF and provided test cases use different formats; auto-detection avoids requiring format conversion |
| 2 | **Both `"warehouse"` and `"warehouse_id"` package keys** are accepted | Used inconsistently across the provided files |
| 3 | **Batch assignment** — all packages assigned before any deliveries start | Prevents earlier assignments from skewing distances for later ones |
| 4 | **FIFO delivery order** within an agent's package list | Simplest deterministic ordering; packages appended in order they appear in input |
| 5 | **Efficiency = distance / packages** (lower = better) | Matches the sample output in the PDF |
| 6 | **Efficiency = 0.0** for agents with no packages | Avoids division by zero; these agents are excluded from best-agent selection |
| 7 | **Tie-breaking** on equal distance → lexicographically smaller agent ID | Deterministic and fair |

---

## Bonus Features

All bonus features are enabled by default and can be disabled with `--no-bonus`.

### 1. Random Delivery Delays
Each package pickup incurs a random 0–30 minute delay, simulating real-world variability (traffic, handling time). Displayed in the console output per agent.

### 2. ASCII Route Visualisation
A terminal map (80×30 grid) is printed showing:
- `W` = Warehouse locations
- `1`–`9` = Agent starting positions  
- `*` = Delivery destinations

All coordinates are normalised to fit the grid.

### 3. CSV Export of Top Performer
The best agent's stats are saved to `top_performer.csv`:
```
agent_id,packages_delivered,total_distance,efficiency,packages
A3,1,14.14,14.14,P3
```

---

## Test Results Summary

| Test Case | Agents | Packages | Best Agent | Total Delivered |
|-----------|--------|----------|------------|-----------------|
| base_case | 3      | 5        | A3         | 5               |
| 1         | 4      | 12       | A1         | 12              |
| 2         | 3      | 10       | A1         | 10              |
| 3         | 4      | 6        | A3         | 6               |
| 4         | 5      | 12       | A3         | 12              |
| 5         | 5      | 10       | A3         | 10              |
| 6         | 4      | 9        | A3         | 9               |
| 7         | 4      | 10       | A3         | 10              |
| 8         | 4      | 11       | A1         | 11              |
| 9         | 4      | 8        | A3         | 8               |
| 10        | 4      | 11       | A4         | 11              |

All packages delivered in every test case. ✓
