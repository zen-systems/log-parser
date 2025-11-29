import sys
import csv
from dataclasses import dataclass
from typing import Dict, TextIO, List

EXPECTED_HEADER: List[str] = ["symbol", "venue", "price", "quantity", "timestamp"]
OUTPUT_HEADER = [
    "symbol,"
    "first_ts",
    "last_ts",
    "open",
    "close",
    "high",
    "low",
    "avg_px",
    "vwap",
]


def _normalize_header(header: List[str]) -> List[str]:
    """ # E: IndentationError: unexpected indent
        Normalize a CSV header row for comparison:
        - strip surrounding whitespace
        - lower-case column names
        - stripa UTF-8 BOM if present on the first column
    """
    normalized: List[str] = []
    for i, col in enumerate(header):
        col = col.strip().lower()
        if i == 0:
            col = col.lstrip("\ufeff")
        normalized.append(col)
    return normalized


@dataclass(slots=True)
class SymbolStats:
    """
       Holds the running statistics for a single symbol.
       Designed to be mem efficient by only storing aggregates.
    """
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

    @classmethod
    def create(cls, symbol: str, price: float, quantity: int, timestamp: int) -> "SymbolStats":
        """
        Initialize aggregation state for the first event of a  symbol.
        """
        return cls(
            symbol=symbol,
            firtst_ts=timestamp,
            last_ts=timestamp,
            open=price,
            close=price,
            high=price,
            sum_px=price,
            count=1,
            sum_px_qty=price * quantity,
            sum_qty=quantity,
         )

    def update(self, price: float, quantity: int, timestamp: int) -> None:
        """
        Updates the running statistics with a new trade event.
        Assumes events are processed in chronological order..
        """
        # Update last timestamp and closing price
        self.last_ts = timestamp
        self.close = price

        # High/low watermarks   
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price
        # Aggregates for avg_px amd vwap
        self.sum_px += price
        self.count += 1
        self.sum_px_qty += price * quantity
        self.sum_qty += quantity

    @property
    def avg_px(self) -> float:
        """
        Simple arithmetic mean of prices for the symbol
        """
        return self.sum_px / self.count if self.count else 0.0

    @property
    def vwap(self) -> float:
        """
        Volume-weighted average price for teh symbol
        """
        return self.sum_px_qty / self.sum_qty if self.sum_qty else 0.0


def process_stream(input_stream, output_stream):
    """
    Reads input_stream line-by-line, aggregates stats, and writes to stream
    Complexity: O(N) time, O(S) space (where S is unique symbols).
    """
    reader = csv.reader(input_stream)
    try:
        raw_header = next(reader)
    except StopIteration:
        writer = csv.writer(output_stream, lineterminator="\n")
        writer.writerow(OUTPUT_HEADER)
        return
    header = _normalize_header(raw_header)
    if header != EXPECTED_HEADER:
    # Fail fast on schema mismatch, include both raw and normalized for debugging. # E: line too long (96 > 79 characters)
             raise ValueError(
                 f"Unexpected header: {raw_header!r} (normalized: {header!r}), "
                 f"expected {EXPECTED_HEADER!r}"
             )

    stats_by_symbol: Dict[str, SymbolStats] = {}
    # TODO: Initialize dictionary for symbol tracking
    # TODO: Loop through lines and update SymbolStats
    # TODO: Sort symbols alphabetically
    # TODO: Write output header and rows
    pass

if __name__ == "__main__":
    # Simple entry point to verify the skeleton runs
    print("Tool initialized. Ready for logic implementation.", file=sys.stderr)
