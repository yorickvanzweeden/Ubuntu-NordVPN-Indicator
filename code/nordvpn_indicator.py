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


APPINDICATOR_ID = 'nordvpn_tray_icon'
TIMER_SECONDS = 10.0


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

        # Set recurrent timer for checking VPN status
        self.status_check_loop()

        # Add indicator
        self.indicator = appindicator.Indicator.new(
            APPINDICATOR_ID,
            self.get_icon_path(False),
            appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        notify.init(APPINDICATOR_ID)
        self.nordvpn.connect(self)
        gtk.main()

    def status_check_loop(self):
        """
        Sets timer in recurrent loop that executes a VPN status check
        """
        self.timer = threading.Timer(TIMER_SECONDS, self.status_check_loop)
        self.timer.start()
        if hasattr(self, 'indicator'):
            self.nordvpn.status_check(None)

    def update(self, message, connected):
        """
        Updates the icon and displays a notification if a message is provided

        Args:
            message: Message for the notification
            connected: Connected status (True/False)
        """
        if message != None:
            notify.Notification.new("NordVPN", message, None).show()
        self.indicator.set_icon(self.get_icon_path(connected))

    @staticmethod
    def get_icon_path(connected):
        """
        Returns the correct icon in response to the connection status

        Args:
            connected: Connected status (True/False)
        """
        filename = 'nordvpn_connected.png' if connected else 'nordvpn_disconnected.png'
        return os.path.dirname(os.path.realpath(__file__)) + '/' + filename

    def build_menu(self):
        """
        Builds menu for the tray icon
        """
        menu = gtk.Menu()

        item_connect = gtk.MenuItem('Connect')
        item_connect.connect('activate', self.nordvpn.connect)
        menu.append(item_connect)

        item_disconnect = gtk.MenuItem('Disconnect')
        item_disconnect.connect('activate', self.nordvpn.disconnect)
        menu.append(item_disconnect)

        item_status_check = gtk.MenuItem('Status check')
        item_status_check.connect('activate', self.nordvpn.status_check)
        menu.append(item_status_check)

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
        self.connected = False

    def attach(self, indicator):
        """
        Attaches an indicator for notifying connection changes

        Args:
            indicator: Indicator instance
        """
        indicator.nordvpn = self
        self.indicator = indicator

    def _notify(self, message):
        """
        Notifies indicator of connection status and passes a notification
        message

        Args:
            message: Message that will be displayed as notification
        """
        self.indicator.update(message, self.connected)

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
        if error != None:
            self._notify(error)

        return output

    def connect(self, _):
        """
        Runs command to connect with a NordVPN server

        Args:
            _: As required by AppIndicator
        """
        output = self.run_command("nordvpn connect")

        # Check output
        if output != None:
            matches = re.search('You are now connected to .*', output)
            if matches != None:
                output = matches.group(0)
                self.connected = True
            self._notify(output)

    def disconnect(self, _):
        """
        Runs command to disconnect with the currently connected NordVPN server

        Args:
            _: As required by AppIndicator
        """
        output = self.run_command("nordvpn disconnect")
        if output != None:
            matches = re.search('You have been disconnected from NordVPN.', output)
            if matches != None:
                self.connected = False
            self._notify(output)

    def status_check(self, _):
        """
        Checks if an IP is outputted by the NordVPN status command

        Args:
            _: As required by AppIndicator
        """
        connected_ip = None

        # Get reported NordVPN IP
        output = self.run_command("nordvpn status")
        if output != None:

            matches = re.search(r'(([0-9])+\.){3}([0-9]+)', output)
            if matches != None:
                connected_ip = matches.group(0)

        if connected_ip is None and self.connected is True:
            self.connected = False
            self.indicator.update(None, self.connected)

        if connected_ip != None and self.connected is False:
            self.connected = True
            self.indicator.update(None, self.connected)


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
