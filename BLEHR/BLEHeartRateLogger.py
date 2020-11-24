#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
	BLEHeartRateLogger
	~~~~~~~~~~~~~~~~~~~

	A tool to log your heart rate using a Bluetooth low-energy (BLE) heart rate
	monitor (HRM). The tool uses system commands (hcitool and gatttool) to
	connect to the BLE HRM and parses the output of the tools. Data is
	interpreted according to the Bluetooth specification for HRM and saved in a
	sqlite database for future processing. In case the connection with the BLE
	HRM is lost, connection is restablished.

	:copyright: (c) 2015 by fg1
	:license: BSD, see LICENSE for more details
"""

__version__ = "0.1.1"

import os
import sys
import time
import logging
import sqlite3
import pexpect
import argparse
import configparser
import csv
import pandas as pd	
import easygui as eg
import pyautogui
from matplotlib import pyplot as plt
import re

data=["time"]


logging.basicConfig(format="%(asctime)-15s  %(message)s")
log = logging.getLogger("BLEHeartRateLogger")


def parse_args():
	"""
	Command line argument parsing
	"""
	parser = argparse.ArgumentParser(description="Bluetooth heart rate monitor data logger")
	parser.add_argument("-m", metavar='MAC', type=str, help="MAC address of BLE device (default: auto-discovery)")
	parser.add_argument("-b", action='store_true', help="Check battery level")
	parser.add_argument("-g", metavar='PATH', type=str, help="gatttool path (default: system available)", default="gatttool")
	parser.add_argument("-o", metavar='FILE', type=str, help="Output filename of the database (default: none)")
	parser.add_argument("-H", metavar='HR_HANDLE', type=str, help="Gatttool handle used for HR notifications (default: none)")
	parser.add_argument("-v", action='store_true', help="Verbose output")
	parser.add_argument("-d", action='store_true', help="Enable debug of gatttool")

	confpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "BLEHeartRateLogger.conf")
	if os.path.exists(confpath):

		config = configparser.ConfigParser()
		config.read([confpath])
		config = dict(config.items("config"))

		# We compare here the configuration given in the config file with the
		# configuration of the parser.
		args = vars(parser.parse_args([]))
		err = False
		for key in config.iterkeys():
			if key not in args:
				log.error("Configuration file error: invalid key '" + key + "'.")
				err = True
		if err:
			sys.exit(1)

		parser.set_defaults(**config)

	return parser.parse_args()


def interpret(data):
	"""
	data is a list of integers corresponding to readings from the BLE HR monitor
	"""

	byte0 = data[0]
	res = {}
	res["hrv_uint8"] = (byte0 & 1) == 0
	sensor_contact = (byte0 >> 1) & 3
	if sensor_contact == 2:
		res["sensor_contact"] = "No contact detected"
	elif sensor_contact == 3:
		res["sensor_contact"] = "Contact detected"
	else:
		res["sensor_contact"] = "Sensor contact not supported"
	res["ee_status"] = ((byte0 >> 3) & 1) == 1
	res["rr_interval"] = ((byte0 >> 4) & 1) == 1

	if res["hrv_uint8"]:
		res["hr"] = data[1]
		i = 2
	else:
		res["hr"] = (data[2] << 8) | data[1]
		i = 3

	if res["ee_status"]:
		res["ee"] = (data[i + 1] << 8) | data[i]
		i += 2

	if res["rr_interval"]:
		res["rr"] = []
		while i < len(data):
			# Note: Need to divide the value by 1024 to get in seconds
			res["rr"].append((data[i + 1] << 8) | data[i])
			i += 2

	return res


def insert_db(sq, res, period, min_ce=2, max_ce=60 * 2, grace_commit=2 / 3.):
	"""
	Inserts data into the database
	"""

	if not hasattr(insert_db, "i"):
		insert_db.i = 0
	if not hasattr(insert_db, "commit_every"):
		insert_db.commit_every = 5

	tstamp = int(time.time())
	if "rr" in res:
		for rr in res["rr"]:
			sq.execute("INSERT INTO hrm VALUES (?, ?, ?)", (tstamp, res["hr"], rr))
	else:
		sq.execute("INSERT INTO hrm VALUES (?, ?, ?)", (tstamp, res["hr"], -1)) #res["hr"] der er vores heart rate data 

	# Instead of pushing the data to the disk each time, we commit only every
	# 'commit_every'.
	if insert_db.i < insert_db.commit_every:
		insert_db.i += 1
	else:
		t = time.time()
		sq.commit()
		delta_t = time.time() - t
		log.debug("sqlite commit time: " + str(delta_t))
		sq.execute("INSERT INTO sql VALUES (?, ?, ?)", (int(t), delta_t, insert_db.commit_every))

		# Because the time for commiting to the disk is not known in advance,
		# we measure it and automatically adjust automatically 'commit_every'
		# following a rule similar to TCP Reno.
		if delta_t < period * grace_commit:
			insert_db.commit_every = min(insert_db.commit_every + 1, max_ce)
		else:
			insert_db.commit_every = max(insert_db.commit_every / 2, min_ce)

		insert_db.i = 0


def get_ble_hr_mac():
	"""
	Scans BLE devices and returs the address of the first device found.
	"""

	while 1:
		log.info("Trying to find a BLE device")
		dictOfBLE = {"Name": "macAddr"}
		regex = re.compile(r'(([0-9A-F]{2}[:-]){5}([0-9A-F]{2})) ([a-zA-Z0-9]+\s[a-zA-z0-9]+)')
		hci = pexpect.spawn("hcitool lescan", encoding='utf-8')
		hci.logfile = open("mylog.txt", "w")
		time.sleep(2)
		try:
			with open("mylog.txt", "r") as mylogs:
				lines = []
				for line in mylogs:
					if "(unknown)" not in line:
						split_list=line.split()
						for item in split_list:
							lines.append(item)
				print(lines)
												
									
			#with open('mylog.log', 'r') as mylog:
			#	print([x.group() for x in regex.finditer(mylog)])
			hci.expect("(([0-9A-F]{2}[:-]){5}([0-9A-F]{2})) ([a-zA-Z0-9]+\s[a-zA-z0-9]+)", timeout=20) 
			addr = hci.match.group(1).decode()
			name = hci.match.group(4).decode()

			with open("mylog.txt", "r") as mylog:
				for line in mylog:
					#if "(unknown)" in line:
					log.info("HEJ MED DIG")
						#dictOfBLE[name] = addr
					# 	print(" NAME " , name)
					# 	print(" ADDR " , addr)
						

				hci.close()
			break

		except pexpect.TIMEOUT:
			time.sleep(20)
			continue

		except KeyboardInterrupt:
			log.info("Received keyboard interrupt. Quitting cleanly.")
			hci.close()
			return None

	# We wait for the 'hcitool lescan' to finish
	time.sleep(1)
	return addr

data=[["time","y"]]
t0=time.time()	

def heart_data(res, first):
	filename="data"	
	if first is False: 
		first = True
		fieldnames = ["time", "HR"]
		with open(filename + '.csv', 'w') as csv_file:
			csv_writer = csv.DictWriter(csv_file, fieldnames = fieldnames)
			csv_writer.writeheader

	while True:

		with open('data.csv', 'a') as csv_file:
			csv_writer = csv.DictWriter(csv_file, fieldnames)

			data = {
				"time": time.time()-t0,
				"HR": res["hr"]
			}
			csv_writer.writerow(data)

	
	tQ=0.5				## Sampling tiime in seconds
	
		## We use this time also in the filename, so that our program saves a unique filename
	data_heart = str(res["hr"])
		
	
	# 			## By adding this time.sleep for .01 s we make so that our sampling will be approx 1/.01=100 Hz	
	# data.append([time.time()-t0,data_heart])	## data is a list containing our trajectory. We add a list of three elements at each cycle
	# #time.sleep(tQ)
	# ## Saving our data in the .csv file
	# with open(filename+".csv","w") as my_file:
	# 	my_file = open(filename+".csv","w") 
	# 	my_writer=csv.writer(my_file)
	# 	for each_row in data:
	# 		my_writer.writerow(each_row)
	# Måske tjekke rækker i data vs rækker i csv

def plotData():
	data = pd.read_csv('data.csv')
	x = data["time"]
	y1 = data["HR"]

	plt.cla()

	plt.plot(x, y1, label = 'HR')

	plt.legend(loc = 'upper left')
	plt.tight_layout()





def gui():
  
	device=[["addr","name"]]
	# message to be displayed  
	text = "Welcome to the Heart Rate monitoring program"
  
	# window title 
	title = "HR monitor"
  
	# button list 
	button_list = [] 
  
	# button 1 
	button1 = "Connect"
  
	# second button 
	button2 = "Show HR grapf"
  
	# third button 
	button3 = "Show HRV grapf"
  
	# appending button to the button list 
	button_list.append(button1) 
	button_list.append(button2) 
	button_list.append(button3) 
  
  
	# creating a button box 
	output = eg.buttonbox(text, title, button_list) 
  
	# printing the button pressed by the user 
	print("User selected option : ", end = " ") 
	print(output) 


	device.append([2,5]) # har skal indsættes navn og adresse fra forskellige devices

	if output == "Connect":
		msg ="Which devices would you like to connect to?"
		title = "Connect"
		choices = [device[0],device[1]]
		choice = eg.choicebox(msg, title, choices)
	
	if output == "Show HR grapf":
		print("hey")
		#få vist graf med HR
	
	if output == "Show HRV grapf":
		print("hey")
		#få vist graf med HRV
		
	#device.append([,]) # har skal indsættes data fra forskellige devices

	if output == "Connect":
		msg ="Which devices would you like to connect to?"
		title = "Connect"
		choices = [device[0],device[1]]
		choice = choicebox(msg, title, choices)


def main(addr=None, sqlfile=None, gatttool="gatttool", check_battery=False, hr_handle=None, debug_gatttool=False):
	"""
	main routine to which orchestrates everything
	"""
	first = False

	if sqlfile is not None:
		# Init database connection
		sq = sqlite3.connect(sqlfile)
		with sq:
			sq.execute("CREATE TABLE IF NOT EXISTS hrm (tstamp INTEGER, hr INTEGER, rr INTEGER)")
			sq.execute("CREATE TABLE IF NOT EXISTS sql (tstamp INTEGER, commit_time REAL, commit_every INTEGER)")

	if addr is None:
		# In case no address has been provided, we scan to find any BLE devices
		addr = get_ble_hr_mac()
		if addr == None:
			sq.close()
			return

	hr_ctl_handle = None
	retry = True
	while retry:

		while 1:
			log.info("Establishing connection to " + addr)
			gt = pexpect.spawn(gatttool + " -b " + addr + " -t random --interactive")
			if debug_gatttool:
				gt.logfile = sys.stdout

			gt.expect(r"\[LE\]>")
			gt.sendline("connect")

			try:
				i = gt.expect(["Connection successful.", r"\[CON\]"], timeout=30) # Tid i secunder
				if i == 0:
					gt.expect(r"\[LE\]>", timeout=30)

			except pexpect.TIMEOUT:
				log.info("Connection timeout. Retrying.")
				continue

			except KeyboardInterrupt:
				log.info("Received keyboard interrupt. Quitting cleanly.")
				retry = False
				break
			break

		if not retry:
			break

		log.info("Connected to " + addr)

		if check_battery:
			gt.sendline("char-read-uuid 00002a19-0000-1000-8000-00805f9b34fb") # Returnere batteri niveau!
			try:
				gt.expect("value: ([0-9a-f]+)")
				battery_level = gt.match.group(1)
				log.info("Battery level: " + str(int(battery_level, 16)))

			except pexpect.TIMEOUT:
				log.error("Couldn't read battery level.")

		if hr_handle == None:
			# We determine which handle we should read for getting the heart rate
			# measurement characteristic.
			gt.sendline("char-desc")

			while 1:
				try:
					gt.expect(r"handle: (0x[0-9a-f]+), uuid: ([0-9a-f]{8})", timeout=10)
				except pexpect.TIMEOUT:
					break
				handle = gt.match.group(1).decode() 
				uuid = gt.match.group(2).decode()

				if uuid == "00002902" and hr_handle: # HRM interaction (the handle that corresponds to UUID 0x2902)
					hr_ctl_handle = handle
					break

				elif uuid == "00002a37": # 2A37 Er stadart til uuid which is used for getting heart rates data from hrm device
					hr_handle = handle

			if hr_handle == None:
				log.error("Couldn't find the heart rate measurement handle?!")
				return

		if hr_ctl_handle:
			# We send the request to get HRM notifications
			gt.sendline("char-write-req " + hr_ctl_handle + " 0100") # char-write-req beder om at få HR målingerne. FORSTÅR IKKE DET HER! Hvordan giver den alt data
			
		# Time period between two measures. This will be updated automatically.
		period = 1.
		last_measure = time.time() - period
		hr_expect = "Notification handle = " + hr_handle + " value: ([0-9a-f ]+)"

		while 1:
			try:
				gt.expect(hr_expect, timeout=10)

			except pexpect.TIMEOUT:
				# If the timer expires, it means that we have lost the
				# connection with the HR monitor
				log.warn("Connection lost with " + addr + ". Reconnecting.")
				if sqlfile is not None:
					sq.commit()
				gt.sendline("quit")
				try:
					gt.wait()
				except:
					pass
				time.sleep(1)
				break

			except KeyboardInterrupt:
				log.info("Received keyboard interrupt. Quitting cleanly.")
				retry = False
				break

			# We measure here the time between two measures. As the sensor
			# sometimes sends a small burst, we have a simple low-pass filter
			# to smooth the measure.
			tmeasure = time.time()
			period = period + 1 / 16. * ((tmeasure - last_measure) - period)
			last_measure = tmeasure

			# Get data from gatttool     
			datahex = gt.match.group(1).strip() # Tager et input fra ???????????
			data = map(lambda x: int(x, 16), datahex.split(b' ')) #Convertere fra HEX til int.
			res = interpret(list(data))  # Skal converteres til en list for at kunne læse eller se indholdet.

			log.debug(res)
			heart_data(res, first)
			ani = FuncAnimation(plt.gct(), plotData, interval = 1000)
			plt.show()
			if sqlfile is None:
				
				log.info("Heart rate: " + str(res["hr"]))
				continue

			# Push the data to the database
			
			insert_db(sq, res, period)
			
	if sqlfile is not None:
		# We close the database properly
		sq.commit()
		sq.close()

	## Loads the .csv file that we just saved as a panda dataframe named dat
	dat = pd.read_csv("data.csv")
	myfigure=dat.plot.scatter(x="time",y="y").get_figure()
	myfigure.savefig("data-sampling.png")
	eg.msgbox(image="data-sampling.png")

	
	
	# We quit close the BLE connection properly
	gt.sendline("quit")
	try:
		gt.wait()
	except:
		pass


def cli():
	"""
	Entry point for the command line interface
	"""


	args = parse_args()

	if args.g != "gatttool" and not os.path.exists(args.g):
		log.critical("Couldn't find gatttool path!")
		sys.exit(1)

	# Increase verbose level
	if args.v:
		log.setLevel(logging.DEBUG)
	else:
		log.setLevel(logging.INFO)

	main(args.m, args.o, args.g, args.b, args.H, args.d)


if __name__ == "__main__": cli()
