import dmx_controller
import time

dmx_ctrl = dmx_controller.Controller(host="192.168.10.221")


## Start the controller (starts sending DMX data to the ArtNet node)
dmx_ctrl.start()

## Arm all fixtures (send arm values to the fixture channels)
dmx_ctrl.arm_fixtures()


## list available fixtures
fixtures = dmx_ctrl.fixtures

print("Available fixtures:")
for fixture in fixtures:
    ## print basic info about each fixture
    print(f" - {fixture.name} (ID: {fixture.id} Type: {fixture.type})")
    
    ## Prepare the fixture (Arm it by sending arm values to the fixture channels)
    fixture.arm()
    
    ## set the intensity of each fixture to maximum
    fixture.dimmer = 1.0 # the controller will set the value 255 for the dimmer channel

    ## set the color of each fixture to blue
    fixture.color = "blue"

    time.sleep(0.5) # wait a bit to see the changes in the fixture


## Wait 2 seconds
time.sleep(2)

# Send blackout command to all fixtures
dmx_ctrl.blackout()


# Stop the controller (stops sending DMX data to the ArtNet node)
dmx_ctrl.stop()