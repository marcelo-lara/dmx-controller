"""Simple example showing how to use Controller and Engine."""
import argparse
import time

from dmx_controller.artnet import ArtNetSender
from dmx_controller.buffer import UniverseBuffer
from dmx_controller.controller import Controller
from dmx_controller.engine import Engine


class DummySender:
    def __init__(self):
        pass

    def send(self, data, force=False):
        print(f"Dummy send (len={len(data)}) force={force}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    sender = DummySender() if args.dry_run else ArtNetSender(host="127.0.0.1")
    buf = UniverseBuffer()
    ctrl = Controller(sender=sender, buffer=buf)
    # set channel 1 to 200
    buf.set_channel(1, 200)

    engine = Engine(ctrl, fps=10)
    engine.start()
    try:
        time.sleep(1)
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
