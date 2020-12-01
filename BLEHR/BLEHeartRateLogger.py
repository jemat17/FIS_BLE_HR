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
import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
import webbrowser
import datetime





data=["time","y", "rr"]


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
		hci = pexpect.spawn("hcitool lescan, encoding='utf-8'") 
		hci.logfile = open("mylog.txt", "wb")
		time.sleep(5)
		try:
			
			hci.expect("(([0-9A-F]{2}[:-]){5}([0-9A-F]{2})) ([a-zA-Z0-9]+\s[a-zA-z0-9]+)", timeout=10)		## Ikke nødvendig!				
			hci.close()
			break

			
		except pexpect.TIMEOUT:
			return None
			time.sleep(20)
			continue

		except KeyboardInterrupt:
			log.info("Received keyboard interrupt. Quitting cleanly.")
			hci.close()
			break

	# We wait for the 'hcitool lescan' to finish
	time.sleep(1)
	 

data=["time","y", "rr"]
t0=time.time()	


def heart_data(res, first,file_name):
	
	#while True:

	if "rr" in res:
		with open('data.csv', 'a') as csv_file:
			csv_writer = csv.writer(csv_file)
			data = [time.time()-t0, res["hr"], res["rr"]]
			csv_writer.writerow(data)
	else:
		with open('data.csv', 'a') as csv_file:
			csv_writer = csv.writer(csv_file)
			data = [time.time()-t0, res["hr"], -1]
			csv_writer.writerow(data)
			
	if "rr" in res:
		with open(file_name+".csv",'a') as csv_file:
			csv_writer = csv.writer(csv_file)
			data2 = [time.time()-t0, res["hr"], res["rr"]]
			csv_writer.writerow(data2)
	else:
		with open(file_name+".csv",'a') as csv_file:
			csv_writer = csv.writer(csv_file)
			data2 = [time.time()-t0, res["hr"], -1]
			csv_writer.writerow(data2)


def main(addr=None, sqlfile=None, gatttool="gatttool", check_battery=False, hr_handle=None, debug_gatttool=False):
	"""
	main routine to which orchestrates everything
	"""
	if addr is None:
		first = False
	
	if sqlfile is not None:
		# Init database connection
		sq = sqlite3.connect(sqlfile)
		with sq:
			sq.execute("CREATE TABLE IF NOT EXISTS hrm (tstamp INTEGER, hr INTEGER, rr INTEGER)")
			sq.execute("CREATE TABLE IF NOT EXISTS sql (tstamp INTEGER, commit_time REAL, commit_every INTEGER)")

	if addr is None:
		# In case no address has been provided, we scan to find any BLE devices
		get_ble_hr_mac()
		
		with open("mylog.txt", "r") as mylogs:
				lines = []
			
				for line in mylogs:
					if "(unknown)" not in line: #husk at tilføje NOT 
						stripped_line = line.strip()
						line_list = stripped_line.split()
						lines.append(line_list)
								
				log.info(len(lines))
		if addr == None:
			
			gui = True
			while gui: 
	# message to be displayed  
				
				text = "Welcome to the Heart Rate monitoring program"
  
	# window title 
				title = "HR monitor"
  
	# button list 
				button_list = [] 
  
	# button 1 
				button1 = "Connect"
  
	# second button 
				button2 = "Show HR graph"
  
	# third button 
				button3 = "Show HRV graph"
				
				button4 = "HR - not live"
  
	# appending button to the button list 
				button_list.append(button1) 
				button_list.append(button2) 
				button_list.append(button3) 
				button_list.append(button4) 
  
  
	# creating a button box 
				output = eg.buttonbox(text, title, button_list) 
  
	# printing the button pressed by the user 
				#print("User selected option : ", end = " ") 
				print(output) 

				if output == "Connect":
					
					msg ="Which devices would you like to connect to?"
					title = "Connect"
					if len(lines)==2:
						choices = [lines[1]]
					if len(lines)==3:
						choices = [lines[1], lines[2]]
					if len(lines)==4:
						choices = [lines[1], lines[2],lines[3]]
						#print(choices)
	
					choice = eg.choicebox(msg, title, choices)
					
					s=choice
					s1=s.replace("'","")
					s2=s1.replace(",","")
					s3=s2.replace("[","")
					s4=s3.replace("]","")

					line_choice = []
					line_choice = s4.split()
					
					if len(lines)==2:
						if line_choice[0] == lines[1][0]:
							addr = lines[1][0]
				
					if len(lines)==3:
						if line_choice[0] == lines[1][0]:
							addr = lines[1][0]
						if line_choice[0] == lines[1][0]:
							addr = lines[1][0]	
						if line_choice[0] == lines[2][0]:
							addr = lines[2][0]
						
					if len(lines)==4:
						print("DAV")
						if line_choice[0] == lines[1][0]:
							addr = lines[1][0]	
						if line_choice[0] == lines[2][0]:
							addr = lines[2][0]
						if line_choice == lines[3][0]:
							addr = lines[3][0]


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
						
						retry = False


				if output == "Show HR graph":
					if addr is not None:
						webbrowser.open('http://127.0.0.1:8050/')
					else:
						print("Please connect")
					gui = False
				
				pwd = os.getcwd()
				ppwd = os.path.join(pwd,'data')
				
				if output == "Show HRV graph":
					
					filename_hr=eg.fileopenbox("Select a series file", title, ppwd+"/", [["*.csv", "*.nybser", "Series File"]])
					data= pd.read_csv(filename_hr)

					x=data['RR']

					fig = plt.figure()
					ax =fig.add_subplot(111)
					ax.set_xlabel('Time')
					ax.set_ylabel('RR-intervel')
					ax.plot(x,c='r',label='Your RR-interval')
					leg=ax.legend()
					plt.show()
					
					gui = False
				

				if output == "HR - not live":
					
					filename_hr=eg.fileopenbox("Select a series file", title, ppwd+"/", [["*.csv", "*.nybser", "Series File"]])
					data= pd.read_csv(filename_hr)

					x=data['HR']

					fig = plt.figure()
					ax =fig.add_subplot(111)
					ax.set_xlabel('Time')
					ax.set_ylabel('Heart Rate')
					ax.plot(x,c='r',label='Your heart rate')
					leg=ax.legend()
					plt.show()
							
					gui=False		
			
	#sq.close()
	hr_ctl_handle = None
	retry = True
	
	while retry:	
		#while 1:
		#	a=2 #RANDOM
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

		current_date_and_time = datetime.datetime.now()
		current_date_and_time_string = str(current_date_and_time)
		file_name = "data/data-"+current_date_and_time_string
					
		with open(file_name+".csv","w") as csv_file:
			csv_writer = csv.writer(csv_file)
			data2 = ['Time', 'HR', 'RR']
			csv_writer.writerow(data2)


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
				
				while 1:
					log.info("Establishing connection to " + addr)
					gt = pexpect.spawn(gatttool + " -b " + addr + " -t random --interactive")
					if debug_gatttool:
						gt.logfile = sys.stdout
						gt.expect(r"\[LE\]>")
						gt.sendline("connect")
				
					try:
						i = gt.expect(["Connection successful.", r"\[CON\]"], timeout=30)
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
			heart_data(res, first,file_name)
			# if startApp == True:
			# 	app.run_server(debug=True)
			# 	startApp = False
			
			
			if sqlfile is None:
				
				log.info("Heart rate: " + str(res["hr"]))
				continue

			# Push the data to the database
			
			insert_db(sq, res, period)
			
	if sqlfile is not None:
		# We close the database properly
		sq.commit()
		sq.close()
	
	
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
	with open('data.csv', 'w') as csv_file:
		csv_writer = csv.writer(csv_file)
		data = ['Time', 'HR', 'rr']
		csv_writer.writerow(data)


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
