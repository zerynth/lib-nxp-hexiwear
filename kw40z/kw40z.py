"""
.. module:: kw40z

************
KW40Z Module
************

The KW40Z SoC can be used in applications as a "BlackBox" modem by simply adding
BLE or IEEE Std. 802.15.4 connectivity to an existing embedded controller system, or
used as a stand-alone smart wireless sensor with embedded application where no host
controller is required. (`datasheet <http://www.nxp.com/assets/documents/data/en/data-sheets/MKW40Z160.pdf>`_).

This module contains the driver for NXP KW40Z Bluetooth Low Energy chip mounted on the Hexiwear device and pre-loaded of the related original default application firmware.
This application exposes all features through a specific serial communication protocol, handles all capacitive touch buttons on Hexiwear device and permits to exchange Hexiwear sensor data via bluetoooth.

.. note :: This module works only if the **HEXIWEAR_KW40.bin** file is loaded on the nxp kw40z chip.
                
                * The binary file can be found `here <https://github.com/MikroElektronika/HEXIWEAR/tree/master/SW/binaries>`_
                * A step-by-step tutorial for loading the binary file inside the kw40z chip can be found `here <https://mcuoneclipse.com/2016/12/07/flashing-and-restoring-the-hexiwear-firmware/>`_

    """

import streams
import threading
import queue 

# gHostInterface
GHI_STARTBYTE_1                 = 0x55
GHI_STARTBYTE_2                 = 0xAA          
GHI_TRAILERBYTE                 = 0x45
GHI_RX_CONFIRM_MASK             = 0x01    
GHI_TX_PACKET_MASK              = 0x10        

GHI_DATASIZE                    = 23
GHI_HEADER_SIZE                 = 4      

GHI_RETRANSMIT_COUNT            = 3    
GHI_RETRANSMIT_TIMEOUT          = 100  

GHI_TX_CONFIRMATION_ENABLE      = 1    
GHI_RX_CONFIRMATION_ENABLE      = 1      

# packet types
PT_PRESS_UP                     = 0        # Electrode touch detected  
PT_PRESS_DOWN                   = 1        # Electrode touch detected  
PT_PRESS_LEFT                   = 2        # Electrode touch detected  
PT_PRESS_RIGHT                  = 3        # Electrode touch detected  
PT_SLIDE                        = 4        # Electrode touch detected  

PT_BATTERY_LEVEL                = 5        # Batterry Service 

PT_ACCEL                        = 6        # Motion Service: Accel 
PT_AMBI_LIGHT                   = 7        # Weather Service: Ambient Light 
PT_PRESSURE                     = 8        # Weather Service: Pressure 

PT_GYRO                         = 9        # Motion Service: Gyro 
PT_TEMPERATURE                  = 10       # Weather Service: Temperature 
PT_HUMIDITY                     = 11       # Weather Service: Humidity 
PT_MAGNET                       = 12       # Motion Service: Magnet 

PT_HEART_RATE                   = 13       # Health Service: Heart Rate 
PT_STEPS                        = 14       # Health Service: Pedometer 
PT_CALORIES                     = 15       # Health Service: Calories counder 

PT_ALERT_IN                     = 16       # Alert Service: Input 
PT_ALERT_OUT                    = 17       # Alert Service: Output 

PT_PASS_DISPLAY                 = 18       # Type for password confirmation 

PT_OTAP_KW40_STARTED            = 19       # OTAP State: OTAP for KW40 Started 
PT_OTAP_MK64_STARTED            = 20       # OTAP State: OTAP for MK64 Started 
PT_OTAP_COMPLETED               = 21       # OTAP State: OTAP completed         
PT_OTAP_FAILED                  = 22       # OTAP State: OTAP failed 

PT_TSI_GROUP_TOGGLE_ACTIVE      = 23       # Toggle active group of electrodes 
PT_TSI_GROUP_GET_ACTIVE         = 24       # Get active group of electrodes 
PT_TSI_GROUP_SEND_ACTIVE        = 25       # Send active group of electrodes 

PT_ADV_MODE_GET                 = 26       # Get bluetooth advertising state
PT_ADV_MODE_SEND                = 27       # Send bluetooth advertising state
PT_ADV_MODE_TOGGLE              = 28       # Toggle bluetooth advertising state

PT_APP_MODE                     = 29       # App Mode Service 

PT_LINK_STATE_GET               = 30       # Get link state (connected / disconnected) 
PT_LINK_STATE_SEND              = 31       # Send link state (connected / disconnected) 

PT_NOTIFICATION                 = 32       # Notifications 

PT_BUILD_VERSION                = 33       # Build version 
    
PT_OK                           = 255      # OK Packet 

# alert
ALERT_IN_TYPE_NOTIFICATION      = 1
ALERT_IN_TYPE_SETTINGS          = 2
ALERT_IN_TYPE_TIME_UPDATE       = 3

# mode
CURRENT_APP_IDLE                = 0  # no app active
CURRENT_APP_SENSOR_TAG          = 2  # sensor tag
CURRENT_APP_HEART_RATE          = 5  # heart rate
CURRENT_APP_PEDOMETER           = 6  # Pedometer 

class KW40Z_HEXI_APP():
    """
.. class:: KW40Z_HEXI_APP(ser)

    Creates an intance of a new KW40Z_HEXI_APP.

    :param ser: Serial used '( SERIAL1, ... )'

    Example: ::

        from nxp.kw40z import kw40z

        ...

        bt_driver = kw40z.KW40Z_HEXI_APP(SERIAL1)
        bt_driver.start()
        ...

    """
    def __init__(self, ser):
        self._ser = streams.serial(ser,baud=230400,stopbits=2,set_default=False)
        self._q = queue.Queue(10)
        self._button_up_callback = None
        self._button_down_callback = None
        self._button_left_callback = None
        self._button_right_callback = None
        self._button_slide_callback = None
        self._alert_callback = None
        self._notification_callback = None
        self._passkey_callback = None

        self.passkey = 0
        self.confirm_recv = False
        self.active_tsi_group = 0
        self.active_adv_mode = 0
        self.link_state = 0
        self.buf = bytearray(1)

    def start(self):
        """
.. method:: start()

        Starts the serial communication with the KW40Z and check the KW40Z status (check if Bluetooth is active, if there are connections with other devices, and which set of capacitive touch buttons are active)

        """
        self._thr_read = thread(self._readloop)
        self._thr_main = thread(self._mainloop)
        self._send_get_active_tsi_group();
        self._send_get_advertisement_mode();
        self._send_get_link_state();

    def attach_button_up(self, callback):
        """
.. method:: attach_button_up(callback)

        Sets the callback function to be executed when Capacitive Button Up on Hexiwear device is pressed.

        """
        self._button_up_callback = callback

    def attach_button_down(self, callback):
        """
.. method:: attach_button_down(callback)

        Sets the callback function to be executed when Capacitive Button Down on Hexiwear device is pressed.

        """
        self._button_down_callback = callback
    
    def attach_button_left(self, callback):
        """
.. method:: attach_button_left(callback)

        Sets the callback function to be executed when Capacitive Button Left on Hexiwear device is pressed.

        """
        self._button_left_callback = callback
    
    def attach_button_right(self, callback):
        """
.. method:: attach_button_right(callback)

        Sets the callback function to be executed when Capacitive Button Right on Hexiwear device is pressed.

        """
        self._button_right_callback = callback
    
    def attach_button_slide(self, callback):
        self._button_slide_callback = callback
    
    def attach_alert(self, callback):
        """
.. method:: attach_alert(callback)

        Sets the callback function to be executed when KW40Z receives an input alert.

        """
        self._alert_callback = callback
    
    def attach_notification(self, callback):
        """
.. method:: attach_notification(callback)

        Sets the callback function to be executed when KW40Z receives a notification.

        """
        self._notification_callback = callback
    
    def attach_passkey(self, callback):
        """
.. method:: attach_passkey(callback)

        Sets the callback function to be executed when KW40Z receives a bluetooth pairing request.

        .. note :: When the KW40Z receives this kind of request it generates a pairing code stored in the passkey class attribute.

        """
        self._passkey_callback = callback

    def _send_get_active_tsi_group(self):
        tx_pack = [GHI_STARTBYTE_1, GHI_STARTBYTE_2, PT_TSI_GROUP_GET_ACTIVE, 0, GHI_TRAILERBYTE]
        self._send_pack(tx_pack, False)

    def _send_get_advertisement_mode(self):
        tx_pack = [GHI_STARTBYTE_1, GHI_STARTBYTE_2, PT_ADV_MODE_GET, 0, GHI_TRAILERBYTE]
        self._send_pack(tx_pack, False)

    def _send_get_link_state(self):
        tx_pack = [GHI_STARTBYTE_1, GHI_STARTBYTE_2, PT_LINK_STATE_GET, 0, GHI_TRAILERBYTE]
        self._send_pack(tx_pack, False)

    def _send_pack_ok(self):
        tx_pack = [GHI_STARTBYTE_1, GHI_STARTBYTE_2, PT_OK, 0, GHI_TRAILERBYTE]
        self._send_pack(tx_pack, False)

    def _send_pack(self, pack, confirm):
        pack[1] = pack[1] | GHI_TX_PACKET_MASK
        if confirm:
            pack[1] = pack[1] | GHI_RX_CONFIRM_MASK
        self._q.put(pack)

    def _send(self, pack):
        confirm = False
        retries = 0
        if (pack[1] & GHI_RX_CONFIRM_MASK) == GHI_RX_CONFIRM_MASK:
            confirm = True
        while True:
            for x in pack:
                self.buf[0] = x
                self._ser.write(self.buf)
            retries += 1
            #print("attempt", retries)
            if GHI_RX_CONFIRMATION_ENABLE and confirm and not self.confirm_recv:
                sleep(GHI_RETRANSMIT_TIMEOUT)
            if not confirm or self.confirm_recv or (retries >= GHI_RETRANSMIT_COUNT):
                break
    
    def _process_pack(self, pack):
        if (pack[1] & GHI_TX_PACKET_MASK) == GHI_TX_PACKET_MASK:
            # this is a tx pack
            pack[1] = pack[1] & ~(GHI_TX_PACKET_MASK)
            self._send(pack)
        else:
            if GHI_TX_CONFIRMATION_ENABLE and (pack[1] & GHI_RX_CONFIRM_MASK) == GHI_RX_CONFIRM_MASK:
                self._send_pack_ok()
            # check rcv pack
            if pack[2] == PT_PRESS_UP:
                #print("pressed up")
                if self._button_up_callback is not None:
                    self._button_up_callback()
            elif pack[2] == PT_PRESS_DOWN:
                #print("pressed down")
                if self._button_down_callback is not None:
                    self._button_down_callback()
            elif pack[2] == PT_PRESS_LEFT:
                #print("pressed left")
                if self._button_left_callback is not None:
                    self._button_left_callback()
            elif pack[2] == PT_PRESS_RIGHT:
                #print("pressed right")
                if self._button_right_callback is not None:
                    self._button_right_callback()
            elif pack[2] == PT_SLIDE:
                #print("slide")
                if self.attach_button_slide is not None:
                    self.attach_button_slide()
            elif pack[2] in (PT_OTAP_COMPLETED, PT_OTAP_FAILED, PT_BUILD_VERSION):
                pass
            elif pack[2] == PT_ALERT_IN:
                #print("alert in")
                if self._alert_callback is not None:
                    self._alert_callback()
            elif pack[2] == PT_PASS_DISPLAY:
                #print("pair code:", ((pack[6]<<16)+(pack[5]<<8)+pack[4]))
                self.passkey = (pack[6]<<16)+(pack[5]<<8)+pack[4]
                if self._passkey_callback is not None:
                    self._passkey_callback()
            elif pack[2] == PT_TSI_GROUP_SEND_ACTIVE:
                self.active_tsi_group = pack[4]
                #print("tsi group", pack[4])
            elif pack[2] == PT_ADV_MODE_SEND:
                self.active_adv_mode = pack[4]
                #print("adv mode", pack[4])
            elif pack[2] == PT_LINK_STATE_SEND:
                self.link_state = pack[4]
                #print("link state", pack[4])
            elif pack[2] == PT_NOTIFICATION:
                #print("notification:", pack[4], pack[5])
                if self._notification_callback is not None:
                    self._notification_callback()
            elif pack[2] == PT_OK:
                pass
            else:
                #print("pack not recognized")
                pass

    def upd_sensors(self, battery=None, accel=None, gyro=None, magn=None, aLight=None, temp=None, humid=None, pres=None):
        """
.. method:: upd_sensors(battery=None, accel=None, gyro=None, magn=None, aLight=None, temp=None, humid=None, press=None)

        Updates Hexiwear sensor data in the KW40Z chip to be readable through any smartphone/tablet/pc bluetooth terminal.

        :param battery: update the battery level value in percentage if passed as argument; default None;
        :param accel: update the acceleration values (list of 3 uint_16 elements for x,y,z axis) if passed as argument; default None;
        :param gyro: update the gyroscope values (list of 3 uint_16 elements for x,y,z axis) if passed as argument; default None;
        :param magn: update the magnetometer values (list of 3 uint_16 elements for x,y,z axis) if passed as argument; default None;
        :param aLight: update the ambient light level value in percentage if passed as argument; default None;
        :param temp: update the temperature value (uint_16) if passed as argument; default None;
        :param humid: update the humidity value (uint_16) if passed as argument; default None;
        :param press: update the pressure value (uint_16) if passed as argument; default None;

        """
        if battery is not None:
            if type(battery) in (PSMALLINT,PINTEGER) and battery >= 0 and battery <= 100:
                # battery value in percentage (uint_8)
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_BATTERY_LEVEL,
                    1,
                    battery,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if accel is not None:
            if type(accel)==PLIST and len(accel) == 3 and all([(x>=0 and x<=65535) for x in accel]):
                # accel in list of three uint_16 elements
                x_msb = (accel[0] >> 8) & 0xFF
                x_lsb = accel[0] & 0xFF
                y_msb = (accel[1] >> 8) & 0xFF
                y_lsb = accel[1] & 0xFF
                z_msb = (accel[2] >> 8) & 0xFF
                z_lsb = accel[2] & 0xFF
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_ACCEL,
                    6, 
                    x_msb,
                    x_lsb,
                    y_msb,
                    y_lsb,
                    z_msb,
                    z_lsb,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if gyro is not None:
            if type(gyro)==PLIST and len(gyro) == 3 and all([(x>=0 and x<=65535) for x in gyro]):
                # gyro in list of three uint_16 elements
                x_msb = (gyro[0] >> 8) & 0xFF
                x_lsb = gyro[0] & 0xFF
                y_msb = (gyro[1] >> 8) & 0xFF
                y_lsb = gyro[1] & 0xFF
                z_msb = (gyro[2] >> 8) & 0xFF
                z_lsb = gyro[2] & 0xFF
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_GYRO,
                    6, 
                    x_msb,
                    x_lsb,
                    y_msb,
                    y_lsb,
                    z_msb,
                    z_lsb,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if magn is not None:
            if type(magn)==PLIST and len(magn) == 3 and all([(x>=0 and x<=65535) for x in magn]):
                # magn in list of three uint_16 elements
                x_msb = (magn[0] >> 8) & 0xFF
                x_lsb = magn[0] & 0xFF
                y_msb = (magn[1] >> 8) & 0xFF
                y_lsb = magn[1] & 0xFF
                z_msb = (magn[2] >> 8) & 0xFF
                z_lsb = magn[2] & 0xFF
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_MAGNET,
                    6, 
                    x_msb,
                    x_lsb,
                    y_msb,
                    y_lsb,
                    z_msb,
                    z_lsb,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if aLight is not None:
            if type(aLight) in (PSMALLINT,PINTEGER) and aLight >= 0 and aLight <= 255:
                # aLight value in percentage (uint_8)
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_AMBI_LIGHT,
                    1,
                    aLight,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if temp is not None:
            if type(temp) in (PSMALLINT,PINTEGER) and temp >= 0 and temp <= 65535:
                # temp value in celtius (uint_16)
                t_msb = (temp >> 8) & 0xFF
                t_lsb = temp & 0xFF
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_TEMPERATURE,
                    2,
                    t_msb,
                    t_lsb,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if humid is not None:
            if type(humid) in (PSMALLINT,PINTEGER) and humid >= 0 and humid <= 65535:
                # humid value in percentage (uint_16)
                h_msb = (humid >> 8) & 0xFF
                h_lsb = humid & 0xFF
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_HUMIDITY,
                    2,
                    h_msb,
                    h_lsb,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if pres is not None:
            if type(pres) in (PSMALLINT,PINTEGER) and pres >= 0 and pres <= 65535:
                # press value in pascal (uint_16)
                p_msb = (pres >> 8) & 0xFF
                p_lsb = pres & 0xFF
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_PRESSURE,
                    2,
                    p_msb,
                    p_lsb,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
    
    def _upd_app_data(self, heart_rate=None, steps=None, calories=None):
        if heart_rate is not None:
            if type(heart_rate) in (PSMALLINT,PINTEGER) and heart_rate >= 0 and heart_rate <= 255:
                # heart_rate value (uint_8)
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_HEART_RATE,
                    1,
                    heart_rate,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if steps is not None:
            if type(steps) in (PSMALLINT,PINTEGER) and steps >= 0 and steps <= 65535:
                # steps value (uint_16)
                s_msb = (steps >> 8) & 0xFF
                s_lsb = steps & 0xFF
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_STEPS,
                    2,
                    s_msb,
                    s_lsb,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError
        if calories is not None:
            if type(calories) in (PSMALLINT,PINTEGER) and calories >= 0 and calories <= 65535:
                # calories value (uint_16)
                c_msb = (calories >> 8) & 0xFF
                c_lsb = calories & 0xFF
                tx_pack = [
                    GHI_STARTBYTE_1,
                    GHI_STARTBYTE_2,
                    PT_CALORIES,
                    2,
                    c_msb,
                    c_lsb,
                    GHI_TRAILERBYTE
                ]
                self._send_pack(tx_pack, True)
            else:
                raise TypeError

    def send_alert(self, data):
        """
.. method:: send_alert()

        Sends alerts from Hexiwear device to the connected smartphone/tablet/pc via Bluetooth

        """
        if type(data)==PLIST and all([(x>=0 and x<=255) for x in data]):
            tx_pack = [
                GHI_STARTBYTE_1,
                GHI_STARTBYTE_2,
                PT_ALERT_OUT,
                len(data),
            ]
            tx_pack.extend(data)
            tx_pack.append(GHI_TRAILERBYTE)
            self._send_pack(tx_pack, True)

    def toggle_adv_mode(self):
        """
.. method:: toggle_adv_mode()

        Changes the status of advertising process. Sets on/off the Bluetooth status.

        """
        tx_pack = [GHI_STARTBYTE_1, GHI_STARTBYTE_2, PT_ADV_MODE_TOGGLE, 0, GHI_TRAILERBYTE]
        self._send_pack(tx_pack, True)

    def toggle_tsi_group(self):
        """
.. method:: toggle_tsi_group()

        Changes active group (pair) of vertical touch sense electrodes. Sets right/left pair capacitive touch buttons.

        """
        tx_pack = [GHI_STARTBYTE_1, GHI_STARTBYTE_2, PT_TSI_GROUP_TOGGLE_ACTIVE, 0, GHI_TRAILERBYTE]
        self._send_pack(tx_pack, True)

    def set_app_mode(self, mode):
        if type(mode) in (PSMALLINT,PINTEGER) and mode in (CURRENT_APP_IDLE, CURRENT_APP_SENSOR_TAG):
            tx_pack = [GHI_STARTBYTE_1, GHI_STARTBYTE_2, PT_APP_MODE, 1, mode, GHI_TRAILERBYTE]
            self._send_pack(tx_pack, True)

    def info(self):
        """
.. method:: info()

        Retrieves the device setting informations regarding the Bluetooth status, which capacitive touch buttons are active, and the connection with other devices status.

        * Bluetooth Status (*bool*): 1 Bluetooth is on, 0 Bluetooth is off;
        * Capacitive Touch Buttons (*bool*): 1 active right pair, 0 acive left pair;
        * Link Status (*bool*): 1 device is connected, 0 device is disconnected.

        Returns bt_on, bt_touch, bt_link

        """
        # print("Device Settings:")
        # print("Bluetooth State: ", ("On" if self.active_adv_mode else "Off"))
        # print("Capacitive Button Active: ", ("Right" if self.active_tsi_group else "Left"))
        # print("Link State: ", ("Connected" if self.active_tsi_group else "Disconnected"))
        return self.active_adv_mode, self.active_tsi_group, self.link_state

    def _mainloop(self):
        while True:
            try:
                pack = self._q.get()
                # ss = ''.join(["%02x " % b for b in pack])
                # print("pack: ",ss)
                self._process_pack(pack)
            except Exception as e:
                print("error in mainloop", e)
                sleep(1000)
            
    def _readloop(self):
        while True:
            try:
                header = self._ser.read(4)
                data = self._ser.read(header[3]+1)
                # str_b = ''.join(["%02x-" % b for b in header])
                # str_d = ''.join(["%02x-" % b for b in data])
                # print("-->",str_b, "data:", str_d)
                pack = header
                pack.extend(data)
                if (GHI_RX_CONFIRMATION_ENABLE or header[2] == PT_OK):
                    self.confirm_recv = True
                self._q.put(pack)
            except Exception as e:
                print("----->",e)
                sleep(1000)

