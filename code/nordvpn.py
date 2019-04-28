# NordVPN interface class
# Provides an interface with the NordVPN Linux client application

import re
import subprocess
from enum import Enum


class ConnectionStatus(Enum):
    """
    Connection status to the VPN
    """
    CONNECTED = 0
    DISCONNECTED = 1
    WAITING = 2


class Settings(Enum):
    """
    Represents the settings available for the NordVPN client application.
    Each value is the exact match of the setting name
    """
    PROTOCOL = "Protocol"
    KILL_SWITCH = "Kill Switch"
    CYBER_SEC = "CyberSec"
    OBFUSCATE = "Obfuscate"
    AUTO_CONNECT = "Auto-connect"
    DNS = "DNS"
    NOTIFY = "Notify"


class NordVPNStatus():
    """
    Status of the NordVPN client app
    """

    def __init__(self):
        self.raw_status = 'Unknown'
        self.connection_status = ConnectionStatus.WAITING
        self.server = 'Unknown'
        self.country = 'Unknown'
        self.city = 'Unknown'
        self.IP = '0.0.0.0'
        self.protocol = 'Unknown'
        self.transfer = 'Unknown'
        self.uptime = 'Unknown'

    def update(self, raw_status):
        self.raw_status = raw_status
        # TODO parse the string and assign internal members
        matches = re.search(r'(([0-9])+\.){3}([0-9]+)', raw_status)
        if matches is not None:
            self.IP = matches.group(0)
            self.connection_status = ConnectionStatus.DISCONNECTED if self.IP is None else ConnectionStatus.CONNECTED
        self.server = 'Unknown'
        self.country = 'Unknown'
        self.city = 'Unknown'
        self.protocol = 'Unknown'
        self.transfer = 'Unknown'
        self.uptime = 'Unknown'


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
        self.status = NordVPNStatus()

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
        output = self.run_command("nordvpn connect")

    def connect_to_country(self, country):
        """
        Runs command to connect to a NordVPN server in the specified country

        Args:
            country: Country name as string
        """
        output = self.run_command("nordvpn connect {}".format(country))

    def disconnect(self, _):
        """
        Runs command to disconnect with the currently connected NordVPN server

        Args:
            _: As required by AppIndicator
        """
        output = self.run_command("nordvpn disconnect")

    def status_check(self, _):
        """
        Checks if an IP is outputted by the NordVPN status command

        Args:
            _: As required by AppIndicator
        """
        output = self.run_command("nordvpn status")
        if output is not None:
            raw = output.split('  ')[1].strip()
            self.status.update(raw)

    def get_status(self):
        """
        Returns the current status of the VPN connection as a string
        """
        return self.status

    def get_countries(self):
        """
        Returns a list of string representing the available countries
        """
        countries = self.run_command('nordvpn countries')
        if countries is None:
            return []
        # country_list = ''.join(countries).split(' ')[2].split()
        country_list = [c.replace(',', '')
                        for c in ''.join(countries).split()[1:]]
        country_list.sort()
        return country_list

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

            if key == Settings.PROTOCOL.value:
                value = 'enabled' if value == 'TCP' else 'disabled'

            settings[Settings(
                key)] = True if value == 'enabled' else False
        return settings

    def set_settings(self, settings):
        """
        Handle the update of nord vpn settings from the indicator app

        Args:
            - settings: a dict {Settings : value} representing settings to set.
                        Settings will be updated only if their related key is in the dict
        """
        for key, value in settings.items():
            setting = value
            if key == Settings.AUTO_CONNECT:
                if value == 'Off':
                    setting = False
                elif value == 'Automatic':
                    setting = True
                else:
                    setting = 'on {}'.format(value.lower())
            self.run_command('nordvpn set {} {}'.format(
                key.value.replace(' ', '').lower(), str(setting).lower()))
