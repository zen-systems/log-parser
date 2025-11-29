import sys
import csv
from dataclasses import dataclass
from typing import Dict, TextIO, List


EXPECTED_HEADER: List[str] = [
    "symbol",
    "venue",
    "price",
    "quantity",
    "timestamp",
]

OUTPUT_HEADER: List[str] = [
    "symbol",
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
    """
    Normalize a CSV header row for comparison.

    - Strip surrounding whitespace.
    - Lower-case column names.
    - Strip a UTF-8 BOM if present on the first column.
    """
    normalized: List[str] = []
    for index, column in enumerate(header):
        col = column.strip().lower()
        if index == 0:
            col = col.lstrip("\ufeff")
        normalized.append(col)
    return normalized


@dataclass(slots=True)
class SymbolStats:
    """
    Holds the running statistics for a single symbol.

    Stores only aggregate values instead of raw events so that memory
    usage stays O(S), where S is the number of distinct symbols.
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
    def create(
        cls,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: int,
    ) -> "SymbolStats":
        """Initialize aggregation state for the first event of a symbol."""
        return cls(
            symbol=symbol,
            first_ts=timestamp,
            last_ts=timestamp,
            open=price,
            close=price,
            high=price,
            low=price,
            sum_px=price,
            count=1,
            sum_px_qty=price * quantity,
            sum_qty=quantity,
        )

    def update(self, price: float, quantity: int, timestamp: int) -> None:
        """
        Update the running statistics with a new trade event.

        Assumes events are processed in chronological order.
        """
        # Update last timestamp and closing price.
        self.last_ts = timestamp
        self.close = price

        # High/low watermarks.
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price

        # Aggregates for avg_px and VWAP.
        self.sum_px += price
        self.count += 1
        self.sum_px_qty += price * quantity
        self.sum_qty += quantity

    @property
    def avg_px(self) -> float:
        """Simple arithmetic mean of prices for the symbol."""
        if self.count == 0:
            return 0.0
        return self.sum_px / self.count

    @property
    def vwap(self) -> float:
        """Volume-weighted average price for the symbol."""
        if self.sum_qty == 0:
            return 0.0
        return self.sum_px_qty / self.sum_qty


def process_stream(input_stream: TextIO, output_stream: TextIO) -> None:
    """
    Read input_stream line-by-line, aggregate stats, and write to output_stream.

    Complexity: O(N) time and O(S) space, where S is the number of symbols.
    """
    reader = csv.reader(input_stream)

    # Handle header / empty input.
    try:
        raw_header = next(reader)
    except StopIteration:
        writer = csv.writer(output_stream, lineterminator="\n")
        writer.writerow(OUTPUT_HEADER)
        return

    header = _normalize_header(raw_header)
    if header != EXPECTED_HEADER:
        # Fail fast on schema mismatch, but include raw and normalized forms.
        message = (
            "Unexpected header. "
            f"raw={raw_header!r}, normalized={header!r}, "
            f"expected={EXPECTED_HEADER!r}"
        )
        raise ValueError(message)

    stats_by_symbol: Dict[str, SymbolStats] = {}

    # Stream rows and update per-symbol stats.
    for line_num, row in enumerate(reader, start=2):
        if len(row) != 5:
            message = (
                "Malformed row at line "
                f"{line_num}: expected 5 columns, got "
                f"{len(row)}: {row!r}"
            )
            raise ValueError(message)

        symbol, venue, price_str, qty_str, ts_str = row

        try:
            price = float(price_str)
            quantity = int(qty_str)
            timestamp = int(ts_str)
        except ValueError as exc:
            message = (
                "Malformed numeric value at line "
                f"{line_num}: {row!r}"
            )
            raise ValueError(message) from exc

        if quantity <= 0:
            message = (
                "Quantity must be positive at line "
                f"{line_num}: {row!r}"
            )
            raise ValueError(message)

        stats = stats_by_symbol.get(symbol)
        if stats is None:
            stats_by_symbol[symbol] = SymbolStats.create(
                symbol=symbol,
                price=price,
                quantity=quantity,
                timestamp=timestamp,
            )
        else:
            stats.update(price=price, quantity=quantity, timestamp=timestamp)

    writer = csv.writer(output_stream, lineterminator="\n")
    writer.writerow(OUTPUT_HEADER)

    # Output one row per symbol, sorted alphabetically.
    for symbol in sorted(stats_by_symbol):
        s = stats_by_symbol[symbol]
        writer.writerow(
            [
                s.symbol,
                str(s.first_ts),
                str(s.last_ts),
                f"{s.open:.3f}",
                f"{s.close:.3f}",
                f"{s.high:.3f}",
                f"{s.low:.3f}",
                f"{s.avg_px:.3f}",
                f"{s.vwap:.3f}",
            ]
        )


if __name__ == "__main__":
    process_stream(sys.stdin, sys.stdout)

