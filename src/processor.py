import sys
import csv
from dataclasses import dataclass

@dataclass
class SymbolStats:
    """
    Holds the running statistics for a single symbol.
    Designed to be memory efficient by only storing aggregates, not raw events.
    """
    symbol: str
    # TODO: Add fields for timestamp tracking (first/last)
    # TODO: Add fields for price tracking (open/high/low/close)
    # TODO: Add fields for calculation (total_volume, total_value, price_sum, count)

    def update(self, price: float, quantity: int, timestamp: int):
        """
        Updates the running statistics with a new trade event.
        Complexity: O(1)
        """
        pass

    def to_csv_row(self) -> list:
        """
        Returns the formatted fields required for output:
        symbol, first_ts, last_ts, open, close, high, low, avg_px, vwap
        """
        return []

def process_stream(input_stream, output_stream):
    """
    Reads from input_stream line-by-line, aggregates stats, and writes to output_stream.
    Complexity: O(N) time, O(M) space (where M is unique symbols).
    """
    # TODO: Initialize dictionary for symbol tracking
    # TODO: Parse CSV header
    # TODO: Loop through lines and update SymbolStats
    # TODO: Sort symbols alphabetically
    # TODO: Write output header and rows
    pass

if __name__ == "__main__":
    # Simple entry point to verify the skeleton runs
    print("Tool initialized. Ready for logic implementation.", file=sys.stderr)
