from __future__ import annotations

from time import perf_counter
from typing import Union
import socket
import time

DMX_CHANNELS = 512
DEFAULT_FPS = 60
ARTNET_PORT = 6454

# Art-Net constants
ARTNET_ID = b"Art-Net\x00"
OPCODE_ARTDMX = (0x00, 0x50)  # Little-endian for 0x5000
PROTOCOL_VERSION = (0x00, 0x0e)  # 14


def _build_artdmx_packet(data: Union[bytes, bytearray], universe: int = 0, sequence: int = 0, physical: int = 0) -> bytes:
    """Build a full ArtDMX packet with 512 bytes payload (pad or truncate).

    Sequence and physical fields are single bytes located after the protocol version.
    """
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
    # Sequence (1 byte) + Physical (1 byte)
    packet.extend((sequence & 0xFF, physical & 0xFF))
    # Universe (low byte first)
    packet.extend((universe & 0xFF, (universe >> 8) & 0xFF))
    # Data length hi/lo for DMX_CHANNELS (hi first)
    packet.extend(((DMX_CHANNELS >> 8) & 0xFF, DMX_CHANNELS & 0xFF))
    packet.extend(d)
    return bytes(packet)


class ArtNetSender:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = ARTNET_PORT,
        universe: int = 0,
        fps: int = DEFAULT_FPS,
        timeout: float = 0.2,
        retries: int = 0,
        reuse_socket: bool = True,
        physical: int = 0,
    ):
        self.host = host
        self.port = port
        self.universe = universe
        self._fps = float(fps)
        self._last_send = 0.0
        self._timeout = timeout
        self._retries = int(retries)
        self._reuse_socket = bool(reuse_socket)
        self._physical = int(physical)
        self._sequence = 0

        self._socket = None
        if self._reuse_socket:
            self._socket = self._create_socket()

    def _create_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self._timeout is not None and self._timeout > 0:
            s.settimeout(self._timeout)
        return s

    def send(self, data: Union[bytes, bytearray], force: bool = False) -> None:
        now = perf_counter()
        if not force and (now - self._last_send) < (1.0 / self._fps):
            return
        self._last_send = now

        seq = self._sequence
        pkt = _build_artdmx_packet(data, self.universe, sequence=seq, physical=self._physical)

        attempts = 0
        last_exc = None
        while attempts <= self._retries:
            attempts += 1
            sock = self._socket if self._reuse_socket else self._create_socket()
            try:
                sock.sendto(pkt, (self.host, self.port))
                if not self._reuse_socket:
                    sock.close()
                # increment sequence on successful send
                self._sequence = (self._sequence + 1) & 0xFF
                return
            except Exception as exc:
                last_exc = exc
                # if using ephemeral sockets, ensure we close them
                try:
                    if not self._reuse_socket:
                        sock.close()
                except Exception:
                    pass
                # backoff small amount
                time.sleep(0.01)
                continue
        # if we reach here, all attempts failed
        raise last_exc

    def close(self) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
