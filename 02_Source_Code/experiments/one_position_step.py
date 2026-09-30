"""Measure the response to exactly one Blue-position command.

Run from the repository root with Chase_the_Dot already open.

Protocol:
    1. Connect to CynLr.
    2. Read one observation before the command.
    3. Send P(TARGET_X, TARGET_Y) exactly once.
    4. Send no further commands.
    5. Record observations for a short window.

This experiment is intended to determine whether the Blue dot jumps
instantaneously to the commanded position or moves over time.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cynlr_client import connect, read_observation, send_position


HOST = "10.211.55.3"
PORT = 6102
BYTEORDER = "big"

TARGET_X = 200
TARGET_Y = 200
DURATION_SECONDS = 3.0

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = RESULTS_DIR / "one_position_step.csv"


def main() -> None:
    print(f"Connecting to {HOST}:{PORT}...", flush=True)
    sock = connect(HOST, PORT)
    print("Connected.", flush=True)

    try:
        before = read_observation(sock, BYTEORDER)
        print(
            f"Before P: green=({before.green_x},{before.green_y}) "
            f"blue=({before.blue_x},{before.blue_y})",
            flush=True,
        )

        command_time = time.monotonic()
        print(
            f"Sending P({TARGET_X},{TARGET_Y}) exactly once.",
            flush=True,
        )
        send_position(sock, TARGET_X, TARGET_Y, BYTEORDER)

        end_time = command_time + DURATION_SECONDS

        with OUTPUT_FILE.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "elapsed_since_command",
                    "green_x",
                    "green_y",
                    "blue_x",
                    "blue_y",
                    "error_x_flag",
                    "error_y_flag",
                ]
            )

            count = 0
            while time.monotonic() < end_time:
                obs = read_observation(sock, BYTEORDER)
                elapsed = time.monotonic() - command_time

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

                count += 1
                if count <= 12 or count % 50 == 0:
                    print(
                        f"t={elapsed:.3f}s "
                        f"green=({obs.green_x},{obs.green_y}) "
                        f"blue=({obs.blue_x},{obs.blue_y})",
                        flush=True,
                    )

        print(f"Recorded {count} observations.", flush=True)
        print(f"Saved to {OUTPUT_FILE}", flush=True)

    finally:
        sock.close()


if __name__ == "__main__":
    main()
