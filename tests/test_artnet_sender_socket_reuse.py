import socket
from types import SimpleNamespace

from dmx_controller.artnet import ArtNetSender


class CountSocketFactory:
    def __init__(self):
        self.created = 0
        self.sockets = []

    def __call__(self, *a, **k):
        self.created += 1
        s = SimpleNamespace(sent=[], closed=False, setsockopt=lambda *a, **k: None, close=lambda: setattr(s, 'closed', True))
        def sendto(pkt, addr):
            s.sent.append(pkt)
        s.sendto = sendto
        self.sockets.append(s)
        return s


def test_socket_reuse_flag(monkeypatch):
    factory = CountSocketFactory()
    monkeypatch.setattr(socket, "socket", factory)

    sender_reuse = ArtNetSender(reuse_socket=True, fps=1000)
    sender_reuse.send(bytes([0] * 512), force=True)
    sender_reuse.send(bytes([0] * 512), force=True)
    assert factory.created == 1

    factory2 = CountSocketFactory()
    monkeypatch.setattr(socket, "socket", factory2)
    sender_no_reuse = ArtNetSender(reuse_socket=False, fps=1000)
    sender_no_reuse.send(bytes([0] * 512), force=True)
    sender_no_reuse.send(bytes([0] * 512), force=True)
    assert factory2.created == 2
