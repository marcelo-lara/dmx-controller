from __future__ import annotations

from time import perf_counter
from typing import Union
import socket

DMX_CHANNELS = 512
DEFAULT_FPS = 60
ARTNET_PORT = 6454

# Art-Net constants
ARTNET_ID = b"Art-Net\x00"
OPCODE_ARTDMX = (0x00, 0x50)  # Little-endian for 0x5000
PROTOCOL_VERSION = (0x00, 0x0e)  # 14


def _build_artdmx_packet(data: Union[bytes, bytearray], universe: int = 0) -> bytes:
    """Build a full ArtDMX packet with 512 bytes payload (pad or truncate)."""
    # Ensure payload is exactly DMX_CHANNELS bytes
    if isinstance(data, (bytes, bytearray)):
        d = bytes(data)
    else:
        d = bytes(data)

    if len(d) < DMX_CHANNELS:
        d = d + bytes(DMX_CHANNELS - len(d))
    else:
        d = d[:DMX_CHANNELS]

    packet = bytearray()
    packet.extend(ARTNET_ID)
    packet.extend(OPCODE_ARTDMX)
    packet.extend(PROTOCOL_VERSION)
    # Sequence + Physical = 2 bytes (we keep zeroed)
    packet.extend((0x00, 0x00))
    # Universe (low byte first as in original) - keep consistent
    packet.extend((universe & 0xFF, (universe >> 8) & 0xFF))
    # Data length hi/lo for DMX_CHANNELS (hi first)
    packet.extend(((DMX_CHANNELS >> 8) & 0xFF, DMX_CHANNELS & 0xFF))
    packet.extend(d)
    return bytes(packet)


class ArtNetSender:
    def __init__(self, host: str = "127.0.0.1", port: int = ARTNET_PORT, universe: int = 0, fps: int = DEFAULT_FPS):
        self.host = host
        self.port = port
        self.universe = universe
        self._fps = fps
        self._last_send = 0.0

    def send(self, data: Union[bytes, bytearray], force: bool = False) -> None:
        now = perf_counter()
        if not force and (now - self._last_send) < (1.0 / self._fps):
            return
        self._last_send = now

        packet = _build_artdmx_packet(data, self.universe)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.sendto(packet, (self.host, self.port))
            sock.close()
        except Exception as exc:  # Keep minimal: let caller catch
            raise
