#!/bin/bash

install_client()
{
    # Get NordVPN Repo Setup (https://nordvpn.com/download/linux/)
    echo "Getting the NordVPN Repo Setup"
    wget https://repo.nordvpn.com/deb/nordvpn/debian/pool/main/nordvpn-release_1.0.0_all.deb

    # Install downloaded package
    echo "Installing the NordVPN Repo Setup"
    sudo apt-get install -y nordvpn-release_1.0.0_all.deb
    rm nordvpn-release_1.0.0_all.deb

    # Update packages
    echo "Updating packages"
    sudo apt-get update

    # Install NordVPN
    echo "Installing NordVPN"
    sudo apt-get install -y nordvpn

    # Prompting user to login
    echo "Logging into NordVPN"
    nordvpn login
}

install_deps()
{
    # Install gir1.2-appindicator
    echo "Installing AppIndicator and Python-GI"
    sudo apt-get install -y gir1.2-appindicator python-gi
}

install_indicator()
{
    # Installing indicator in opt directory
    echo "Installing Ubuntu NordVPN Indicator"
    sudo mkdir -p /opt/ubuntu-nordvpn-indicator/
    sudo cp code/* /opt/ubuntu-nordvpn-indicator/

    # Installing autostart desktop file
    echo "Making sure the indicator starts at boot using autostart"
    mkdir -p $HOME/.config/autostart
    cp ubuntu-nordvpn-indicator.desktop $HOME/.config/autostart/
}

# Install client if not present
if ! command -v nordvpn > /dev/null 2>&1;
then
    install_client
fi

# Install dependencies if not present
deps_available=$(dpkg -l | grep -E "gir1.2-appindicator-|python-gi"  | wc --lines)
if [[ $deps_available -eq 2 ]]
then
    echo "Dependencies have been installed"
else
    install_deps
fi

# Install indicator
install_indicator

# Starting script
if pgrep -f "nordvpn_indicator" > /dev/null
then
    echo "Indicator already running"
else
    echo "Starting indicator"
    nohup $(command -v python) /opt/ubuntu-nordvpn-indicator/nordvpn_indicator.py >/dev/null 2>&1 &
fi

echo "Finished"
