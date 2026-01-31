import socket

import dmx_controller


class FakeSocket:
    def __init__(self):
        self.sent = []

    def setsockopt(self, *a, **k):
        pass

    def settimeout(self, *a, **k):
        pass

    def sendto(self, packet, addr):
        self.sent.append((packet, addr))

    def close(self):
        pass


def test_moving_head_controls_write_channels(monkeypatch):
    fake = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    c = dmx_controller.Controller(fps=1000)
    fixtures = c.fixtures
    head = next((f for f in fixtures if f.id == "head_el150"), None)
    assert head is not None

    # set speed, pan and tilt
    head.speed = 100
    head.pan = 32766
    head.tilt = 1280

    # force send
    c.send_frame(force=True)

    assert fake.sent, "no packet sent"
    pkt, addr = fake.sent[-1]
    payload = pkt[-512:]

    # channels from fixtures.json: pan_msb=1, pan_lsb=2, tilt_msb=3, tilt_lsb=4, speed=5
    assert payload[0] == 0x7F  # 32766 >> 8
    assert payload[1] == 0xFE  # 32766 & 0xFF
    assert payload[2] == 0x05  # 1280 >> 8
    assert payload[3] == 0x00  # 1280 & 0xFF
    assert payload[4] == 100   # speed
