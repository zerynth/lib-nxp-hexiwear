################################################################################
# Send Battery Level via Bluetooth
#
# Created: 2017-03-29 14:45:18.159845
#
################################################################################

from nxp.hexiwear.kw40z import kw40z
import streams
import threading

streams.serial()

def toggle_ble():
    try:
        print("Left Button Pressed")
        bt_driver.toggle_adv_mode()
    except Exception as e:
        print("error on left_pressed", e)
    
def print_paircode():
    print("Your Pair Code:",bt_driver.passkey)

pinMode(LED1, OUTPUT)

def check_status():
    print("Device Settings")
    bt_on, bt_touch, bt_link = bt_driver.info()
    print("Bluetooth State: ", ("On" if bt_on == 1 else "Off"))
    digitalWrite(LED1, 0 if bt_on==1 else 1)
    print("Capacitive Button Active: ", ("Left" if bt_touch == 0 else "Right"))
    print("Link State: ", ("Connected" if bt_link == 1 else "Disconnected"))
    while True:
        bt_on_new, bt_touch_new, bt_link_new = bt_driver.info()
        if bt_on_new != bt_on:
            print("Bluetooth State: ", ("On" if bt_on_new == 1 else "Off"))
            digitalWrite(LED1, 0 if bt_on_new==1 else 1)
            bt_on = bt_on_new
        if bt_touch_new != bt_touch:
            print("Capacitive Button Active: ", ("Left" if bt_touch_new == 0 else "Right"))
            bt_touch = bt_touch_new
        if bt_link_new != bt_link:
            print("Link State: ", ("Connected" if bt_link_new == 1 else "Disconnected"))
            bt_link = bt_link_new
        sleep(500)
        
try:
    # Setup ble chip 
    # This setup is referred to kw40z mounted on Hexiwear device
    # The original Hexiwear default application binary file must be pre-loaded inside the kw40z 
    # The application binary file for kw40z can be found here:
    # Link: https://github.com/MikroElektronika/HEXIWEAR/blob/master/SW/binaries/HEXIWEAR_KW40.bin
    print("init...")
    bt_driver = kw40z.KW40Z_HEXI_APP(SERIAL1)
    print("start")
    bt_driver.start()
    # wait for starting the ble chip
    sleep(1000)
    # start thread for check ble status
    thread(check_status)
    # attach callback function to left and right button
    bt_driver.attach_button_left(toggle_ble)
    bt_driver.attach_passkey(print_paircode)
except Exception as e:
    print("error1:", e)
    
level = 0
while True:
    try:
        print(".")
        bt_driver.upd_sensors(battery=level)
        level += 1
        if level > 100:
            level = 0
        sleep(5000)
    except Exception as e:
        print("error2", e)
        sleep(1000)
