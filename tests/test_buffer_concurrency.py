import threading
from dmx_controller.buffer import UniverseBuffer


def worker(buf: UniverseBuffer, ch: int, val: int):
    for _ in range(1000):
        buf.set_channel(ch, val)


def test_concurrent_updates():
    buf = UniverseBuffer(16)
    threads = []
    for i in range(1, 5):
        t = threading.Thread(target=worker, args=(buf, i, i * 10))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # Ensure channels have valid values
    for i in range(1, 5):
        assert buf.get_channel(i) in (i * 10,)
