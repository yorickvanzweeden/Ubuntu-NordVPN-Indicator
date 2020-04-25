#!/usr/bin/python
"""
Adds icon to notification tray that allows for connecting
and disconnecting to NordVPN
"""

import os
import signal
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator

from nordvpn import NordVPN, ConnectionStatus, NordVPNStatus


APPINDICATOR_ID = 'nordvpn_tray_icon'
TIMER_SECONDS = 5.0

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
        self.nordvpn = nordvpn

        # Add indicator
        self.indicator = appindicator.Indicator.new(
            APPINDICATOR_ID,
            self.get_icon_path(ConnectionStatus.WAITING),
            appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

        # Set recurrent timer for checking VPN status
        self.status_check_loop()
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
        status = self.nordvpn.get_status()
        self.status_label.set_label(status.get_label_status())
        self.indicator.set_icon_full(self.get_icon_path(status.data[NordVPNStatus.Param.STATUS]),'')

    @staticmethod
    def get_icon_path(connected):
        """
        Returns the correct icon in response to the connection status

        Args:
            connected: Connected status ConnectionStatus object
        """
        if connected == ConnectionStatus.CONNECTED:
            filename = 'nordvpn_connected.png'
        elif connected == ConnectionStatus.DISCONNECTED:
            filename = 'nordvpn_disconnected.png'
        else:
            filename = 'nordvpn_waiting.png'
        return os.path.dirname(os.path.realpath(__file__)) + '/' + filename

    def build_menu(self):
        """
        Builds menu for the tray icon
        """
        main_menu = gtk.Menu()

        # Create a Connect submenu
        menu_connect = gtk.Menu()
        item_connect = gtk.MenuItem(label='Connect')
        item_connect.set_submenu(menu_connect)
        main_menu.append(item_connect)

        # First item is to connect automatically
        item_connect_auto = gtk.MenuItem(label='Auto')
        item_connect_auto.connect('activate', self.auto_connect_cb)
        menu_connect.append(item_connect_auto)

        # Second item is submenu to select the country
        countries = self.nordvpn.get_countries()
        countries_menu = gtk.Menu()
        item_connect_country = gtk.MenuItem(label='Countries')
        item_connect_country.set_submenu(countries_menu)
        for country in countries:
            item = gtk.MenuItem(label=country)
            item.connect('activate', self.country_connect_cb)
            countries_menu.append(item)
        menu_connect.append(item_connect_country)

        # Next item is submenu to select a specific city
        cities_menu = gtk.Menu()
        item_connect_city = gtk.MenuItem(label='Cities')
        item_connect_city.set_submenu(cities_menu)
        for country in countries:
            # Draw the country as disabled
            item_country = gtk.MenuItem(label=country)
            item_country.set_sensitive(False)
            cities_menu.append(item_country)
            # List the cities below
            cities = self.nordvpn.get_cities(country)
            for city in cities:
                item_city = gtk.MenuItem(label=city)
                item_city.connect('activate', self.city_connect_cb)
                cities_menu.append(item_city)
        menu_connect.append(item_connect_city)

        # Next item is submenu to select a server group
        groups = self.nordvpn.get_groups()
        groups_menu = gtk.Menu()
        item_connect_group = gtk.MenuItem(label='Groups')
        item_connect_group.set_submenu(groups_menu)
        for g in groups:
            item = gtk.MenuItem(label=g)
            item.connect('activate', self.group_connect_cb)
            groups_menu.append(item)
        menu_connect.append(item_connect_group)

        # Disconnect item
        item_disconnect = gtk.MenuItem(label='Disconnect')
        item_disconnect.connect('activate', self.nordvpn.disconnect)
        main_menu.append(item_disconnect)

        # Create a submenu for the connection status
        menu_status = gtk.Menu()
        item_status = gtk.MenuItem(label='Status')
        item_status.set_submenu(menu_status)
        main_menu.append(item_status)

        # Add a label to show the current status details
        self.status_label = gtk.MenuItem(label='')
        menu_status.append(self.status_label)
        self.status_label.set_sensitive(False)

        # Define the Settings menu entry
        item_settings = gtk.MenuItem(label='Settings...')
        item_settings.connect('activate', self.display_settings_window)
        main_menu.append(item_settings)

        item_quit = gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self.quit)
        main_menu.append(item_quit)

        main_menu.show_all()
        return main_menu

    def quit(self, _):
        """
        Cancels the timer, removes notifications, removes tray icon resulting
        in quitting the application
        """
        self.timer.cancel()
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

    def display_settings_window(self, widget):
        """
        Display a new window showing the settings of the NordVPN client app
        """
        window = SettingsWindow(self.nordvpn)
        window.show_all()

    def group_connect_cb(self, menu_item):
        """
        Callback to connect to a server group
        """
        self.nordvpn.disconnect(None)
        self.nordvpn.connect_to_group(menu_item.get_label())

    def city_connect_cb(self, menu_item):
        """
        Callback to connet to a city server
        """
        self.nordvpn.disconnect(None)
        self.nordvpn.connect_to_city(menu_item.get_label())

class SettingsWindow(gtk.Window):
    """
    GTK window widget to display NordVPN settings

    Args:
        - settings: dict {Settings:value} representing the configuration to display
        - callback: function accepting 1 argument as the "settings" dict above. Callback
                    is called to save the settings
    """
    def __init__(self, nordvpn):
        super(SettingsWindow, self).__init__()
        self.nordvpn = nordvpn
        self.selected_setting = None
        # GTK Window configuration
        self.set_default_size(200,200)
        self.set_title('NordVPN settings')
        self.set_border_width(8)
        #self.set_position(WIN_POS_CENTER)
        self.set_default_icon_from_file(os.path.dirname(os.path.realpath(__file__)) + '/nordvpn_disconnected.png')
        self.set_focus()
        # Build window layout
        self.add(self.create_widgets())

    def create_widgets(self):
        # TODO start a timer that keep updating the settings
        settings = self.nordvpn.get_settings()
        # Store the setting widget to update its value
        self.settings_labels = dict()

        m_vbox = gtk.VBox(False, 20)

        # Main parent sections that holds the current settings
        row_current = gtk.Box(gtk.Orientation.HORIZONTAL, 4)
        vbox_settings = gtk.VBox(False, 5)
        vbox_settings.add(gtk.Label('Current NordVPN settings'))
        vbox_settings.add(gtk.Label('(Hover on each setting row for a tooltip)'))
        for key, value in settings.items():
            # Create a row to display the current setting
            row_setting = gtk.Box(gtk.Orientation.HORIZONTAL, 4)
            widget = gtk.Label('{}: {}'.format(key, value))
            row_setting.add(widget)
            # Store the widget in the dict to update its value later
            self.settings_labels[key] = widget
            # Set the help message as widget tooltip
            row_setting.set_tooltip_text(self.nordvpn.get_help_message(key))
            vbox_settings.add(row_setting)
        # Add vertical box to the first window row
        row_current.pack_start(vbox_settings, True, True, 0)

        # Section containing widgets to change current settings
        row_set = gtk.Box(gtk.Orientation.HORIZONTAL, 4)
        row_set.add(gtk.Label('nordvpn set '))
        # Combo box to select setting to update
        combo_set = gtk.ComboBoxText()
        for key, value in settings.items():
            combo_set.append(key, key)
        combo_set.connect('changed', self.on_setting_selection)
        combo_set.set_active_id(settings.items()[0][0])
        row_set.add(combo_set)
        # Entry to insert setting command
        self.entry_set = gtk.Entry()
        row_set.add(self.entry_set)
        # Apply button to set the entered command
        button_apply = gtk.Button('Apply')
        button_apply.connect('clicked', self.on_apply)
        row_set.add(button_apply)

        # Display command output in this section
        row_output = gtk.Box(gtk.Orientation.HORIZONTAL, 4)
        vbox_output = gtk.VBox(False, 5)
        vbox_output.pack_start(gtk.Label('Output: '), True, False, 0)
        self.cmd_output = gtk.Label('')
        vbox_output.pack_start(self.cmd_output, True, False, 0)
        row_output.pack_start(vbox_output, True, False, 0)

        row_buttons = gtk.Box(gtk.Orientation.HORIZONTAL, 4, halign=gtk.Align.END)
        button_close = gtk.Button('Close')
        button_close.connect('clicked', self.on_close)
        row_buttons.add(button_close)

        m_vbox.pack_start(row_current, True, True, 0)
        m_vbox.pack_start(gtk.HSeparator(), True, False, 0)
        m_vbox.pack_start(row_set, True, False, 0)
        m_vbox.pack_start(row_output, True, False, 0)
        m_vbox.pack_start(row_buttons, True, False, 0)
        return m_vbox

    def on_close(self, widget):
        self.destroy()

    def on_setting_selection(self, widget):
        self.selected_setting = widget.get_active_text()

    def on_apply(self, widget):
        output = self.nordvpn.set_setting(self.selected_setting, self.entry_set.get_text())
        # Show output in window
        self.cmd_output.set_text(output)
        # Clear the Entry widget
        self.entry_set.set_text('')
        # Update the current settings labels
        for key, value in self.nordvpn.get_settings().items():
            self.settings_labels[key].set_text('{}: {}'.format(key, value))

def main():
    """
    Entry of the program

    Signal for allowing Ctrl+C interrupts
    """
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Indicator(NordVPN())

if __name__ == '__main__':
    main()
