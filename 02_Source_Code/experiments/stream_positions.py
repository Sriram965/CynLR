"""Measure the live Green-dot stream for Experiment 1.

Set Object Speed manually in the CynLr UI before starting this script.
The script does not send any command; it only records the streamed
observations and timestamps them.

Usage:
    python3 experiments/stream_positions.py

The CSV is written under results/ so the raw measurement can be kept
with the experiment.

Run this once for each Object Speed you want to compare, for example
500, 250, and 100.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cynlr_client import connect, read_observation

HOST = "10.211.55.3"
PORT = 6102
BYTEORDER = "big"
DURATION_SECONDS = 10.0

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def main() -> None:
    speed_label = input(
        "Enter the Object Speed currently shown in CynLr "
        "(for example 500, 250, or 100): "
    ).strip()

    if not speed_label:
        raise SystemExit("Object Speed label cannot be empty.")

    output_file = RESULTS_DIR / f"green_speed_{speed_label}.csv"

    print(f"Connecting to {HOST}:{PORT}...")
    sock = connect(HOST, PORT)
    print("Connected.")
    print(f"Recording for {DURATION_SECONDS:.1f} seconds.")
    print("No commands will be sent.")

    start = time.perf_counter()
    packet_count = 0

    try:
        with output_file.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "elapsed_time",
                    "green_x",
                    "green_y",
                    "blue_x",
                    "blue_y",
                    "error_x",
                    "error_y",
                ]
            )

            while True:
                elapsed = time.perf_counter() - start
                if elapsed >= DURATION_SECONDS:
                    break

                obs = read_observation(sock, BYTEORDER)
                elapsed = time.perf_counter() - start

                writer.writerow(
                    [
                        f"{elapsed:.6f}",
                        obs.green_x,
                        obs.green_y,
                        obs.blue_x,
                        obs.blue_y,
                        int(obs.error_x),
                        int(obs.error_y),
                    ]
                )

                packet_count += 1

                if packet_count % 100 == 0:
                    print(
                        f"packets={packet_count:5d} "
                        f"t={elapsed:7.3f}s "
                        f"green=({obs.green_x}, {obs.green_y})",
                        flush=True,
                    )
    finally:
        sock.close()

    print()
    print("Experiment complete.")
    print(f"Packets recorded: {packet_count}")
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()
