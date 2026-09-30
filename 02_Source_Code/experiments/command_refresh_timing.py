"""Test whether repeated P commands must be refreshed.

Run from the repository root with Chase_the_Dot already open.

Experiment:
    - Connect and read one baseline observation.
    - Send P(TARGET_X, TARGET_Y) every 100 ms for 1 second.
    - Stop sending commands.
    - Continue reading observations for 2 seconds.
    - Timestamp every command and observation.

This is an environment-identification experiment. It does not change
the existing client or protocol implementation.
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

TARGET_X = 900
TARGET_Y = 600

COMMAND_INTERVAL_SECONDS = 0.100
COMMAND_DURATION_SECONDS = 1.0
OBSERVATION_DURATION_AFTER_STOP_SECONDS = 2.0

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = RESULTS_DIR / "command_refresh_timing.csv"


def main() -> None:
    print(f"Connecting to {HOST}:{PORT}...", flush=True)
    sock = connect(HOST, PORT)
    print("Connected.", flush=True)

    try:
        before = read_observation(sock, BYTEORDER)
        print(
            f"Before commands: green=({before.green_x},{before.green_y}) "
            f"blue=({before.blue_x},{before.blue_y})",
            flush=True,
        )

        experiment_start = time.monotonic()
        command_end = experiment_start + COMMAND_DURATION_SECONDS
        observation_end = command_end + OBSERVATION_DURATION_AFTER_STOP_SECONDS

        with OUTPUT_FILE.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "event",
                    "elapsed_since_start",
                    "elapsed_since_last_command",
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

            next_command = experiment_start
            command_count = 0
            last_command_time: float | None = None

            while time.monotonic() < observation_end:
                now = time.monotonic()

                if now >= next_command and now < command_end:
                    send_position(sock, TARGET_X, TARGET_Y, BYTEORDER)
                    command_count += 1
                    last_command_time = now
                    print(
                        f"COMMAND #{command_count}: "
                        f"t={now - experiment_start:.6f}s "
                        f"P({TARGET_X},{TARGET_Y})",
                        flush=True,
                    )
                    writer.writerow(
                        [
                            "command",
                            f"{now - experiment_start:.6f}",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ]
                    )
                    next_command += COMMAND_INTERVAL_SECONDS
                    continue

                obs = read_observation(sock, BYTEORDER)
                observed_time = time.monotonic()
                elapsed = observed_time - experiment_start

                error_x = obs.green_x - obs.blue_x
                error_y = obs.green_y - obs.blue_y
                error_distance = (error_x * error_x + error_y * error_y) ** 0.5

                since_command = (
                    ""
                    if last_command_time is None
                    else f"{observed_time - last_command_time:.6f}"
                )

                phase = "during_commands" if observed_time < command_end else "after_stop"

                writer.writerow(
                    [
                        phase,
                        f"{elapsed:.6f}",
                        since_command,
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

                if command_count <= 2 or phase == "after_stop" or command_count % 5 == 0:
                    print(
                        f"{phase}: t={elapsed:.6f}s "
                        f"green=({obs.green_x},{obs.green_y}) "
                        f"blue=({obs.blue_x},{obs.blue_y}) "
                        f"error=({error_x},{error_y})",
                        flush=True,
                    )

        print(f"Commands sent: {command_count}", flush=True)
        print(f"Saved to {OUTPUT_FILE}", flush=True)

    finally:
        sock.close()


if __name__ == "__main__":
    main()
