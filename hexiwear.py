"""
.. module:: hexiwear_lib

***************
HEXIWEAR Module
***************

This module contains the driver for enabling and handling all Hexiwear onboard sensors and features.
The HEXIWEAR class permits an easier access to the internal peripherals and exposes all functionalities in simple function calls (`wiki <https://docs.mikroe.com/Hexiwear>`_).
    """

import adc
import threading

class HEXIWEAR():
    """

.. class:: HEXIWEAR(battery_en=True, oled_en=True, amb_light_en=True, heart_rate_en=True, temp_humid_en=True, gyro_en=True, acc_magn_en=True, pressure_en=True, bt_driver_en=True)

    Creates an intance of a new HEXIWEAR.

    :param battery_en(*bool*): Flag for enabling the battery level reading feature; default True 
    :param oled_en(*bool*): Flag for enabling the onboard color oled display; default True 
    :param amb_light_en(*bool*): Flag for enabling the ambient light sensor; default True
    :param heart_rate_en(*bool*): Flag for enabling the heart rate sensor; default True 
    :param temp_humid_en(*bool*): Flag for enabling the temperature and humidity sensor; default True 
    :param gyro_en(*bool*): Flag for enabling the onboard gyroscope; default True 
    :param acc_magn_en(*bool*): Flag for enabling the onboard accelerometer and magnetometer; default True 
    :param pressure_en(*bool*): Flag for enabling the pressure sensor; default True 
    :param bt_driver_en(*bool*): Flag for enabling driver for bluetooth features; default True 


    Example: ::

        from nxp.hexiwear import hexiwear

        ...

        
        hexi = hexiwear.HEXIWEAR()
        t = hexi.get_temperature()
        h = hexi.get_humidity()
        ...
        gyro = hexi.get_gyroscope_data()

    """
    def __init__(self, battery_en=True, oled_en=True, amb_light_en=True, heart_rate_en=True, temp_humid_en=True, gyro_en=True, acc_magn_en=True, pressure_en=True, bt_driver_en=True):
        # features activated
        self.battery_en = battery_en
        self.oled_en = oled_en
        self.amb_light_en = amb_light_en
        self.heart_rate_en = heart_rate_en
        self.temp_humid_en = temp_humid_en
        self.gyro_en = gyro_en
        self.acc_magn_en = acc_magn_en
        self.pressure_en = pressure_en
        self.bt_driver_en = bt_driver_en
        self.init_vibro = False
        self.init_leds = False
        # event for updating sensor values
        self.evt = threading.Event()
        self.lock = threading.Lock()
        # battery level
        if self.battery_en:
            self._init_battery_sense()
        # oled display
        if self.oled_en:
            self._init_oled()
        # ambient_light sensor
        if self.amb_light_en:
            self._init_ambient_light()
        # temp_humid sensor
        if self.temp_humid_en:
            self._init_temp_humid()
        # gyroscope
        if self.gyro_en:
            self._init_gyro()
        # accelerometer/magnetometer
        if self.acc_magn_en:
            self._init_acc_magn()
        # pressure sensor
        if self.pressure_en:
            self._init_pressure()
        # bluetooth
        if self.bt_driver_en:
            self._init_bt_driver()
        # heart_rate sensor
        if self.heart_rate_en:
            self._init_heart_rate()
        self._start_internal_threads()
        # wait for initialization 
        sleep(400)        

    def _init_battery_sense(self):
        self.lock.acquire()
        self.chg_pin = D69
        self.bat_sense = A7
        pinMode(self.bat_sense, INPUT_ANALOG)
        pinMode(self.chg_pin, INPUT)
        pinMode(D68, OUTPUT)
        digitalWrite(D68, 0)
        self.lock.release()

    def _init_oled(self):
        self.lock.acquire()
        from solomon.ssd1351 import ssd1351 
        self.oled = ssd1351.SSD1351(SPI0,D57,D58,D59,D71)
        self.oled.init(96,96)
        self.oled.on()
        self.oled.clear()
        self.lock.release()

    def _init_heart_rate(self):
        self.lock.acquire()
        from maxim.max30101 import max30101
        # power on
        pinPowerOn = D70
        digitalWrite(pinPowerOn,HIGH)
        pinMode(pinPowerOn,OUTPUT)
        # init sensor
        self.heart_rate = max30101.MAX30101(I2C0)
        self.heart_rate.start()
        self.heart_rate.init()
        self.heart_rate._thr = -20
        self.heart_rate._dt = 50
        self.heart_rate._prev = 0
        self.heart_rate._smp_buff = [0]*8
        self.heart_rate._cnt = 0
        self.heart_rate.hr_avg = 0
        self.lock.release()
    
    def _init_ambient_light(self):
        self.lock.acquire()
        from ams.tsl2561 import tsl2561
        self.amb_light = tsl2561.TSL2561(I2C0, addr=tsl2561.TSL_I2C_ADDRESS["LOW"])
        self.amb_light.start()
        self.amb_light.init()
        self.lock.release()

    def _init_temp_humid(self):
        self.lock.acquire()
        from meas.htu21d import htu21d
        self.temp_humid = htu21d.HTU21D(I2C0)
        self.temp_humid.start()
        self.temp_humid.init()
        self.lock.release()

    def _init_gyro(self):
        self.lock.acquire()
        from nxp.fxas21002c import fxas21002c
        self.gyro = fxas21002c.FXAS21002C(I2C1)
        self.gyro.start()
        self.gyro.init()
        self.lock.release()

    def _init_acc_magn(self):
        self.lock.acquire()
        from nxp.fxos8700cq import fxos8700cq
        self.acc_magn = fxos8700cq.FXOS8700CQ(I2C1)
        self.acc_magn.start()
        self.acc_magn.init()
        self.lock.release()

    def _init_pressure(self):
        self.lock.acquire()
        from nxp.mpl3115a2 import mpl3115a2
        self.pressure = mpl3115a2.MPL3115A2(I2C1)
        self.pressure.start()
        self.pressure.init()
        self.lock.release()

    def _init_bt_driver(self):
        self.lock.acquire()
        from nxp.hexiwear.kw40z import kw40z
        self.bt_driver = kw40z.KW40Z_HEXI_APP(SERIAL1)
        self.bt_driver.start()
        self.lock.release()

    def _start_internal_threads(self):
        if self.heart_rate_en:
            thread(self._work_hr, self.heart_rate)
            sleep(100)
        if self.bt_driver_en:
            thread(self._upd_sensors)
            sleep(100)

    def _upd_sensors(self):
        while True:
            try:
                self.evt.wait()
                bl = None
                t = None
                h = None
                gyro = None
                acc = None
                magn = None
                al = None
                p = None
                # read sensors
                if self.battery_en:
                    self.lock.acquire()
                    bl, chg = self._battery_level_calc()
                    self.lock.release()
                if self.temp_humid_en:
                    self.lock.acquire()
                    t = self.temp_humid.get_raw_temp()
                    h = self.temp_humid.get_raw_humid()
                    self.lock.release()
                if self.gyro_en:
                    self.lock.acquire()
                    gyro = self.gyro.get_raw_gyro()
                    self.lock.release()
                if self.acc_magn_en:
                    self.lock.acquire()
                    acc = self.acc_magn.get_raw_acc()
                    self.lock.release()
                    self.lock.acquire()
                    magn = self.acc_magn.get_raw_mag()
                    self.lock.release()
                if self.amb_light_en:
                    self.lock.acquire()
                    al = int(self.amb_light.get_lux())&0xFF
                    self.lock.release()
                if self.pressure_en:
                    self.lock.acquire()
                    p = self.pressure.get_raw_pres()>>4
                    self.lock.release()
                self.lock.acquire()
                self.bt_driver.upd_sensors(battery=int(bl), accel=acc, gyro=gyro, magn=magn, aLight=al, temp=t, humid=h, pres=p)
                self.lock.release()
                sleep(5000)
            except Exception as e:
                print("error in upd_sensor thread",e)
                sleep(3000)

    def _check_for_beat(self, smp):
        beat_detected = False
        self.heart_rate._smp_buff[self.heart_rate._cnt] = smp-self.heart_rate._prev
        self.heart_rate._prev=smp
        self.heart_rate._cnt += 1
        if self.heart_rate._cnt == 8:
            self.heart_rate._cnt = 0
        smp_min = min(self.heart_rate._smp_buff)
        if self.heart_rate._smp_buff[(self.heart_rate._cnt-4)&0x7] == smp_min and self.heart_rate._smp_buff[(self.heart_rate._cnt-5)&0x7] != 0 and smp_min <= self.heart_rate._thr:
            if smp_min >= -2000 and smp_min <= -20:
                self.heart_rate._thr = (self.heart_rate._thr + self.heart_rate._smp_buff[(self.heart_rate._cnt-4)&0x7]*.6)/2
            beat_detected = True
            self.heart_rate._smp_buff = [0]*8        
        return beat_detected

    def _work_hr(self, obj):
        cnt = 0
        idx = 0
        hr_avg = 0
        HR_AVG_SIZE = 10
        rate = [0]*HR_AVG_SIZE
        while True:
            try:
                self.lock.acquire()
                val = obj.read_raw_samples(6)
                self.lock.release()
                hr = (val[3]<<16 | val[4]<<8 | val[5])
                cnt += 1
                res = self._check_for_beat(hr)
                if res:
                    dt = cnt*obj._dt
                    cnt = 0
                    bpm = 60000/dt
                    if bpm < 255 and bpm > 20:
                        rate[idx] = bpm
                        idx += 1
                        if idx == HR_AVG_SIZE:
                            idx = 0
                        hr_avg = 0
                        for rr in rate:
                            hr_avg += rr
                        self.heart_rate.hr_avg = hr_avg/HR_AVG_SIZE
                if cnt >= 3000/obj._dt:
                    cnt = 0
                    self.heart_rate._thr = -20
                    rate = [0]*HR_AVG_SIZE
                    self.heart_rate.hr_avg = 0
                obj.clear_fifo()
                sleep(obj._dt)
            except Exception as e:
                print("ErrorT", e)
                sleep(1000)

    def _battery_level_calc(self, chg_state=False):
        chg = None
        if chg_state:
            chg = digitalRead(self.chg_pin)
            if chg == 0:
                chg = True
            else:
                chg = False
        val = adc.read(self.bat_sense)
        bat = val*(3.3/65535.0)*1000
        if bat > 2670:
            bat_level = 100
        elif bat > 2500:
            bat_level = 50*(bat-2500)/170.0
            bat_level += 50
        elif bat > 2430:
            bat_level = 20*(bat-2430)/70.0
            bat_level += 30
        elif bat > 2370:
            bat_level = 20*(bat-2370)/60.0
            bat_level += 10
        else:
            bat_level = 0
        return bat_level, chg

    def get_battery_level(self, chg_state=False):
        """

.. method:: get_battery_level(chg_state)

        If battery level reading feature is enabled; retrieves the current battery level in percentage and the charging battery status if *chg=True* is provided. 
        
        :param chg_state(*bool*): flag for enabling the battery charging status reading; default False

        Returns battery_level or battery_level, charging_status or None

        """
        if self.battery_en:
            self.lock.acquire()
            bat_level, chg = self._battery_level_calc(chg_state)
            self.lock.release()
            if chg_state:
                return bat_level, chg
            else:
                return bat_level
        else:
            return None

    def get_pressure(self):
        """

.. method:: get_pressure()

        If pressure sensor is enabled; retrieves the current pressure data from the onboard sensor as calibrate value in Pa.
        
        Returns pressure or None

        """
        if self.pressure_en:
            self.lock.acquire()
            pressure = self.pressure.get_pres()
            self.lock.release()
            return pressure
        else:
            return None

    def get_temperature(self):
        """

.. method:: get_temperature()

        If temperature and humidity sensor is enabled; retrieves the current temperature data from the onboard sensor as calibrate value in °C.
        
        Returns temperature or None

        """
        if self.temp_humid_en:
            self.lock.acquire()
            temperature = self.temp_humid.get_temp()
            self.lock.release()
            return temperature
        else:
            return None

    def get_humidity(self):
        """

.. method:: get_humidity()

        If temperature and humidity sensor is enabled; retrieves the current humidity data from the onboard sensor as calibrate value in %RH.
        
        Returns humidity or None

        """
        if self.temp_humid_en:
            self.lock.acquire()
            humidity = self.temp_humid.get_humid()
            self.lock.release()
            return humidity
        else:
            return None

    def get_accelerometer_data(self):
        """

.. method:: get_accelerometer_data()

        If accelerometer and magnetometer are enabled; retrieves the current accelerometer data from the onboard sensor in m/s^2 as a tuple of X, Y, Z values.
        
        Returns [acc_x, acc_y, acc_z] or None

        """
        if self.acc_magn_en:
            self.lock.acquire()
            accelerometer = self.acc_magn.get_acc()
            self.lock.release()
            return accelerometer
        else:
            return None

    def get_magnetometer_data(self):
        """

.. method:: get_magnetometer_data()

        If accelerometer and magnetometer are enabled; retrieves the current magnetometer data from the onboard sensor in uT as a tuple of X, Y, Z values.
        
        Returns [magn_x, magn_y, magn_z] or None

        """
        if self.acc_magn_en:
            self.lock.acquire()
            magnetometer = self.acc_magn.get_mag()
            self.lock.release()
            return magnetometer
        else:
            return None

    def get_gyroscope_data(self):
        """

.. method:: get_gyroscope_data()

        If gyroscope is enabled; retrieves the current gyroscope data from the onboard sensor in degrees per second as a tuple of X, Y, Z values.
        
        Returns [gyro_x, gyro_y, gyro_z] or None

        """
        if self.gyro_en:
            self.lock.acquire()
            gyroscope = self.gyro.get_gyro()
            self.lock.release()
            return gyroscope
        else:
            return None

    def get_ambient_light(self):
        """

.. method:: get_ambient_light()

        If ambient light sensor is enabled; Converts the raw sensor values to the standard SI lux equivalent.

        Returns lux or None

        """
        if self.amb_light_en:
            self.lock.acquire()
            amb_lihght = self.amb_light.get_lux()
            self.lock.release()
            return amb_lihght
        else:
            return None

    def get_heart_rate(self):
        """

.. method:: get_heart_rate()

        If heart rate sensor is enabled; retrieves the current heart rate from the onboard sensor as value in bpm (beat per minute).

        Returns heart_rate or None

        """
        if self.heart_rate_en:
            return int(self.heart_rate.hr_avg)
        else:
            return None

    def get_altitude(self):
        """

.. method:: get_altitude()

        If pressure sensor is enabled; calculates, from measured pressure, the current altitude data as value in meters.
        
        Returns altitude or None

        """
        if self.pressure_en:
            self.lock.acquire()
            altitude = self.pressure.get_alt()
            self.lock.release()
            return altitude
        else:
            return None

    def attach_button_up(self, callback):
        """
.. method:: attach_button_up(callback)

        If bluetooth driver is enabled; sets the callback function to be executed when Capacitive Button Up on Hexiwear device is pressed.

        """
        if self.bt_driver_en:
            self.bt_driver.attach_button_up(callback)

    def attach_button_down(self, callback):
        """
.. method:: attach_button_down(callback)

        If bluetooth driver is enabled; sets the callback function to be executed when Capacitive Button Down on Hexiwear device is pressed.

        """
        if self.bt_driver_en:
            self.bt_driver.attach_button_down(callback)

    def attach_button_left(self, callback):
        """
.. method:: attach_button_left(callback)

        If bluetooth driver is enabled; sets the callback function to be executed when Capacitive Button Left on Hexiwear device is pressed.

        """
        if self.bt_driver_en:
            self.bt_driver.attach_button_left(callback)

    def attach_button_right(self, callback):
        """
.. method:: attach_button_right(callback)

        If bluetooth driver is enabled; sets the callback function to be executed when Capacitive Button Right on Hexiwear device is pressed.

        """
        if self.bt_driver_en:
            self.bt_driver.attach_button_right(callback)
    
    def attach_passkey(self, callback):
        """
.. method:: attach_passkey(callback)

        If bluetooth driver is enabled; sets the callback function to be executed when KW40Z receives a bluetooth pairing request.

        .. note :: When the KW40Z receives this kind of request it generates a pairing code stored in the passkey KW40Z class attribute of bt_driver internal instance.

        """
        if self.bt_driver_en:
            self.bt_driver.attach_passkey(callback)

    def bluetooth_on(self):
        """
.. method:: bluetooth_on()

        If bluetooth driver is enabled; turns on the bluetooth features.

        """
        if self.bt_driver_en:
            self.lock.acquire()
            bt_on, bt_touch, bt_link = self.bt_driver.info()
            if bt_on == 0:
                self.bt_driver.toggle_adv_mode()
            self.lock.release()

    def bluetooth_off(self):
        """
.. method:: bluetooth_off()

        If bluetooth driver is enabled; turns off the bluetooth features.

        """
        if self.bt_driver_en:
            self.lock.acquire()
            bt_on, bt_touch, bt_link = self.bt_driver.info()
            if bt_on == 1:
                self.bt_driver.toggle_adv_mode()
            self.lock.release()

    def right_capacitive_buttons_active(self):
        """
.. method:: right_capacitive_buttons_active()

        If bluetooth driver is enabled; turns active the right pair of capacitive buttons.

        """
        if self.bt_driver_en:
            self.lock.acquire()
            bt_on, bt_touch, bt_link = self.bt_driver.info()
            if bt_touch == 0:
                self.bt_driver.toggle_tsi_group()
            self.lock.release()

    def left_capacitive_buttons_active(self):
        """
.. method:: right_capacitive_buttons_active()

        If bluetooth driver is enabled; turns active the left pair of capacitive buttons.

        """
        if self.bt_driver_en:
            self.lock.acquire()
            bt_on, bt_touch, bt_link = self.bt_driver.info()
            if bt_touch == 1:
                self.bt_driver.toggle_tsi_group()
            self.lock.release()

    def bluetooth_info(self):
        """
.. method:: bluetooth_info()

        If bluetooth driver is enabled; retrieves the bluetooth chip informations regarding the status, which capacitive touch buttons are active, and the "connection with other devices" status.

        * Bluetooth Status (*bool*): 1 Bluetooth is on, 0 Bluetooth is off;
        * Capacitive Touch Buttons (*bool*): 1 active right pair, 0 acive left pair;
        * Link Status (*bool*): 1 device is connected, 0 device is disconnected.

        Returns bt_on, bt_touch, bt_link

        """
        if self.bt_driver_en:
            self.lock.acquire()
            bt_on, bt_touch, bt_link = self.bt_driver.info()
            self.lock.release()
            return bt_on, bt_touch, bt_link

    def enable_bt_upd_sensors(self):
        """
.. method:: enable_bt_upd_sensors()

        If bluetooth driver is enabled; enables the automatic update of all sensor values in the KW40Z bluetooth chip to be readable through any smartphone/tablet/pc bluetooth terminal (once every 5 seconds).

        """
        if self.bt_driver_en:
            self.evt.set()

    def disable_bt_upd_sensors(self):
        """
.. method:: disable_bt_upd_sensors()

        If bluetooth driver is enabled; disables the automatic update of all sensor values in the KW40Z bluetooth chip.

        """
        if self.bt_driver_en:
            self.evt.clear()

    def display_on(self):
        """
.. method:: display_on()

        If color oled display is enabled; turns on the onboard display.

        """
        if self.oled_en:
            self.lock.acquire()
            self.oled.on()
            self.lock.release()

    def display_off(self):
        """
.. method:: display_off()

        If color oled display is enabled; turns off the onboard display.

        """
        if self.oled_en:
            self.lock.acquire()
            self.oled.off()
            self.lock.release()

    def clear_display(self):
        """
.. method:: clear_display()

        If color oled display is enabled; clears the onboard display.

        """
        if self.oled_en:
            self.lock.acquire()
            self.oled.clear()
            self.lock.release()

    def fill_screen(self, color, encode=True):
        """
.. method:: fill_screen(color, encode=True)

        If color oled display is enabled; fills the entire display with color code provided as argument.

        :param color: hex color code for the screen
        :param encode(*bool*): flag for enabling the color encoding; default True

        .. note:: The onboard color oled is a 65K color display, so if a stadard hex color code (24 bit) is provided
                  it is necessary to encode it into a 16 bit format.
                  
                  If a 16 bit color code is provided, the encode flag must be set to False.

        """
        if self.oled_en:
            self.lock.acquire()
            self.oled.fill_screen(color, encode)
            self.lock.release()

    def fill_rect(self, x, y, w, h, color, encode=True):
        """
.. method:: fill_rect(x, y, w, h, color, encode=True)

        If color oled display is enabled; draws a rectangular area in the screen colored with the color code provided as argument.

        :param x: x-coordinate for left high corner of the rectangular area
        :param y: y-coordinate for left high corner of the rectangular area
        :param w: width of the rectangular area
        :param h: height of the rectangular area
        :param color: hex color code for the rectangular area
        :param encode(*bool*): flag for enabling the color encoding; default True

        .. note:: The onboard color oled is a 65K color display, so if a stadard hex color code (24 bit) is provided
                  it is necessary to encode it into a 16 bit format.
                  
                  If a 16 bit color code is provided, the encode flag must be set to False.

        """
        if self.oled_en:
            self.lock.acquire()
            self.oled.fill_rect(x, y, w, h, color, encode)
            self.lock.release()
    
    def draw_image(self, image, x, y, w, h):
        """
.. method:: draw_image(image, x, y, w, h)

        If color oled display is enabled; draws a rectangular area in the screen colored with the color code provided as argument.

        :param image: image to draw in the oled display converted to hex array format and passed as bytearray
        :param x: x-coordinate for left high corner of the image
        :param y: y-coordinate for left high corner of the image
        :param w: width of the image
        :param h: height of the image
        
        .. note :: To obtain a converted image in hex array format, you can go and use this `online tool <http://www.digole.com/tools/PicturetoC_Hex_converter.php>`_.
                   
                   After uploading your image, you can resize it setting the width and height fields; you can also choose the code format (HEX:0x recommended) and the color format
                   (65K color for this display).
                   
                   Clicking on the "Get C string" button, the tool converts your image with your settings to a hex string that you can copy and paste inside a bytearray in your project and privide to this function.

        """
        if self.oled_en:
            self.lock.acquire()
            self.oled.draw_img(image, x, y, w, h)
            self.lock.release()

    def draw_pixel(self, x, y, color, encode=True):
        """
.. method:: draw_pixel(x, y, color, encode=True)

        If color oled display is enabled; draws a single pixel in the screen colored with the color code provided as argument.

        :param x: pixel x-coordinate
        :param y: pixel y-coordinate
        :param color: hex color code for the pixel
        :param encode(*bool*): flag for enabling the color encoding; default True

        .. note:: The onboard color oled is a 65K color display, so if a stadard hex color code (24 bit) is provided
                  it is necessary to encode it into a 16 bit format.
                  
                  If a 16 bit color code is provided, the encode flag must be set to False.

        """
        if self.oled_en:
            self.lock.acquire()
            self.oled.draw_pixel(x, y, color, encode)
            self.lock.release()

    def draw_text(self, text, x=None, y=None, w=None, h=None, color=None, align=None, background=None, encode=True):
        """
.. method:: draw_text(text, x=None, y=None, w=None, h=None, color=None, align=None, background=None, encode=True)

        If color oled display is enabled; prints a string inside a text box in the screen.

        :param text: string to be written in the display
        :param x: x-coordinate for left high corner of the text box; default None
        :param y: y-coordinate for left high corner of the text box; default None
        :param w: width of the text box; default None
        :param h: height of the text box; default None
        :param color: hex color code for the font; default None
        :param align: alignment of the text inside the text box (1 for left alignment, 2 for right alignment, 3 for center alignment); default None
        :param background: hex color code for the background; default None
        :param encode(*bool*): flag for enabling the color encoding of the font and background color; default True

        .. note:: The onboard color oled is a 65K color display, so if a stadard hex color code (24 bit) is provided
                  it is necessary to encode it into a 16 bit format.
                  
                  If a 16 bit color code is provided, the encode flag must be set to False.

        .. note:: If only text argument is provided, an automatic text box is created with the following values:

                    * x = 0
                    * y = 0
                    * w = min text width according to the font
                    * h = max char height according to the font
                    * color = 0xFFFF
                    * align = 3 (centered horizontally)
                    * background = 0x4471

        """
        if self.oled_en:
            self.lock.acquire()
            self.oled.draw_text(text, x, y, w, h, color, align, background, encode)
            self.lock.release()
    
    def vibration(self, ms):
        """
.. method:: vibration(ms)

        Turns on the vibration motor for *ms* milliseconds.

        :param ms: motor vibration duration

        """
        if not self.init_vibro:
            self.init_vibro = True
            self.vibro = D67
            pinMode(self.vibro, OUTPUT) 
        digitalWrite(self.vibro, 1)
        sleep(ms)
        digitalWrite(self.vibro, 0)

    def leds_on(self):
        """
.. method:: leds_on()

        Turns on the rgb onboard led (white light).

        """
        if not self.init_leds:
            self.init_leds = True
            self.led_red = LED0
            pinMode(self.led_red, OUTPUT) 
            self.led_green = LED1
            pinMode(self.led_green, OUTPUT) 
            self.led_blue = LED2
            pinMode(self.led_blue, OUTPUT) 
        digitalWrite(self.led_red, 0)
        digitalWrite(self.led_green, 0)
        digitalWrite(self.led_blue, 0)

    def leds_off(self):
        """
.. method:: leds_off()

        Turns off the rgb onboard led.

        """
        if not self.init_leds:
            self.init_leds = True
            self.led_red = LED0
            pinMode(self.led_red, OUTPUT) 
            self.led_green = LED1
            pinMode(self.led_green, OUTPUT) 
            self.led_blue = LED2
            pinMode(self.led_blue, OUTPUT) 
        digitalWrite(self.led_red, 1)
        digitalWrite(self.led_green, 1)
        digitalWrite(self.led_blue, 1)
