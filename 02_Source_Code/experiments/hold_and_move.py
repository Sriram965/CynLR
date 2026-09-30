"""Stay connected and send one fixed P command after every record.

    python3 experiments/hold_and_move.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cynlr_client import connect, read_observation, send_position

HOST = "10.211.55.3"
PORT = 6102
TARGET_X = 200
TARGET_Y = 200

sock = connect(HOST, PORT)
print("connected", flush=True)
try:
    while True:
        send_position(sock, TARGET_X, TARGET_Y, "big")
        obs = read_observation(sock, "big")
        print(
            obs.green_x,
            obs.green_y,
            obs.blue_x,
            obs.blue_y,
            obs.error_x,
            obs.error_y,
            flush=True,
        )
finally:
    sock.close()
