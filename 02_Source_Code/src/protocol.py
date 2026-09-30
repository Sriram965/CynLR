"""CynLr observation records and C/P commands.

Field order and sizes come from the application manual.
The manual does not state endianness. Pass byteorder="little" or "big".
The manual does not state whether bool 1 means "in error".
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

OBSERVATION_SIZE = 20
POSITION_COMMAND_SIZE = 13
CONFIG_COMMAND_SIZE = 17

_CRLF = b"\r\n"
_ENDIAN = {"little": "<", "big": ">"}


@dataclass(frozen=True)
class Observation:
    green_x: int
    green_y: int
    blue_x: int
    blue_y: int
    error_x: bool
    error_y: bool


def _prefix(byteorder: str) -> str:
    try:
        return _ENDIAN[byteorder]
    except KeyError as exc:
        raise ValueError('byteorder must be "little" or "big"') from exc


def _flag(value: int, name: str) -> bool:
    if value not in (0, 1):
        raise ValueError(f"{name} bool byte must be 0 or 1, got {value}")
    return bool(value)


def parse_observation(packet: bytes, byteorder: str) -> Observation:
    """Parse one 20-byte observation. packet must already be one whole record."""
    if len(packet) != OBSERVATION_SIZE:
        raise ValueError(f"observation must be {OBSERVATION_SIZE} bytes, got {len(packet)}")

    green_x, green_y, blue_x, blue_y, error_x, error_y, cr, lf = struct.unpack(
        _prefix(byteorder) + "iiiiBBBB", packet
    )
    if bytes((cr, lf)) != _CRLF:
        raise ValueError("observation must end with CR LF")
    
    return Observation(
        green_x=green_x,
        green_y=green_y,
        blue_x=blue_x,
        blue_y=blue_y,
        error_x=_flag(error_x, "Error X"),
        error_y=_flag(error_y, "Error Y"),
    )


def build_position_command(blue_x: int, blue_y: int, byteorder: str) -> bytes:
    """P command, 13 bytes: set the Blue Dot position."""
    packet = struct.pack(_prefix(byteorder) + "3sii2s", b"P\r\n", blue_x, blue_y, _CRLF)
    if len(packet) != POSITION_COMMAND_SIZE:
        raise RuntimeError(f"P command length {len(packet)}")
    return packet


def build_config_command(object_speed: int, object_size: float, byteorder: str) -> bytes:
    """C command, 17 bytes: set object speed and object size."""
    if not 100 <= object_speed <= 500:
        raise ValueError("object speed must be from 100 to 500")
    if not 10 <= object_size <= 100:
        raise ValueError("object size must be from 10 to 100")

    packet = struct.pack(
        _prefix(byteorder) + "3sId2s",
        b"C\r\n",
        object_speed,
        float(object_size),
        _CRLF,
    )
    if len(packet) != CONFIG_COMMAND_SIZE:
        raise RuntimeError(f"C command length {len(packet)}")
    return packet
