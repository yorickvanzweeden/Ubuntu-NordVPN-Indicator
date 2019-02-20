# Ubuntu NordVPN Indicator
This repository allows for the installation of a Python script that adds an application indicator for NordVPN. NordVPN does not seem to provide such a program and only offers terminal access or an OpenVPN configuration. The indicator is placed with the other GNOME App Indicators and allows for connecting and disconnecting to NordVPN. A screenshot is shown below:
![alt text](https://raw.githubusercontent.com/yorickvanzweeden/Ubuntu-NordVPN-Indicator/master/screenshot.png "Screenshot")


## Installation
Run the installation script ```install.sh```
> ./install.sh

If the package ```nordvpn``` is not found, it will be installed. The python script is added as a startup application. During the installation process, NordVPN will ask for credentials. The status of the VPN is checked every 10 seconds. If no VPN connection is detected, the logo turns blue. When a VPN connection is established, the logo will become green.

![alt text](https://raw.githubusercontent.com/yorickvanzweeden/Ubuntu-NordVPN-Indicator/master/code/nordvpn_disconnected.png "Disconnected logo")  ![alt text](https://raw.githubusercontent.com/yorickvanzweeden/Ubuntu-NordVPN-Indicator/master/code/nordvpn_connected.png "Connected logo")

## Uninstallation
Run the uninstallation script ```uninstall.sh``` to remove this program. An option will be offered to remove the package ```nordvpn``` as well.
> ./uninstall.sh

## Todo
- Add option to connect to a server at startup
- Add option to pick which country to connect to
- Add option to pick a specific server
- Add option to change status polling frequency
