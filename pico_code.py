import digitalio
import board
import usb_hid
import time
import storage
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.consumer_control import ConsumerControl

class RotaryEncoder:
    def __init__(self, _id, clk_pin, dt_pin, sw_pin, modes=1):
        self.clk = digitalio.DigitalInOut(clk_pin)
        self.clk.direction = digitalio.Direction.INPUT

        self.dt = digitalio.DigitalInOut(dt_pin)
        self.dt.direction = digitalio.Direction.INPUT

        self.sw = digitalio.DigitalInOut(sw_pin)
        self.sw.direction = digitalio.Direction.INPUT
        self.sw.pull = digitalio.Pull.UP

        self.cc = ConsumerControl(usb_hid.devices)
        self.keyboard = Keyboard(usb_hid.devices)

        self.rotate_delay = False
        self.total_modes = modes
        self.current_mode = 0
        
        self.id = _id

    def millis(self):
        return time.monotonic() * 1000

    def log(self, message):
        print(self.id, message)

    def ccw(self):
        self.log("CCW")

    def cw(self):
        self.log("CW")

    def long_press(self):
        self.log("LONG_PRESS")

    def short_press(self):
        self.log("SHORT_PRESS")
        
    def reset_keyboard(self, force=False):
        if force:
            time.sleep(1)
            self.log("Resetting keyboard..")
            self.cc = ConsumerControl(usb_hid.devices)
            self.keyboard = Keyboard(usb_hid.devices)
        else:
            if self.cc is None:
                time.sleep(1)
                self.log("ConsumerControl not initialized. Trying again..")
                self.cc = ConsumerControl(usb_hid.devices)
            if self.keyboard is None:
                time.sleep(1)
                self.log("Keyboard not initialized. Trying again..")
                self.keyboard = Keyboard(usb_hid.devices)

    def loop(self):
        current_state = self.clk.value
        # Rotation
        if not current_state:
            if not self.rotate_delay:
                self.reset_keyboard()
                try:
                    if self.dt.value != current_state:
                        self.cw()
                    else:
                        self.ccw()
                except Exception as e:
                    print("An error occurred: {}".format(e))
                    self.reset_keyboard(True)

                self.rotate_delay = True
        else:
            self.rotate_delay = False

        # Press
        if self.sw.value == 0:
            press_time = self.millis()
            time.sleep(0.2)
            long_pressed = False
            self.reset_keyboard()
            try:
                while self.sw.value == 0:
                    if self.millis() - press_time > 1000 and not long_pressed:
                        long_pressed = True
                        self.long_press()

                if not long_pressed:
                    self.short_press()

            except Exception as e:
                print("An error occurred: {}".format(e))
                self.reset_keyboard(True)

if __name__ == "__main__":
    # Create instances of RotaryEncoder for each encoder
    encoder4 = RotaryEncoder(4, board.GP0, board.GP1, board.GP2)
    encoder3 = RotaryEncoder(3, board.GP4, board.GP5, board.GP6)
    encoder2 = RotaryEncoder(2, board.GP8, board.GP9, board.GP10)
    encoder1 = RotaryEncoder(1, board.GP12, board.GP13, board.GP14)

    while True:
        try:
            encoder1.loop()
            encoder2.loop()
            encoder3.loop()
            encoder4.loop()
            # Add more encoder loops as needed
        except Exception as e2:
            print("An error in the loop occurred: {}".format(e2))
            encoder1.reset_keyboard(True)
            encoder2.reset_keyboard(True)
            encoder3.reset_keyboard(True)
            encoder4.reset_keyboard(True)
