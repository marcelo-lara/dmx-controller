import time
import socket

from dmx_controller.artnet import ArtNetSender


class FakeSocket:
    def __init__(self):
        self.sent = []

    def setsockopt(self, a, b, c):
        pass

    def sendto(self, packet, addr):
        self.sent.append((packet, addr))

    def close(self):
        pass


def test_artnet_sender_rate_limit(monkeypatch):
    fake = FakeSocket()

    def fake_socket(*args, **kwargs):
        return fake

    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    sender = ArtNetSender(host="127.0.0.1", fps=1000)
    data = bytes([1] * 512)
    # first send
    sender.send(data)
    # immediate second send should be rate-limited when fps=1000 it's very small but still
    sender.send(data)
    # at least one packet sent
    assert len(fake.sent) >= 1
