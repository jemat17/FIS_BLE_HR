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
	choice = eg.choicebox(msg, title, choices)

