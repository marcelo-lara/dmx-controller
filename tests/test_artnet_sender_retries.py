import socket

from dmx_controller.artnet import ArtNetSender


class FlakySocket:
    def __init__(self):
        self.sent = []
        self.calls = 0

    def setsockopt(self, a, b, c):
        pass

    def sendto(self, packet, addr):
        self.calls += 1
        if self.calls == 1:
            raise OSError("network error")
        self.sent.append(packet)

    def close(self):
        pass


def test_retries(monkeypatch):
    fake = FlakySocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    sender = ArtNetSender(host="127.0.0.1", fps=1000, retries=1, reuse_socket=True)
    data = bytes([0] * 512)
    sender.send(data, force=True)
    # should have succeeded on second attempt
    assert fake.calls == 2
    assert len(fake.sent) == 1
