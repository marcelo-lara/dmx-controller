from dmx_controller.artnet import _build_artdmx_packet, DMX_CHANNELS


def test_artdmx_packet_length_and_header():
    payload = bytes([1, 2, 3])
    pkt = _build_artdmx_packet(payload, universe=1)
    assert pkt.startswith(b"Art-Net\x00")
    # OpCode should be present (0x5000 little-endian: 00 50)
    assert pkt[8:10] == bytes((0x00, 0x50))
    # Protocol version bytes
    assert pkt[10:12] == bytes((0x00, 0x0e))
    # Data length should be DMX_CHANNELS (hi, lo)
    data_len_hi = pkt[16]
    data_len_lo = pkt[17]
    data_len = (data_len_hi << 8) | data_len_lo
    assert data_len == DMX_CHANNELS
    # Payload occupies the remainder
    assert len(pkt) == 18 + DMX_CHANNELS
