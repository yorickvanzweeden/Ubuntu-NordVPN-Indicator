#!/bin/sh

install_client()
{
    # Get NordVPN Repo Setup (https://nordvpn.com/download/linux/)
    echo Getting the NordVPN Repo Setup
    wget https://repo.nordvpn.com/deb/nordvpn/debian/pool/main/nordvpn-release_1.0.0_all.deb

    # Install downloaded package
    echo Installing the NordVPN Repo Setup
    sudo apt-get install -y nordvpn-release_1.0.0_all.deb
    rm nordvpn-release_1.0.0_all.deb

    # Update packages
    echo Updating packages
    sudo apt-get update

    # Install NordVPN
    echo Installing NordVPN
    sudo apt-get install -y nordvpn

    # Prompting user to login
    echo Logging into NordVPN
    nordvpn login
}

install_deps()
{
    # Install gir1.2-appindicator
    echo Installing AppIndicator
    sudo apt-get install -y gir1.2-appindicator python-gi
}

install_indicator()
{
    # Installing indicator in opt directory
    echo Installing Ubuntu NordVPN Indicator
    sudo mkdir -p /opt/ubuntu-nordvpn-indicator/
    sudo cp code/nordvpn_* /opt/ubuntu-nordvpn-indicator/

    # Installing autostart desktop file
    echo Making sure the indicator starts at boot using autostart
    mkdir -p $HOME/.config/autostart
    cp ubuntu-nordvpn-indicator.desktop $HOME/.config/autostart/
}

if ! command -v nordvpn > /dev/null 2>&1;
then
    install_client
fi

install_deps
install_indicator

# Starting script
echo Starting indicator
nohup $(command -v python) /opt/ubuntu-nordvpn-indicator/nordvpn_indicator.py >/dev/null 2>&1 &

echo Finished
