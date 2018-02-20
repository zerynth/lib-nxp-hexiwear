################################################################################
# Basic example of use for Hexiwear Library
#
# Created: 2017-03-30 07:55:48.081359
#
################################################################################

import streams
from nxp.hexiwear import hexiwear
import threading
import zLogo

streams.serial()

def pressed_up():
    print("Up Button Pressed")
    hexi.vibration(100)
    hexi.enable_bt_upd_sensors()

def pressed_down():
    print("Down Button Pressed")
    hexi.vibration(100)
    hexi.disable_bt_upd_sensors()

def toggle_ble():
    try:
        print("Left Button Pressed")
        hexi.vibration(100)
        hexi.bt_driver.toggle_adv_mode()
    except Exception as e:
        print("error on left_pressed", e)

def toggle_touch():
    try:
        print("Right Button Pressed")
        hexi.vibration(100)
        hexi.bt_driver.toggle_tsi_group()
    except Exception as e:
        print("error on right_pressed", e)
    
def print_paircode():
    # print the pair code in the serial monitor
    print("Your Pair Code:",hexi.bt_driver.passkey)

# used to check the bluetooth status
pinMode(LED2, OUTPUT)

try:
    print("init")
    hexi = hexiwear.HEXIWEAR()
    print("start")
    hexi.fill_screen(0xFFFF,False)
    # attach toggle_ble function to left button (enabled/disabled ble)
    hexi.attach_button_left(toggle_ble)
    # attach toggle_touch function to right button (toggle active button - left/right pair)
    hexi.attach_button_right(toggle_touch)
    # attach pressed_up function to up button - enabled ble update sensor value thread
    hexi.attach_button_up(pressed_up)
    # attach pressed_up function to down button - disabled ble update sensor value thread
    hexi.attach_button_down(pressed_down)
    # attach print_paircode function to bluetooth pairing request
    hexi.attach_passkey(print_paircode)
    print("Ready!")
    print("------------------------------------------------------------------------------")
except Exception as e:
    print(e)
    
    
def read_bt_status():
    while True:
        bt_on, bt_touch, bt_link = hexi.bluetooth_info()
        digitalWrite(LED2, 0 if bt_on==1 else 1)
        sleep(1000)

thread(read_bt_status)

hexi.draw_image(zLogo.zz, 38, 10, 20, 20)
hexi.draw_text("Start!", 0, 60, 96, 20, align=3, color=0xFFFF, background=0x0000, encode=False)

while True:
    try:
        bl, chg = hexi.get_battery_level(chg_state=True)
        print("Battery Level:", bl, "% - Charging:", chg)
        al = hexi.get_ambient_light()
        print("Ambient Light:", al)
        acc = hexi.get_accelerometer_data()
        print("Accelerometer Data [xyz]", acc, "m/s^2")
        magn = hexi.get_magnetometer_data()
        print("Magnetometer Data [xyz]", magn, "uT")
        magn = hexi.get_gyroscope_data()
        print("Gyroscope Data [xyz]", magn, "dps")
        temp = hexi.get_temperature()
        print("Temperature", temp, "*C")
        humid = hexi.get_humidity()
        print("Humidity", humid, "RH%")
        press = hexi.get_pressure()
        print("Pressure", press, "Pa")
        hr = hexi.get_heart_rate()
        print("Heart Rate", hr, "bpm")
        print("------------------------------------------------------------------------------")
        sleep(3000)
    except Exception as e:
        print(e)
        sleep(3000)