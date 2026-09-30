"""Probe the CynLr Position Error / Error % behavior.

Goal
----
Compare three observable things during one fresh Learning Mode run:

1. The application's raw Error X / Error Y bytes.
2. The coordinate difference computed from the reported Green/Blue X/Y.
3. The GUI's cumulative "Error %" value, which must be read manually.

Protocol
--------
- Start a fresh Learning Mode path with Object Speed/Object Size fixed.
- Phase 1: continuously command P(current Green X, current Green Y).
- Pause and note the GUI Error %.
- Phase 2: send no P commands and only observe.
- Pause and note the GUI Error % again.

The experiment does NOT assume that Error X/Y are positional errors, nor that
the reported Blue coordinates perfectly match the visual Blue dot. It records
those quantities so they can be compared against the GUI metric.

Run from the repository root:

    python3 -m experiments.error_metric_probe

The script writes:
    results/error_metric_probe.csv
    results/error_metric_probe_summary.txt
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

FOLLOW_SECONDS = 10.0
HOLD_SECONDS = 10.0
SOCKET_TIMEOUT = 2.0

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)

OUTPUT_CSV = RESULTS_DIR / "error_metric_probe.csv"
OUTPUT_SUMMARY = RESULTS_DIR / "error_metric_probe_summary.txt"


def collect_phase(
    sock,
    phase: str,
    duration: float,
    send_follow_command: bool,
    start_time: float,
    rows: list[dict[str, object]],
) -> None:
    phase_end = time.monotonic() + duration

    while time.monotonic() < phase_end:
        obs = read_observation(sock, BYTEORDER)
        observed = time.monotonic()

        coordinate_error_x = obs.green_x - obs.blue_x
        coordinate_error_y = obs.green_y - obs.blue_y
        coordinate_distance = (
            coordinate_error_x * coordinate_error_x
            + coordinate_error_y * coordinate_error_y
        ) ** 0.5

        row = {
            "phase": phase,
            "elapsed_since_start": f"{observed - start_time:.6f}",
            "green_x": obs.green_x,
            "green_y": obs.green_y,
            "blue_x": obs.blue_x,
            "blue_y": obs.blue_y,
            "computed_dx": coordinate_error_x,
            "computed_dy": coordinate_error_y,
            "computed_distance": f"{coordinate_distance:.6f}",
            "error_x_flag": int(obs.error_x),
            "error_y_flag": int(obs.error_y),
            "error_any_flag": int(obs.error_x or obs.error_y),
        }
        rows.append(row)

        if send_follow_command:
            # The manual defines P as the Blue-position command.
            # We intentionally command the *currently reported* Green position,
            # i.e. the same simple feedback strategy as track_green.py.
            send_position(sock, obs.green_x, obs.green_y, BYTEORDER)


def summarize(rows: list[dict[str, object]], phase: str) -> dict[str, object]:
    phase_rows = [r for r in rows if r["phase"] == phase]
    if not phase_rows:
        return {
            "phase": phase,
            "observations": 0,
            "error_any_fraction": "n/a",
            "mean_coordinate_distance": "n/a",
        }

    error_any = sum(int(r["error_any_flag"]) for r in phase_rows)
    distances = [float(r["computed_distance"]) for r in phase_rows]

    return {
        "phase": phase,
        "observations": len(phase_rows),
        "error_any_fraction": f"{error_any / len(phase_rows):.4f}",
        "mean_coordinate_distance": f"{sum(distances) / len(distances):.3f}",
    }


def ask_gui_percentage(label: str) -> str:
    value = input(
        f"Look at the CynLr GUI now and enter the displayed Error % "
        f"for {label} (or press Enter to skip): "
    ).strip()
    return value if value else "not recorded"


def main() -> None:
    print()
    print("=== CynLr Error Metric Probe ===")
    print()
    print("Before starting:")
    print("  1. Open a fresh Learning Mode path.")
    print("  2. Keep Object Speed and Object Size fixed.")
    print("  3. Leave the GUI visible so Error % can be read.")
    input("Press Enter when ready... ")

    rows: list[dict[str, object]] = []
    gui_values: dict[str, str] = {}

    print("\nConnecting...")
    with connect(HOST, PORT, timeout=SOCKET_TIMEOUT) as sock:
        baseline = read_observation(sock, BYTEORDER)
        print(
            "Initial observation: "
            f"green=({baseline.green_x},{baseline.green_y}) "
            f"blue=({baseline.blue_x},{baseline.blue_y})"
        )

        gui_values["before_follow"] = ask_gui_percentage("before FOLLOW")

        start_time = time.monotonic()

        print(
            f"\nPhase 1: FOLLOW for {FOLLOW_SECONDS:.1f}s "
            "(send P(current Green X, current Green Y))."
        )
        collect_phase(
            sock,
            phase="follow",
            duration=FOLLOW_SECONDS,
            send_follow_command=True,
            start_time=start_time,
            rows=rows,
        )

        gui_values["after_follow"] = ask_gui_percentage("after FOLLOW")

        print(
            f"\nPhase 2: HOLD for {HOLD_SECONDS:.1f}s "
            "(send no P commands; observe only)."
        )
        collect_phase(
            sock,
            phase="hold",
            duration=HOLD_SECONDS,
            send_follow_command=False,
            start_time=start_time,
            rows=rows,
        )

        gui_values["after_hold"] = ask_gui_percentage("after HOLD")

    fieldnames = [
        "phase",
        "elapsed_since_start",
        "green_x",
        "green_y",
        "blue_x",
        "blue_y",
        "computed_dx",
        "computed_dy",
        "computed_distance",
        "error_x_flag",
        "error_y_flag",
        "error_any_flag",
    ]

    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summaries = [
        summarize(rows, "follow"),
        summarize(rows, "hold"),
    ]

    with OUTPUT_SUMMARY.open("w") as f:
        f.write("CynLr Error Metric Probe Summary\n")
        f.write("================================\n\n")
        f.write("GUI Error % values entered manually:\n")
        f.write(f"before FOLLOW: {gui_values['before_follow']}\n")
        f.write(f"after FOLLOW:  {gui_values['after_follow']}\n")
        f.write(f"after HOLD:    {gui_values['after_hold']}\n\n")
        f.write("Stream-derived summaries (NOT the GUI metric):\n")
        for summary in summaries:
            f.write(
                f"{summary['phase']}: "
                f"observations={summary['observations']}, "
                f"error_any_fraction={summary['error_any_fraction']}, "
                f"mean_coordinate_distance={summary['mean_coordinate_distance']}\n"
            )
        f.write(
            "\nInterpretation note:\n"
            "The script does not assume that Error X/Y are positional errors "
            "or that computed Green-Blue distance is the application's true "
            "Position Error. Compare the recorded quantities with the GUI "
            "Error % and visual state.\n"
        )

    print()
    print("Experiment complete.")
    print(f"Saved: {OUTPUT_CSV}")
    print(f"Saved: {OUTPUT_SUMMARY}")
    print()
    print("Do not treat the computed distance or Error X/Y flags as the GUI")
    print("Position Error until the comparison supports that interpretation.")


if __name__ == "__main__":
    main()
