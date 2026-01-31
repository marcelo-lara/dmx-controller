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


def test_debug_output_limited(monkeypatch, capsys):
    """When Controller.debug=True, a full universe is sent but the debug
    hex dump printed to stdout is limited to the last-configured fixture's
    highest channel.
    """
    fake = FakeSocket()

    # make socket.socket() return our single fake instance
    monkeypatch.setattr(socket, "socket", lambda *a, **k: fake)

    c = dmx_controller.Controller(debug=True, fps=1000)

    # pick a fixture with expected max channel (ParCan L in packaged data)
    f = c.fixtures[1]
    max_ch = max(f.channels.values())
    assert max_ch < 512

    # configure fixture (this should mark it as last-configured)
    f.dimmer = 1.0

    # set a channel beyond the fixture's max to ensure full universe contains it
    c.buffer.set_channel(100, 123)

    # force a send
    c.send_frame(force=True)

    # ensure socket actually got a packet
    assert fake.sent, "no packet sent"
    pkt, addr = fake.sent[-1]

    # the DMX payload is the last 512 bytes of the packet
    payload = pkt[-512:]
    assert len(payload) == 512
    # channel 100 (1-based) is at index 99 (0-based)
    assert payload[99] == 123

    # capture stdout and check debug output
    captured = capsys.readouterr()
    out = captured.out.strip()
    assert out, "no debug output printed"

    parts = out.split()
    # the debug dump should be limited to the fixture's max channel
    assert len(parts) == max_ch
    # first printed byte should correspond to channel 1 (which we did not set hence 00)
    assert parts[0] == "00"
    # the printed bytes should not include channel 100 (so 123 should not appear)
    assert "7B" not in parts  # 123 == 0x7B
