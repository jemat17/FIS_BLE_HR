BLEHeartRateLogger.py
=====================

pip3 install pexpect configparser dash dash_core_components dash_html_components plotly webbrowser pandas matplotlib.pyplot easygui numpy




BLEHeartRateLogger.py is a Bluetooth Low-Energy (BLE) Heart Rate Monitor (HRM) data logger written in Python for Linux. With this tool you can log your heart rate and heart rate variability (RR) during exercise, sleep or whatever comes to mind.

Communication with the BLE HRM is established using `hcitool` and `gatttool`. The output of those tools is then parsed and saved to an sqlite database.



## Installation

###User instructions on Debian/Ubuntu:

For using this program you first have to install:
#$ sudo apt-get install bluetooth bluez 
bluez contains hcitool and gatttools.
#$ pip3 install pip3 install pexpect dash dash_core_components dash_html_components plotly pandas matplotlib.pyplot easygui numpy
These python libraries are necessary for running the program. 

Setting up hcitools:
It is necessary to be able to run hcitool lescan without sudo. This is done by:
Installs linux capabilities manipulation tools:
```
#$ sudo apt-get install libcap2-bin
```
Sets the missing capabilities on the executable quite like the setuid bit:
```
#$ sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
```
Next check that all is good: 
```
#$ getcap `which hcitool`
```
Should say:

> /usr/bin/hcitool = cap_net_admin,cap_net_raw+eip

Next you will need to program:

You can download the program from github by writing the following in a terminal:
```
#git clone https://github.com/jemat17/FIS_BLE_HR.git 
```
When you have install the software you can now take your heart rate sensor device on

To run the program open a terminal and run the following command:
```
#cd /FIS_BLE_HR/BLEHR

#./start.sh
```
After writing the program in the terminal, a box will appear where you have to click.

Connect 

When you click connect all bluetooth devices near you will appear, you should now find your heart rate device and then.
“click on your heart rate device” 
Then click OK

You are now back in the gui, now you can click on what measure do wanna see you can now click on Live HR, Live HRV, HR, and HRV.

If you clicked on Live HR or HRV you will now see a live graph of HR or HRV.

If you clicked on HR or HRV you now have to click on which date you want to see data from.

Then you have to click OK.

You can now see a graph of your Heart Rate or Heart Rate Variability from the date you have chosen. 

To exit the program: 

hold ctrl and press c in the terminal running the ./start.sh

Run the script as root user or correctly specify the rights on `hcitool` and `gatttool` (see Troubleshooting) .



## Usage

To start the tool (as root or with correct rights):

Make sure hcitool can run without root. 
```
# ./start.sh
2015-01-10 13:40:59,326  Trying to find a BLE device
2015-01-10 13:41:00,856  Establishing connection to 00:11:22:33:44:55
2015-01-10 13:41:01,115  Connected to 00:11:22:33:44:55
2015-01-10 13:41:03,412  Heart rate: 65
2015-01-10 13:41:04,357  Heart rate: 65
```

To quit the tool, simply Ctrl-C.


Command line options:
```
usage: BLEHeartRateLogger.py [-h] [-m MAC] [-b] [-g PATH] [-o FILE] [-v]

Bluetooth heart rate monitor data logger

optional arguments:
  -h, --help  show this help message and exit
  -m MAC      MAC address of BLE device (default: auto-discovery)
  -b          Check battery level
  -g PATH     gatttool path (default: system available)
  -o FILE     Output filename of the database (default: none)
  -v          Verbose output
```



## Troubleshooting

In case the tool is not able to connect to your BLE HRM, first check manually that your computer and BLE HRM device are able to talk to eachother using the following steps (as root).
```
# hcitool lescan
```
This should list the BLE devices around you with their MAC address with something which looks like this: 00:11:22:33:44:55. You can safely Ctrl-C when the device has been found. We will the connect to the device:
```
# gatttool -b 00:11:22:33:44:55 -I
```
This should open a prompt. Type the following commands:
```
> connect
> characteristics
> exit
```

In case one of the steps mentionned above fails, check your Linux installation and eventually `bluez` version (>= v.5 recommended).

## HCItool without sudo:

Installs linux capabilities manipulation tools:
#sudo apt-get install libcap2-bin

Sets the missing capabilities on the executable quite like the setuid bit:
#sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`

Next check that all is good: 
#getcap !$

Should say:
> getcap `which hcitool`
> /usr/bin/hcitool = cap_net_admin,cap_net_raw+eip
 
#If connection lost: 
sudo service bluetooth restart 

## Contributing

Contributions are welcome.

1. [Fork the repository](https://github.com/jemat17/FIS_BLE_HR)
2. Create your feature branch (`git checkout -b my-feature`)
3. Commit your changes (`git commit -am 'Commit message'`)
4. Push to the branch (`git push origin my-feature`)
5. Create a pull request

