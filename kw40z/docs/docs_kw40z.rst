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

    
.. class:: KW40Z_HEXI_APP(serdrv)

    Creates an intance of a new KW40Z_HEXI_APP.

    :param serdrv: Serial used '( SERIAL1, ... )'

    Example: ::

        from nxp.kw40z import kw40z

        ...

        bt_driver = kw40z.KW40Z_HEXI_APP(SERIAL1)
        bt_driver.start()
        ...

    
.. method:: start()

        Starts the serial communication with the KW40Z and check the KW40Z status (check if Bluetooth is active, if there are connections with other devices, and which set of capacitive touch buttons are active)

        
.. method:: attach_button_up(callback)

        Sets the callback function to be executed when Hexiwear Up Button is pressed.

        
.. method:: attach_button_down(callback)

        Sets the callback function to be executed when Hexiwear Down Button is pressed.

        
.. method:: attach_button_left(callback)

        Sets the callback function to be executed when Hexiwear Left Button is pressed.

        
.. method:: attach_button_right(callback)

        Sets the callback function to be executed when Hexiwear Right Button is pressed.

        
.. method:: attach_alert(callback)

        Sets the callback function to be executed when KW40Z receives an input alert.

        
.. method:: attach_notification(callback)

        Sets the callback function to be executed when KW40Z receives a notification.

        
.. method:: attach_passkey(callback)

        Sets the callback function to be executed when KW40Z receives a bluetooth pairing request.

        .. note :: When the KW40Z receives this kind of request it generates a pairing code stored in the passkey class attribute.

        
.. method:: upd_sensors(battery=None, accel=None, gyro=None, magn=None, aLight=None, temp=None, humid=None, press=None)

        Updates Hexiwear sensor data in the KW40Z chip to be readable through any smartphone/tablet/pc bluetooth terminal.

        :param battery: update the battery level value in percentage if passed as argument; default None;
        :param accel: update the acceleration values (list of 3 int_16 elements for x,y,z axis) if passed as argument; default None;
        :param gyro: update the gyroscope values (list of 3 int_16 elements for x,y,z axis) if passed as argument; default None;
        :param magn: update the magnetometer values (list of 3 int_16 elements for x,y,z axis) if passed as argument; default None;
        :param aLight: update the ambient light level value in percentage if passed as argument; default None;
        :param temp: update the temperature value (int_16) if passed as argument; default None;
        :param humid: update the humidity value (int_16) if passed as argument; default None;
        :param press: update the pressure value (int_16) if passed as argument; default None;

        
.. method:: send_alert()

        Sends alerts from Hexiwear device to the connected smartphone/tablet/pc via Bluetooth

        
.. method:: toggle_adv_mode()

        Changes the status of advertising process. Sets on/off the Bluetooth status.

        
.. method:: toggle_tsi_group()

        Changes active group (pair) of vertical touch sense electrodes. Sets right/left pair capacitive touch buttons.

        
.. method:: info()

        Retrieves the device setting informations regarding the Bluetooth status, which capacitive touch buttons are active, and the connection with other devices status.

        * Bluetooth Status (*bool*): 1 Bluetooth is on, 0 Bluetooth is off;
        * Capacitive Touch Buttons (*bool*): 1 active right pair, 0 acive left pair;
        * Link Status (*bool*): 1 device is connected, 0 device is disconnected.

        Returns bt_on, bt_touch, bt_link

        
