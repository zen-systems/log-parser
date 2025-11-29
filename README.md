# Trade Statistics Aggregator

A high-performance command-line tool to calculate aggregated trade statistics from a stream of price updates.

## Overview

This tool processes a CSV of chronological price update events and outputs aggregated statistics per symbol:

- **Open**
- **High**
- **Low**
- **Close**
- **Simple average price (`avg_px`)**
- **Volume-weighted average price (`vwap`)**

It is designed to run in **O(N)** time and **O(S)** space, where:

- **N** = total number of rows (events)
- **S** = number of unique symbols

This makes it suitable for **very large datasets** that exceed available memory, because it never stores raw rows—only aggregates.

---

## Quick Start

### Prerequisites

You can run this in a few ways:

- **Python 3.10+** (local execution)
- **Docker** (for a fully reproducible environment)
- `make` (for the convenience targets below)

---

### 1. Running with `make` (recommended)

From the repository root:

```bash
# Install Python dependencies (pytest, etc.)
make install

# Run against the sample data in data/input.csv
make run

# Run against a specific file
make run FILE=path/to/large_input.csv

# Run tests
make test
```

### 2. Running directly with Python

```bash
# From a file
python3 src/main.py data/input.csv

# Or via stdin
cat data/input.csv | python3 src/main.py

# Explicitly tell the CLI to use stdin
python3 src/main.py - < data/input.csv
```

### 3. Running with Docker

Build the image:

```bash
docker build -t trade-aggregator .
```

Then run, streaming CSV over stdin:

```bash
cat data/input.csv | docker run --rm -i trade-aggregator
```

Or via the Makefile:

```bash
make docker-build
cat data/input.csv | make docker-run
```

---

## CLI Usage

The CLI is intentionally simple:

```bash
python3 src/main.py [FILE]
```

- If `FILE` is provided and not `-`, the tool reads from that file.
- If `FILE` is omitted or set to `-`, the tool reads from stdin.

**Examples:**

```bash
# File input
python3 src/main.py data/input.csv

# Streaming input (e.g., from another process)
some_generator | python3 src/main.py

# Explicit stdin
python3 src/main.py - < data/input.csv
```

---

## Input & Output Format

### Input CSV schema

The tool expects a CSV with the following header and columns:

```
symbol,venue,price,quantity,timestamp
```

- **symbol** (string)
- **venue** (string)
- **price** (float)
- **quantity** (integer, must be > 0)
- **timestamp** (integer, typically nanosecond epoch)

### Output CSV schema

The tool emits one row per symbol:

```
symbol,first_ts,last_ts,open,close,high,low,avg_px,vwap
```

Where:

- **first_ts** = timestamp of the first event seen for that symbol (open)
- **last_ts** = timestamp of the last event seen for that symbol (close)
- **open** = price of the first event for that symbol
- **close** = price of the last event for that symbol
- **high** = maximum trade price for that symbol
- **low** = minimum trade price for that symbol
- **avg_px** = simple arithmetic mean of prices for that symbol
- **vwap** = volume-weighted average price  
  `= sum(price * quantity) / sum(quantity)`

All price-like values are formatted to 3 decimal places.

Symbols are sorted alphabetically in the output.

---

## Design & Architecture

### Streaming & Complexity

**Single pass processing:**

- Input is processed line-by-line using Python's stdlib `csv` reader.
- No raw event rows are stored after they are processed.

**Complexity:**

- **Time:** O(N) — each event is processed exactly once.
- **Space:** O(S) — only one `SymbolStats` object per symbol is kept, regardless of N.

This satisfies the requirement to handle "very large amounts of data" while remaining simple to reason about.

### Aggregation State: SymbolStats

Per symbol, the tool maintains a compact aggregation structure:

```python
@dataclass(slots=True)
class SymbolStats:
    symbol: str
    first_ts: int
    last_ts: int
    open: float
    close: float
    high: float
    low: float
    sum_px: float
    count: int
    sum_px_qty: float
    sum_qty: int
```

- `create(...)` initializes the stats from the first event for that symbol.
- `update(...)` folds each subsequent event into:
  - `last_ts` / `close`
  - `high` / `low` watermarks
  - running sums for simple average and VWAP:
    - `sum_px` and `count` for `avg_px`
    - `sum_px_qty` and `sum_qty` for `vwap`

This is the key to keeping memory usage at O(S) while still being able to calculate all required metrics at the end.

### Header Normalization & Validation

The first row is treated as the header and normalized via `_normalize_header`:

- leading/trailing whitespace stripped
- converted to lowercase
- any UTF-8 BOM on the first column stripped

The normalized header is compared against an `EXPECTED_HEADER` constant:

```python
EXPECTED_HEADER = [
    "symbol",
    "venue",
    "price",
    "quantity",
    "timestamp",
]
```

If it does not match, the tool:

- raises `ValueError`
- includes both the raw and normalized header in the error message

This gives a fail-fast behavior on schema drift, while being tolerant of cosmetic issues like:

```
" Symbol ", "VENUE ", "Price", " quantity", "Timestamp"
```

### Numeric Parsing & Validation

For each row:

- **price** → parsed as `float`
- **quantity** → parsed as `int` and must be strictly positive
- **timestamp** → parsed as `int`

**Error handling:**

- If a row has the wrong number of columns, the tool raises `ValueError` with:
  - line number
  - expected vs actual column count
  - offending row
- If type conversion fails (e.g. `price="foo"`), a `ValueError` is raised with a line number and the offending row.
- If `quantity <= 0`, a `ValueError` is raised (this is treated as malformed data, not just "zero volume").

This "fail fast with context" behavior is intentional: it surfaces upstream data issues instead of silently skipping bad rows.

### Concurrency Model

**Single-threaded:**

- The implementation is deliberately single-threaded.
- Given that the file is already ordered by timestamp and all statistics are simple per-symbol reductions, a single-threaded streaming parser is sufficient for the problem size and constraints.

**Why not parallel?**

- Parallelizing this safely would require sharding by symbol (e.g., hashing symbol → worker) and then merging per-symbol aggregates.
- That adds non-trivial complexity (synchronization, merging) for limited benefit in this context.

**Scalability note:**

- The current architecture keeps all symbol state in a dictionary. If higher throughput were required, this design can be extended by:
  - sharding symbols across worker processes
  - merging `SymbolStats` aggregates at the end.
- For the scope of this exercise, the simpler single-threaded model is a better trade-off: deterministic, easy to reason about, fewer failure modes.

### Data Types & Precision

- **Prices:** stored as Python `float` (double precision).
- **Quantities & timestamps:** stored as Python `int` (unbounded, but conceptually 64-bit in the source data).

**Rounding:**

- Internal computations keep full precision.
- Only the final CSV output is rounded to 3 decimal places via format strings like `f"{value:.3f}"`.
- This avoids unnecessary rounding error accumulation during aggregation.

---

## Project Structure

```
.
├── data/
│   └── input.csv          # Sample input data
├── src/
│   ├── __init__.py        # Marks src as a package
│   ├── main.py            # CLI entrypoint (argument parsing, stdin/file handling)
│   └── processor.py       # Streaming aggregation logic and SymbolStats
├── tests/
│   └── test_processor.py  # Pytest suite for core aggregation logic
├── Dockerfile             # Containerized runtime
├── Makefile               # Convenience commands (run, test, docker-*)
├── requirements.txt       # Python dependencies (pytest, etc.)
└── README.md              # This file
```

---

## Testing

Tests are written with `pytest` and focus on:

- Correct aggregation for simple multi-symbol scenarios
- Header normalization behavior
- Failure modes for bad headers and invalid data (e.g., non-positive quantity)

Run them via:

```bash
make test
# or
python3 -m pytest
```

---

## Assumptions & Limitations

- Input is chronologically ordered by timestamp.
- Input conforms to the specified schema; malformed rows are treated as fatal.
- VWAP is computed across all events for a symbol, not per-venue or per-day.
- The tool is I/O bound and single-threaded by design; if the dataset grows to extreme sizes and a single process becomes insufficient, sharding + merge would be the next step.
