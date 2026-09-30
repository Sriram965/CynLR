"""Characterize whether Object Size affects Green and/or Blue.

Protocol experiment:
- Connect to the CynLr application.
- Send C commands repeatedly at one fixed Object Speed.
- Test minimum Object Size (10), then maximum (100).
- Do not send P commands.
- Record streamed Green/Blue positions and Error fields for later visual comparison.

The experiment is intentionally descriptive: it does not assume what Object Size
controls. Visual observations from the application should be recorded alongside
the CSV.
"""

from __future__ import annotations

import csv
import os
import threading
import time
from pathlib import Path

from src.cynlr_client import connect, read_observation, send_config

HOST = "10.211.55.3"
PORT = 6102
BYTEORDER = "big"

OBJECT_SPEED = 300
SIZES = (10, 100)
SECONDS_PER_SIZE = 5.0
CONFIG_REFRESH_SECONDS = 0.2

OUTPUT = Path("results/object_size_effect.csv")


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    stop_sender = threading.Event()
    current_size = {"value": SIZES[0]}
    lock = threading.Lock()

    with connect(HOST, PORT) as sock:
        print(f"Connected to {HOST}:{PORT}")
        print(f"Object Speed: {OBJECT_SPEED}")
        print(f"Testing Object Size: {SIZES[0]} -> {SIZES[1]}")
        print("No P commands will be sent.")

        def send_configs() -> None:
            while not stop_sender.is_set():
                with lock:
                    size = current_size["value"]
                send_config(sock, OBJECT_SPEED, size, BYTEORDER)
                stop_sender.wait(CONFIG_REFRESH_SECONDS)

        sender = threading.Thread(target=send_configs, daemon=True)
        sender.start()

        rows = []
        start = time.perf_counter()

        try:
            for size in SIZES:
                with lock:
                    current_size["value"] = size

                phase_start = time.perf_counter()
                print(f"\nTesting Object Size = {size}")

                while time.perf_counter() - phase_start < SECONDS_PER_SIZE:
                    obs = read_observation(sock, BYTEORDER)
                    elapsed = time.perf_counter() - start
                    rows.append(
                        {
                            "elapsed_time": elapsed,
                            "object_size": size,
                            "green_x": obs.green_x,
                            "green_y": obs.green_y,
                            "blue_x": obs.blue_x,
                            "blue_y": obs.blue_y,
                            "error_x": int(obs.error_x),
                            "error_y": int(obs.error_y),
                        }
                    )

                print(f"Finished Object Size = {size}")

        finally:
            stop_sender.set()
            sender.join(timeout=1.0)

    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [
            "elapsed_time",
            "object_size",
            "green_x",
            "green_y",
            "blue_x",
            "blue_y",
            "error_x",
            "error_y",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Recorded {len(rows)} observations.")
    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
