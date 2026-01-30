import socket

from dmx_controller.artnet import ArtNetSender


class FakeSocket:
    def __init__(self):
        self.sent = []

    def setsockopt(self, a, b, c):
        pass

    def sendto(self, packet, addr):
        self.sent.append(packet)

    def close(self):
        pass


def test_sequence_increments(monkeypatch):
    fake = FakeSocket()
    created = {"count": 0}

    def factory(*a, **k):
        created["count"] += 1
        return fake

    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    sender = ArtNetSender(host="127.0.0.1", fps=1000, reuse_socket=True)
    data = bytes([0] * 512)

    sender.send(data, force=True)
    sender.send(data, force=True)
    pkt1 = fake.sent[0]
    pkt2 = fake.sent[1]
    # Sequence byte is at index 12
    assert pkt1[12] == 0
    assert pkt2[12] == 1
