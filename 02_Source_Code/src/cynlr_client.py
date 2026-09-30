"""TCP client for the CynLr app.

The manual says the app listens and sends 20-byte observations.
It does not say how many bytes one recv returns, or how long to wait.
"""

from __future__ import annotations

import socket

from src.protocol import (
    OBSERVATION_SIZE,
    Observation,
    build_config_command,
    build_position_command,
    parse_observation,
)


def connect(host: str, port: int, timeout: float = 5.0) -> socket.socket:
    """Open a TCP connection. CynLr is the server; this process is the client."""
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(timeout)
    return sock


def read_exact(sock: socket.socket, size: int) -> bytes:
    """Read until size bytes have arrived. One recv may return fewer."""
    parts: list[bytes] = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            got = size - remaining
            raise ConnectionError(f"connection closed after {got} of {size} bytes")
        parts.append(chunk)
        remaining -= len(chunk)
    return b"".join(parts)


def read_observation(sock: socket.socket, byteorder: str) -> Observation:
    packet = read_exact(sock, OBSERVATION_SIZE)
    return parse_observation(packet, byteorder)


def send_position(sock: socket.socket, blue_x: int, blue_y: int, byteorder: str) -> None:
    sock.sendall(build_position_command(blue_x, blue_y, byteorder))


def send_config(sock: socket.socket, object_speed: int, object_size: float, byteorder: str) -> None:
    sock.sendall(build_config_command(object_speed, object_size, byteorder))
