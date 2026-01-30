# DMX Controller Library

This package is intended to be used as an ArtNet DMX controller to encapsulate DMX Lighting Fixtures.

## Fixcture Class

### Core Fixture
Every fixture has:
- An ID and Name to identify the fixture.
- A type to identify the subclass to implement the fixture value to channel functions.
- A list of channels address with common types (color, dimmer, shutter, etc.)
- A list of meta channels: functions that are handled by the derived classes.
  Example: to show "blue" a ParCan with RGB channels needs to set the "blue" channel to 255 and "red" and "green" to 0.
  to show "blue" a Moving Head with a Color Wheel needs to set the "color" channel to 150 (value from the color wheel mapping).
  Having this abstraction makes easy to manage different fixture types with the same interface.
- Ready status: ready to emmit light or not; Example: if we set the color to "blue", we need to be sure that dimmer and shutter are set properly.

### ParCan Fixture

- extends the Core Fixture
- to render the color, we need to set the RGB channels (additive color mode)
- To enable these fixtures we need to set the Dimmer Channel to 255 and the Shutter Channel to 255.
- To disable (blackout), all values should be 0

### Moving Head Fixture

- extends the Core Fixture
- to render the color, we need to set the Color Channel to the mapping of the Color Wheel.
- The Pan and Tilt positions are 16bits, so we need to extract MSB and LSB of the value to set both channels.
    - There is a speed channel to "smooth" the movement to the next position. 0 is fast (no smooth), 255 is slow (takes 2 seconds to move to the next position).
- The moving head also features a Gobo Wheel with discrete values for each gobo shape.

## DMX Controller Class

### Core Controller
- Keeps a list of the all the fixtures in the universe.
- Keeps the state values of each channel (last value sent)
- JSON Definition Parser:
    - Parser for `fixtures.json`.
    - Map specific fixture IDs to their starting DMX addresses.

### ArtNet Emmiter

- [ ] **60FPS ArtNet Engine**:
    - Broadcast loop targeting a rock-solid 60FPS (approx. 16.6ms per frame).
    - **Protocol Details**:
        - **Port**: UDP 6454.
        - **Target IP**: `192.168.10.221` (Configurable).
        - **ArtNet Header**: `Art-Net\x00`, OpCode `0x5000` (ArtDMX), Protocol Version `14`.
        - **Universe**: Fixed to Universe `0`.
        - **Payload**: Full 512-channel frame (0-255 per channel).
- [ ] **Thread-Safe Universe Buffer**:
    - In-memory `bytearray(512)` representing the current universe state.
    - Implement a thread-safe/async-safe mechanism (e.g., `asyncio.Lock`) to protect the "soft state" during concurrent updates from the Web UI, Internal API, or background tasks.
- [ ] **State Reconciliation**: Ensure the in-memory state is the "source of truth" and any mid-frame updates are included in the next 60FPS broadcast cycle.
- [ ] **Jitter-Free Timing Loop**:
    - Utilize `time.perf_counter()` for high-precision sleep intervals.
- [ ] **Graceful Shutdown Profile**:
    - Implement termination signal handlers.
    - **Requirement**: Broadcast a final "Blackout" packet (all channels at 0) before process exit.
