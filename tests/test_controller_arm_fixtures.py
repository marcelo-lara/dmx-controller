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


def test_arm_fixtures_sends_arm_values(monkeypatch):
    fake = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    # high fps to avoid rate-limiting
    c = dmx_controller.Controller(fps=1000)

    # ensure fixtures loaded and find some known channels
    fixtures = c.fixtures
    # Head EL-150 has 'shutter' channel 7 with arm value 255 in data
    head = next((f for f in fixtures if f.id == "head_el150"), None)
    assert head is not None
    # ParCan L has 'dim' channel 16 with arm value 255
    parc = next((f for f in fixtures if f.id == "parcan_l"), None)
    assert parc is not None

    # call arm_fixtures which should set channels and send a frame
    c.arm_fixtures(send=True, force=True)

    assert fake.sent, "no packet sent"
    pkt, addr = fake.sent[-1]
    payload = pkt[-512:]
    assert payload[6] == 255  # channel 7 (0-based index 6)
    assert payload[15] == 255  # channel 16 (0-based index 15)
