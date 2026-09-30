"""Stay connected and command Blue to the latest Green position.

    python3 experiments/track_green.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cynlr_client import connect, read_observation, send_position

HOST = "10.211.55.3"
PORT = 6102

sock = connect(HOST, PORT)
print("connected", flush=True)
try:
    while True:
        obs = read_observation(sock, "big")
        send_position(sock, obs.green_x, obs.green_y, "big")
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
