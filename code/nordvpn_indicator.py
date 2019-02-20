#!/usr/bin/python
"""
Adds icon to notification tray that allows for connecting
and disconnecting to NordVPN
"""

import os
import re
import signal
import subprocess
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from enum import Enum


APPINDICATOR_ID = 'nordvpn_tray_icon'
TIMER_SECONDS = 5.0

class VPN_STATUS(Enum):
    CONNECTED = 0
    DISCONNECTED = 1
    WAITING = 2

class Indicator(object):
    """
    Indicator provides tray icon with menu, handles user interaction
    and sets a timer for checking the VPN status

    Args:
        nordvpn: Nordvpn instance for connecting/disconnecting and
        checking the status of the connection

    Returns:
        Instance of Indicator class
    """
    def __init__(self, nordvpn):
        # Set references within both classes
        nordvpn.attach(self)
        self.nordvpn = nordvpn

        # Add indicator
        self.indicator = appindicator.Indicator.new(
            APPINDICATOR_ID,
            self.get_icon_path(False),
            appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

        # Set recurrent timer for checking VPN status
        self.status_check_loop()

        notify.init(APPINDICATOR_ID)
        gtk.main()

    def status_check_loop(self):
        """
        Sets timer in recurrent loop that executes a VPN status check
        """
        self.update()
        self.timer = threading.Timer(TIMER_SECONDS, self.status_check_loop)
        self.timer.start()

    def update(self):
        """
        Updates the icon and the menu status item
        """
        self.nordvpn.status_check(None)
        self.status_label.set_label(self.nordvpn.get_status())
        self.indicator.set_icon(self.get_icon_path(self.nordvpn.is_connected()))
        self.update_settings_menu()

    @staticmethod
    def get_icon_path(connected):
        """
        Returns the correct icon in response to the connection status

        Args:
            connected: Connected status VPN_STATUS object
        """
        if connected == VPN_STATUS.CONNECTED:
            filename = 'nordvpn_connected.png'
        elif connected == VPN_STATUS.DISCONNECTED:
            filename = 'nordvpn_disconnected.png'
        else:
            filename = 'nordvpn_waiting.png'
        return os.path.dirname(os.path.realpath(__file__)) + '/' + filename

    def build_menu(self):
        """
        Builds menu for the tray icon
        """
        menu = gtk.Menu()

        # Create a Connect submenu
        menu_connect = gtk.Menu()
        item_connect = gtk.MenuItem('Connect')
        item_connect.set_submenu(menu_connect)

        # First item is to connect automatically
        item_connect_auto = gtk.MenuItem('Auto')
        item_connect_auto.connect('activate', self.auto_connect_cb)
        menu_connect.append(item_connect_auto)

        menu.append(item_connect)

        countries = self.nordvpn.get_countries()
        countries_menu = gtk.Menu()
        item_connect_country = gtk.MenuItem('Countries')
        item_connect_country.set_submenu(countries_menu)
        for c in countries:
            item = gtk.MenuItem(c.replace('_',' '))
            item.connect('activate', self.country_connect_cb)
            countries_menu.append(item)
        menu_connect.append(item_connect_country)

        item_disconnect = gtk.MenuItem('Disconnect')
        item_disconnect.connect('activate', self.nordvpn.disconnect)
        menu.append(item_disconnect)

        # Create a submenu for the connection status
        menu_status = gtk.Menu()
        item_status = gtk.MenuItem('Status')
        item_status.set_submenu(menu_status)

        # First item is to refresh the status
        item_refresh = gtk.MenuItem('Refresh')
        item_refresh.connect('activate', self.nordvpn.status_check)
        menu_status.append(item_refresh)

        # Add a label to show the current status details
        self.status_label = gtk.MenuItem('')
        menu_status.append(self.status_label)
        self.status_label.set_sensitive(False)

        menu.append(item_status)

        # Define the Settings menu
        menu_settings = gtk.Menu()
        item_settings = gtk.MenuItem('Settings')
        item_settings.set_submenu(menu_settings)

        self.item_setting_tcp = gtk.CheckMenuItem(NordVPN.Settings.PROTOCOL.value)
        self.item_setting_tcp.connect('toggled', self.on_setting_update)
        menu_settings.append(self.item_setting_tcp)
        self.item_setting_kill = gtk.CheckMenuItem(NordVPN.Settings.KILL_SWITCH.value)
        self.item_setting_kill.connect('toggled', self.on_setting_update)
        menu_settings.append(self.item_setting_kill)
        self.item_setting_cybersec = gtk.CheckMenuItem(NordVPN.Settings.CYBER_SEC.value)
        self.item_setting_cybersec.connect('toggled', self.on_setting_update)
        menu_settings.append(self.item_setting_cybersec)
        self.item_setting_obfuscate = gtk.CheckMenuItem(NordVPN.Settings.OBFUSCATE.value)
        self.item_setting_obfuscate.connect('toggled', self.on_setting_update)
        menu_settings.append(self.item_setting_obfuscate)
        self.item_setting_autoconnect = gtk.CheckMenuItem(NordVPN.Settings.AUTO_CONNECT.value)
        self.item_setting_autoconnect.connect('toggled', self.on_setting_update)
        menu_settings.append(self.item_setting_autoconnect)
        self.item_setting_dns = gtk.CheckMenuItem(NordVPN.Settings.DNS.value)
        self.item_setting_dns.connect('toggled', self.on_setting_update)
        menu_settings.append(self.item_setting_dns)
        self.update_settings_menu()

        menu.append(item_settings)

        item_quit = gtk.MenuItem('Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def quit(self, _):
        """
        Cancels the timer, removes notifications, removes tray icon resulting
        in quitting the application
        """
        self.timer.cancel()
        notify.uninit()
        gtk.main_quit()

    def country_connect_cb(self, btn_toggled):
        """
        Callback function to handle the connection of a selected country
        """
        self.nordvpn.disconnect(None)
        self.nordvpn.connect_to_country(btn_toggled.get_label())

    def auto_connect_cb(self, _):
        """
        Callback to handle connection to auto server
        """
        self.nordvpn.disconnect(None)
        self.nordvpn.connect(None)

    def report(self, message):
        """
        Notifies indicator of connection issues and passes a notification
        message

        Args:
            message: Message that will be displayed as notification
        """
        notify.Notification.new("NordVPN", message, None).show()

    def on_setting_update(self, item):
        """
        Callback to handle toggle of Auto connect setting
        """
        setting = NordVPN.Settings(item.get_label())
        self.nordvpn.set_setting(setting, item.get_active())

    def update_settings_menu(self):
        """
        Update the setting menu with the current configuration set in the client app
        """
        settings = self.nordvpn.get_settings()
        self.item_setting_tcp.set_active(settings[NordVPN.Settings.PROTOCOL])
        self.item_setting_kill.set_active(settings[NordVPN.Settings.KILL_SWITCH])
        self.item_setting_cybersec.set_active(settings[NordVPN.Settings.CYBER_SEC])
        self.item_setting_obfuscate.set_active(settings[NordVPN.Settings.OBFUSCATE])
        self.item_setting_autoconnect.set_active(settings[NordVPN.Settings.AUTO_CONNECT])
        self.item_setting_dns.set_active(settings[NordVPN.Settings.DNS])


class NordVPN(object):
    """
    NordVPN

    Args:
        nordvpn: Nordvpn instance for connecting/disconnecting and
        checking the status of the connection

    Returns:
        Instance of Indicator class
    """
    def __init__(self):
        self.indicator = None
        self.connected = VPN_STATUS.WAITING
        self.status = ""

    def attach(self, indicator):
        """
        Attaches an indicator for notifying connection changes

        Args:
            indicator: Indicator instance
        """
        indicator.nordvpn = self
        self.indicator = indicator

    def run_command(self, command):
        """
        Runs bash commands and notifies on errors

        Args:
            command: Bash command to run

        Returns:
            Output of the bash command
        """
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        if error is not None:
            self.indicator.report(error)
        return output

    def connect(self, _):
        """
        Runs command to connect with a NordVPN server

        Args:
            _: As required by AppIndicator
        """
        self.connected = VPN_STATUS.WAITING
        output = self.run_command("nordvpn connect")

        # Check output
        if output is not None:
            matches = re.search('You are now connected to .*', output)
            if matches is not None:
                output = matches.group(0)
                self.connected = VPN_STATUS.CONNECTED

    def connect_to_country(self, country):
        """
        Runs command to connect to a NordVPN server in the specified country

        Args:
            country: Country name as string
        """
        self.connected = VPN_STATUS.WAITING
        output = self.run_command("nordvpn connect {}".format(country))

        # Check output
        if output is not None:
            matches = re.search('You are now connected to .*', output)
            if matches is not None:
                output = matches.group(0)
                self.connected = VPN_STATUS.CONNECTED

    def disconnect(self, _):
        """
        Runs command to disconnect with the currently connected NordVPN server

        Args:
            _: As required by AppIndicator
        """
        self.connected = VPN_STATUS.WAITING
        output = self.run_command("nordvpn disconnect")
        if output is not None:
            matches = re.search('You have been disconnected from NordVPN.', output)
            if matches is not None:
                self.connected = VPN_STATUS.DISCONNECTED

    def status_check(self, _):
        """
        Checks if an IP is outputted by the NordVPN status command

        Args:
            _: As required by AppIndicator
        """
        connected_ip = None

        # Get reported NordVPN IP
        output = self.run_command("nordvpn status")
        if output is not None:
            self.status = output.split('  ')[1].strip()
            matches = re.search(r'(([0-9])+\.){3}([0-9]+)', output)
            if matches is not None:
                connected_ip = matches.group(0)

        self.connected = VPN_STATUS.DISCONNECTED if connected_ip is None else VPN_STATUS.CONNECTED

    def get_status(self):
        """
        Returns the current status of the VPN connection as a string
        """
        return self.status

    def is_connected(self):
        """
        Returns VPN_STATUS instance representing the connection status
        """
        return self.connected

    def get_countries(self):
        """
        Returns a list of string representing the available countries
        """
        countries = self.run_command('nordvpn countries')
        if countries is None:
            return []
        country_list = ''.join(countries).split(' ')[2].split()
        country_list.sort()
        return country_list
        #return countries.split(' ')[2].split().sort()

    def get_settings(self):
        """
        Read the current settings from the client app and return them as dictionary

        Returns:
            - A dictionary {Setting:Value} where Setting is a instance of Settings Enum
        """
        settings = {}
        output = self.run_command('nordvpn settings')
        output = output.splitlines()[3:]
        for setting in output:
            key = setting.split(':')[0].strip()
            value = setting.split(':')[1].strip()
            settings[NordVPN.Settings(key)] = True if value == 'enabled' else False
        return settings

    def set_setting(self, setting, value):
        """
        Handle the update of nord vpn settings from the indicator app

        Args:
            - setting: the setting to update (instance of NordVPN.Settings)
            - value: the value reflecting the current menu selection
        """
        label = setting.value.replace(' ','').lower()
        if setting == NordVPN.Settings.PROTOCOL:
            status = 'TCP' if value else 'UDP'
        else:
            status = value

        print 'nordvpn set {} {}'.format(label, status)
        #self.run_command('nordvpn set {} {}'.format(label, value))

    class Settings(Enum):
        """
        Represents the settings available for the nordvpn client.
        Each value is the exact match of the setting name
        """
        PROTOCOL = "Protocol"
        KILL_SWITCH = "Kill Switch"
        CYBER_SEC = "CyberSec"
        OBFUSCATE = "Obfuscate"
        AUTO_CONNECT = "Auto connect"
        DNS = "DNS"


def main():
    """
    Entry of the program

    Signal for allowing Ctrl+C interrupts
    """
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    nordvpn = NordVPN()
    Indicator(nordvpn)

if __name__ == '__main__':
    main()
