from dmx_controller.fixture_types import ParCanFixture, MovingHeadFixture


def test_parcan_color_mapping():
    f = ParCanFixture(id="p1", name="Par", type="rgb", channels={"red": 1, "green": 2, "blue": 3})
    updates = f.set_color_rgb(10, 20, 30)
    assert updates == {1: 10, 2: 20, 3: 30}
    assert f.current_values["red"] == 10


def test_moving_head_pan_tilt_mapping():
    f = MovingHeadFixture(
        id="m1",
        name="Head",
        type="moving",
        channels={"pan_msb": 1, "pan_lsb": 2, "tilt_msb": 3, "tilt_lsb": 4},
    )
    updates = f.set_pan_tilt(0x1234, 0x00FF)
    assert updates[1] == 0x12
    assert updates[2] == 0x34
    assert updates[3] == 0x00
    assert updates[4] == 0xFF
    assert f.current_values["pan"] == 0x1234
    assert f.current_values["tilt"] == 0x00FF
