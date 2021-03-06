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
import pexpect
import argparse
import configparser
import csv
import pandas as pd	
import numpy as np
import easygui as eg
from matplotlib import pyplot as plt
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

	# See if the BLEHeartRateLogger.conf file exist. 
	confpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "BLEHeartRateLogger.conf")
	if os.path.exists(confpath):

		config = configparser.ConfigParser()
		config.read([confpath])
		config = dict(config.items("config"))

		# We compare here the configuration given in the config file with the
		# configuration of the parser.
		args = (parser.parse_args([]))
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
	Bitwise operation is performed to interpret the data into res.
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
			res["rr"].append((((data[i + 1] << 8) | data[i])/1024)*1000)
			#print(res["rr"])
			i += 2

	return res


def get_ble_hr_mac():

	"""
	Scans BLE devices for 5 seconds. And add the found devices to the file mylog.txt. This is done by calling "hcitool lescan" 
	After lescan is called write the output to a log called mylog.txt
	Use expect to look for mac-addr
	"""
	
	while 1:
		log.info("Trying to find a BLE device")
		hci = pexpect.spawn("hcitool lescan, encoding='utf-8'") 
		hci.logfile = open("mylog.txt", "wb")
		time.sleep(5)
		try:
			
			hci.expect("(([0-9A-F]{2}[:-]){5}([0-9A-F]{2})) ([a-zA-Z0-9]+\s[a-zA-z0-9]+)", timeout=10)						
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

data=["time","y", "rr", 'HRV']
t0=time.time()	

def heart_data(res,file_name):
	hrv_variable = 0
	data_from_csv = pd.read_csv('data.csv')
	# if there is rr data in res.
	if "rr" in res:
		if type(data_from_csv['rr'].iloc[-1]) is str and len(data_from_csv) > 0: 
			data_from_csv['rr'] = data_from_csv['rr'].str.extract(r'([0-9]+)') # extract numbers in [ ]
			data_from_csv['rr'] = pd.to_numeric(data_from_csv['rr'])# convert from str to numbers 
			if len(data_from_csv) > 2: 
				hrv_variable = np.absolute(data_from_csv.iloc[-1,2] - data_from_csv.iloc[-2,2]) # calculate hrv from difference between last and current
				if(hrv_variable > 250): # normal range does not eccede 250 
					hrv_variable = 0 
		
		with open('data.csv', 'a') as csv_file:
			csv_writer = csv.writer(csv_file)
			data = [time.time()-t0, res["hr"], res["rr"], hrv_variable]
			csv_writer.writerow(data)
	# if no rr data in res, replace with 0
	else:
		with open('data.csv', 'a') as csv_file:
			csv_writer = csv.writer(csv_file)
			data = [time.time()-t0, res["hr"], hrv_variable]
			csv_writer.writerow(data)

	# Make backup data file for /data folder. 	
	if "rr" in res:
		with open(file_name+".csv",'a') as csv_file:
			csv_writer = csv.writer(csv_file)
			data2 = [time.time()-t0, res["hr"], res["rr"], hrv_variable]
			csv_writer.writerow(data2)
	else:
		with open(file_name+".csv",'a') as csv_file:
			csv_writer = csv.writer(csv_file)
			data2 = [time.time()-t0, res["hr"], hrv_variable]
			csv_writer.writerow(data2)


def main(addr=None, gatttool="gatttool", check_battery=False, hr_handle=None, debug_gatttool=False):
	"""
	main routine to which orchestrates everything
	"""
	
	if addr is None:
		# Call the function get_bla_hr_mac() to scan for BLE devices 
		get_ble_hr_mac()
		
		# Opens the logfile mylog.txt and creates a list called lines[]. Go through the mylog.txt and only takes the lines not containing "unknown". 
		# The lines are split with line.split() and append to the list lines, to make a list of lists. 
		with open("mylog.txt", "r") as mylogs:
				lines = []
			
				for line in mylogs:
					if "(unknown)" not in line: 
						line_list = line.split()
						lines.append(line_list)
								
				log.info(len(lines))
		
		#if no MAC adress this if statement return true. 
		if addr == None:
			# The hrv_variableiable gui is set to true, and controls whether the GUI should close or remain open. 
			gui = True
			# While loop to control if gui is true.  
			while gui: 
				# The first part of the gui creates five buttons to control the gui. 
				
				# message to be displayed  
				
				text = "Welcome to the Heart Rate monitoring program"
  
				# window title 
				title = "HR monitor"
  
				# button list 
				button_list = [] 
  
				# button 1 
				button1 = "Connect"
  
				# second button 
				button2 = "Live HR/HRV graphs"
  
				# third button 
				button3 = "Show HRV graph"
				
				# fourth button 
				button4 = "Show HR graph"
				
				# fifth button 
				button5 = "Cancel"
  
				# appending button to the button list 
				button_list.append(button1) 
				button_list.append(button2) 
				button_list.append(button3) 
				button_list.append(button4)
				button_list.append(button5) 
  
				# creating a button box 
				output = eg.buttonbox(text, title, button_list) 
  
				# printing the button pressed by the user 
				#print("User selected option : ", end = " ") 
				print(output) 

				# If the user clicks cancel, the gui will close
				if output == "Cancel":
					gui = False
				
				# If the user clicks connect the program shows up to three different devices to connect to. This is controlled with several if statements. 
				if output == "Connect":
					
					msg ="Which devices would you like to connect to?"
					title = "Connect"
					if len(lines)==2:
						choices = [lines[1]]
					if len(lines)==3:
						choices = [lines[1], lines[2]]
					if len(lines)==4:
						choices = [lines[1], lines[2],lines[3]]
	
					choice = eg.choicebox(msg, title, choices)
					
					#Several characters are replaces by the command .replace 
					s=choice
					s1=s.replace("'","")
					s2=s1.replace(",","")
					s3=s2.replace("[","")
					s4=s3.replace("]","")

					line_choice = []
					#The choise is split to create a list with the different elements in the string 
					line_choice = s4.split()
					
					# Depending on the amount of possible devices the MAC adress hrv_variableiable addr is set to the choice.   
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
						if line_choice[0] == lines[1][0]:
							addr = lines[1][0]	
						if line_choice[0] == lines[2][0]:
							addr = lines[2][0]
						if line_choice == lines[3][0]:
							addr = lines[3][0]

					# While retry is true we are trying to connect to the chosen device
					retry = True
					while retry:
						# Use gatttools to connect to MAC addr and wait for connection successful. if not try agian. 
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
						
						retry = False

				#If the user choses "Live HR/HRV graphs" it user webbrowser.open to access the live graph server.    
				if output == "Live HR/HRV graphs":
					if addr is not None:
						webbrowser.open('http://127.0.0.1:8050/')
					else:
						print("Please connect")
					gui = False
				
				
				# Here the current working directory is joined with the folder data, to access the folder where the data files are saved. 
				pwd = os.getcwd()
				ppwd = os.path.join(pwd,'data')
				
				#If the user clicks "Show HRV graph", the user can select a data file from the folder by using easygui.fileopenbox
				if output == "Show HRV graph":
					
					filename_hr=eg.fileopenbox("Select a series file", title, ppwd+"/", [["*.csv", "*.nybser", "Series File"]])
					data= pd.read_csv(filename_hr)
					
					# The data is plotted using matplotlib

					y=data['HRV']
					x=data['Time']

					fig = plt.figure()
					ax =fig.add_subplot(111)
					ax.set_xlabel('Time')
					ax.set_ylabel('HRV')
					ax.set_ylabel('Heart Rate hrv_variableability')
					ax.scatter(x,y,c='r',label='Your HRV')
					leg=ax.legend()
					plt.show()
					
					gui = False
				
				#Similar to show HRV, the button HR, can be used to show a graph of HR data. 
				if output == "Show HR graph":
					
					filename_hr=eg.fileopenbox("Select a series file", title, ppwd+"/", [["*.csv", "*.nybser", "Series File"]])
					data= pd.read_csv(filename_hr)

					y=data['HR']
					x=data['Time']
					fig = plt.figure()
					ax =fig.add_subplot(111)
					ax.set_xlabel('Time')
					ax.set_title('HR')
					ax.set_ylabel('Heart Rate')
					ax.scatter(x,y,c='r',label='Your heart rate')
					leg=ax.legend()
					plt.show()
							
					gui=False		

	hr_ctl_handle = None
	retry = True
	
	while retry:	
		if check_battery: # Check battery level.
			gt.sendline("char-read-uuid 00002a19-0000-1000-8000-00805f9b34fb") # Return batteri level!
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

			# We find fist the hr_handle and then the hr_ctl_handle. 
			# Hr_ctl_handle is used to subscribe to hr data.
			# hr_handle
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

				elif uuid == "00002a37": # 2A37 Er stadard til uuid which is used for getting heart rates data from hrm device
					hr_handle = handle

			if hr_handle == None:
				log.error("Couldn't find the heart rate measurement handle?!")
				return

		if hr_ctl_handle:
			# We send the request to get HRM notifications
			gt.sendline("char-write-req " + hr_ctl_handle + " 0100") 

		# Time period between two measures. This will be updated automatically.
		period = 1.
		last_measure = time.time() - period
		# contains the hrm data
		hr_expect = "Notification handle = " + hr_handle + " value: ([0-9a-f ]+)"

		current_date_and_time = datetime.datetime.now()
		current_date_and_time_string = str(current_date_and_time)
		file_name = "data/data-"+current_date_and_time_string
					
		with open(file_name+".csv","w") as csv_file:
			csv_writer = csv.writer(csv_file)
			data2 = ['Time', 'HR', 'RR', 'HRV']
			csv_writer.writerow(data2)

		# If the connection to the device is lost, the program tries to reconnect 
		while 1:
			try:
				gt.expect(hr_expect, timeout=10)

			except pexpect.TIMEOUT:
				# If the timer expires, it means that we have lost the
				# connection with the HR monitor
				log.warning("Connection lost with " + addr + ". Reconnecting.")

				gt.sendline("quit")
				try:
					gt.wait()
				except:
					pass
				time.sleep(1)
				
				# Reconnect if connection is lost in case of timeout. 
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

				log.info("Connected to " + addr)	
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
			datahex = gt.match.group(1).strip() 
			data = map(lambda x: int(x, 16), datahex.split(b' ')) #Convert from HEX to int.
			res = interpret(list(data))  # Converting to a list. 

			log.debug(res)
			
			# Calls function heart data, that inserts data into files. 
			heart_data(res,file_name)

			#Print Hr in terminal
			log.info("Heart rate: " + str(res["hr"]))
			
	
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
		data = ['Time', 'HR', 'rr', 'HRV']
		csv_writer.writerow(data)

	# use parse_args to check if a .conf file exist. 
	args = parse_args()

	if args.g != "gatttool" and not os.path.exists(args.g):
		log.critical("Couldn't find gatttool path!")
		sys.exit(1)

	# Increase verbose level
	if args.v:
		log.setLevel(logging.DEBUG)
	else:
		log.setLevel(logging.INFO)
	# call function.
	main(args.m, args.g, args.b, args.H, args.d)


if __name__ == "__main__": cli()
