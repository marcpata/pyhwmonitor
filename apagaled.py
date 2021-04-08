from libs.ledble import ledBle
leds = ledBle()
leds.connect_ble()
leds.set_state('off')
leds.disconnect_ble()
