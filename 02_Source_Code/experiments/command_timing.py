"""Timestamp command/observation timing for one P command.

Run from the repository root with Chase_the_Dot already open.

The experiment:
    1. Connect.
    2. Read one observation.
    3. Send one P command.
    4. Send no more commands.
    5. Continue reading observations for a short window.

Every observation is timestamped using the same monotonic clock as the
command timestamp. This helps distinguish command timing from the
asynchronous observation stream.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cynlr_client import connect, read_observation, send_position
from src.protocol import build_position_command


HOST = "10.211.55.3"
PORT = 6102
BYTEORDER = "big"

TARGET_X = 900
TARGET_Y = 600
DURATION_SECONDS = 2.0

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = RESULTS_DIR / "command_timing.csv"


def main() -> None:
    print(f"Connecting to {HOST}:{PORT}...", flush=True)
    sock = connect(HOST, PORT)
    print("Connected.", flush=True)

    try:
        # Read the current state once before sending the command.
        before = read_observation(sock, BYTEORDER)
        print(
            f"Before P: green=({before.green_x},{before.green_y}) "
            f"blue=({before.blue_x},{before.blue_y})",
            flush=True,
        )

        packet = build_position_command(TARGET_X, TARGET_Y, BYTEORDER)
        print(f"P packet ({len(packet)} bytes): {packet.hex(' ')}", flush=True)

        command_time = time.monotonic()
        send_position(sock, TARGET_X, TARGET_Y, BYTEORDER)
        print(
            f"P({TARGET_X},{TARGET_Y}) sent at t=0.000000s",
            flush=True,
        )

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
                    "computed_error_x",
                    "computed_error_y",
                    "computed_error_distance",
                    "error_x_flag",
                    "error_y_flag",
                ]
            )

            count = 0
            while time.monotonic() < end_time:
                obs = read_observation(sock, BYTEORDER)
                observed_time = time.monotonic()
                elapsed = observed_time - command_time

                error_x = obs.green_x - obs.blue_x
                error_y = obs.green_y - obs.blue_y
                error_distance = (error_x * error_x + error_y * error_y) ** 0.5

                writer.writerow(
                    [
                        f"{elapsed:.6f}",
                        obs.green_x,
                        obs.green_y,
                        obs.blue_x,
                        obs.blue_y,
                        error_x,
                        error_y,
                        f"{error_distance:.6f}",
                        int(obs.error_x),
                        int(obs.error_y),
                    ]
                )

                count += 1
                if count <= 20 or count % 50 == 0:
                    print(
                        f"t={elapsed:.6f}s "
                        f"green=({obs.green_x},{obs.green_y}) "
                        f"blue=({obs.blue_x},{obs.blue_y}) "
                        f"error=({error_x},{error_y})",
                        flush=True,
                    )

        print(f"Recorded {count} observations.", flush=True)
        print(f"Saved to {OUTPUT_FILE}", flush=True)

        # Keep the socket open only for the measurement window; no commands
        # are sent after the single P command.
    finally:
        sock.close()


if __name__ == "__main__":
    main()
