# Trade Statistics Aggregator

A high-performance command-line tool to calculate aggregated trade statistics from a stream of price updates.

## Overview
This tool processes a CSV of chronological price update events and outputs aggregated statistics (Open, High, Low, Close, VWAP) per symbol. It is designed to run in O(N) time and O(M) space (where M is the number of unique symbols), making it suitable for very large datasets that exceed available memory.

## Quick Start

### Prerequisites
* **Docker** (Recommended method)
* *Or* **Python 3.10+** (Local execution)

### Running with Docker (Recommended)
This ensures the tool runs in a reproducible environment.

```bash
# Build and run against the sample data
make run

# Run against a specific file
make run FILE=path/to/large_input.csv
```

### Running Locally

```bash
# Setup environment
make install

# Process data
cat data/sample.csv | python3 src/main.py
```

### Running Tests

```bash
make test
```

## Design & Architecture

### Memory & Streaming Strategy
Single Pass Processing: The tool processes input in a single pass and does not retain individual rows in memory.

Complexity: Memory usage is O(S) where S is the number of distinct symbols (for aggregation state), and O(1) with respect to the total number of rows.

Rationale: This satisfies the requirement to handle "very large amounts of data" effectively while remaining simple to reason about and maintain.

### Concurrency Model
Single-threaded: The implementation is single-threaded. Given that the file is already ordered by timestamp and all statistics are simple per-symbol reductions, a single-threaded streaming parser is sufficient.

Synchronization: This avoids complex synchronization and merge logic.

Scalability Note: If higher throughput were required, the architecture allows for sharding by symbol (e.g., modulo hashing symbol strings to worker threads), but this was deemed unnecessary complexity for the baseline requirements.

### Data Types & Precision
Prices: Parsed as double-precision floats.

Quantities/Timestamps: Parsed as 64-bit integers to prevent overflow and maintain nanosecond resolution.

Rounding: All output prices are rounded to 3 decimal places as required. Internal calculations preserve full precision until the final output formatting.

## Assumptions
Input Validity: The input is assumed to strictly follow the specified CSV schema (symbol,venue,price,quantity,timestamp). Malformed lines trigger a fatal error ("fail fast") rather than being silently skipped, ensuring data integrity issues are caught immediately.

Encoding: Input is treated as UTF-8. While the sample data is ASCII, the tool supports international symbol names without modification.

Sorting: Output is sorted using standard lexicographical comparison to satisfy the alphabetical sorting requirement.

## Project Structure

```
## Project Structure

```text
├── .github/
│   └── workflows/          # CI configuration (linting, tests)
├── src/                    # Source code
│   ├── main.py             # CLI entry point & argument parsing
│   ├── processor.py        # Streaming engine: reads CSV, updates per-symbol stats
│   └── stats.py            # Aggregation data structures & helpers (SymbolStats, etc.)
├── tests/                  # Pytest suite (unit + end-to-end tests)
├── Dockerfile              # Multi-stage build for reproducible runs
├── Makefile                # Developer UX: run, test, install targets
└── requirements.txt        # Python runtime + dev dependencies

```# log-parser
