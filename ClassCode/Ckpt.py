# FGFS cockpit controller

import imp, sys
def rel():
	imp.reload(sys.modules['Ckpt'])
	
import tkinter as tk
from tkinter import ttk
import struct, time, pickle
import os.path

_TK = tk.Tk()
_TK.withdraw()

# Ensure the ClassCode directory exists 
_CCDir = os.path.abspath('.')
if os.path.basename(_CCDir) != 'ClassCode':
	_CCDir = os.path.join(_CCDir, 'ClassCode')
	if not os.path.isdir(_CCDir): raise IOError('No ClassCode in {}'.format(os.path.dirname(_CCDir)))

try: from . import Utilities, Fgfs							# being run from parent directory
except SystemError: import Utilities, Fgfs		# being run from ClassCode

	
class Ckpt:
	'''build a minimal graphic cockpit to control the FlightGear process'''
	
	stkRes = 200					# joystick canvas size
	fltStepSpan = 10			# record flight point every nth packet exchange in recSnd

	def __init__(sf,tsk='notSet',rc=False,gui=True):
		'''FGFS interface and flight control cockpit & information display'''
		sf.ccDir = _CCDir		# make the ClassCode directory available to AI via getWayPts()
		sf.task = tsk
		sf.rcrdP = rc				# save data packets to fltPath anc cmdPath if True
		sf.fltPath = []
		sf.cmdPath = []
		sf.fltStep = 0
		sf.fltCmds = Utilities.CmdData()			# object to organize flight commands
		sf.fltData = Utilities.FltData()				# object to organize flight data
		sf.strtE = False						# Boolean; True: engine start commanded but not yet running
		sf.fg = None
		sf.runningP = None
		sf.fgFltPkt = None					# string for packed flight data
		sf.fgCmdPkt = None				# for packed command data
		if gui:
			sf.guiP = True
			sf.addGuiCtls()
		else: 
			sf.guiP = False
			sf.inCtl = tk.IntVar()
			sf.inCtl.set(2)

	def start(sf):
		'''Set the engine to automatically start when running & launch FlightGear'''
		sf.strtEng()
		sf.strtFG()

	def addGuiCtls(sf):
		sf.myWin = tk.Toplevel()
		sf.myWin.grid()
		sf.myWin.title('Flight Control Panel')
		sf.jStk = JoyStick(sf.stkRes)		# object to manage the 2D joystick position <-> values
		fltDesc = ['KIAS', 'Altitude', 'Heading', 'Pitch', 'Roll', 'Latitude', 'Longitude']	# flight info display labels
		sf.fltFmts = ['{:5.1f}     ', '{:7.1f}   ', '{:5.1f}     ',  '{:5.1f}     ',  '{:5.1f}     ',  '{:5.1f}     ',  '{:5.1f}     ']

		# Flight data display
		fltLbls = [ttk.Label(sf.myWin, text=fltDesc[i], relief=tk.FLAT) for i in range(len(fltDesc))]
		sf.fltTxts = [tk.Text(sf.myWin, width = 10, height=1) for fd in fltDesc]
		for i in range(len(fltDesc)):
			fltLbls[i].grid(row=i, column=3, sticky=tk.E)
			sf.fltTxts[i].grid(row=i, column=4)
			
		# Flight controls: stick square and ball
		sf.stkC = tk.Canvas(sf.myWin, width=sf.stkRes, height=sf.stkRes)
		sf.stkC.create_rectangle(2, 2, sf.stkRes + 1, sf.stkRes + 1, outline='black', fill='light blue')
		sf.stkC.bind( "<B1-Motion>", sf.setStkCtl)
		sf.stkC.bind( "<Button-1>", sf.setStkCtl)
		sf.stkC.grid(row=0, column=0, columnspan=3, rowspan=10) # , columnspan=2)
		sf.jStk.setup(sf.stkC)			# attach the cockpit joystick canvas to the JoyStick object
		# rudder control & label
		sf.rudS = ttk.Scale(sf.myWin, orient=tk.HORIZONTAL, from_=-1., to=1., \
				command=(lambda x: setattr(sf.fltCmds, 'rudder', float(x))) )
		sf.rudS.grid(row=11, column=0, columnspan=3, sticky='EW')
		tk.Label(sf.myWin, text='Rudder', relief=tk.FLAT).grid(row=12, column=1, sticky='N')
		# throttle control & label
		sf.thrS = ttk.Scale(sf.myWin, orient=tk.VERTICAL, from_=1., to=0., \
				command=(lambda x: setattr(sf.fltCmds, 'throttle', float(x))) )
		sf.thrS.grid(row=11, column=3, rowspan = 2, sticky='NS')
		tk.Label(sf.myWin, text='Throttle', relief=tk.FLAT).grid(row=13, column=3, sticky='N')
		# mixture control & label
		sf.mixS = ttk.Scale(sf.myWin, orient=tk.VERTICAL, from_=1., to=0., \
				command=(lambda x: setattr(sf.fltCmds, 'mixture', float(x))) )
		sf.mixS.grid(row=11, column=4, rowspan = 2, sticky='NS')
		ttk.Label(sf.myWin, text='Mixture', relief=tk.FLAT).grid(row=13, column=4, sticky='N')
		# start engine button
		sf.strtB = tk.Button(sf.myWin, text='Start Eng', command=sf.strtEng)
		sf.strtB.grid(row=13, column=0, sticky='EW')
		sf.strtBbgRgb = sf.strtB.cget('bg')
		# launch FGFS button
		sf.fgB = tk.Button(sf.myWin, text='FGFS', command=sf.strtFG)
		sf.fgB.grid(row=13, column=1, sticky='EW')
		# quit everything button
		sf.quitB = tk.Button(sf.myWin, text='Quit', command=sf.endAll)
		sf.quitB.grid(row=13, column=2, sticky='EW')
		
		# Keyboard, Cockpit, AI selection
		sf.inCtl = tk.IntVar()
		sf.rb1 = ttk.Radiobutton(sf.myWin, text='Kbd', variable=sf.inCtl, value=0, command=sf.selected)
		sf.rb2 = ttk.Radiobutton(sf.myWin, text='Ckpt', variable=sf.inCtl, value=1, command=sf.selected)
		sf.rb3 = ttk.Radiobutton(sf.myWin, text='AI', variable=sf.inCtl, value=2, command=sf.selected)
		sf.rb1.grid(row=14, column=0)
		sf.rb2.grid(row=14, column=1)
		sf.rb3.grid(row=14, column=2)

	def selected(sf):
		'''service radio buttons for selecting inputs from Kbd, Ckpt, AI'''
		if not sf.fg:
			print('Cannot select control input; no FGFS started')
			return
		if sf.inCtl.get()==0:	# keyboard so tell fgfs not to send command packets
			sf.fg.setKbd(True)
		else:
			sf.fg.setKbd(False)
#		print('selected', sf.inCtl.get())

	def recSnd(sf):
		'''Loop waiting for a data packet, decode, then send a command packet'''
		itr = 0;	lstTik = 0.
		badPkts = 0
		while sf.runningP:
			if sf.guiP: sf.myWin.update()
			time.sleep(0.2)		# avoid busy waiting while FGFS process initializes
			sf.fgFltPkt = sf.fg.getDat()		# wait for a data packet from fgfs object
#			if len(sf.fgFltPkt) != FltData.datPktLen:	# wrong length packet
			if len(sf.fgFltPkt) != Utilities.FltData.datPktLen:	# wrong length packet
				if lstTik > 0.:						# count bad pkts but only count after fgfs starts
					badPkts += 1
					sf.savBadPkt = sf.fgFltPkt
					print('{} bad packets, last length {}'.format(badPkts, len(sf.fgFltPkt)))
				continue
			if sf.rcrdP and sf.fltStep >= Ckpt.fltStepSpan:
				sf.fltPath.append(sf.fgFltPkt)
				sf.cmdPath.append(sf.fgCmdPkt)
				sf.fltSetp = 0
			else: sf.fltStep += 1
			sf.fltData.decFData(sf.fgFltPkt)
			if sf.guiP:
				for fFmt,txtB,fdVal in zip(sf.fltFmts, sf.fltTxts, sf.fltData.getFData()):
					txtB.insert('1.0', fFmt.format(fdVal))
			if sf.inCtl.get() == 2: 					# allow for AI control
				if sf.ai(sf.fltData, sf.fltCmds) == 'stop':
					sf.endAll()
					sf.runningP = False				# terminate with ai value of 'stop'
			if sf.strtE and sf.fltData.running: 
				sf.strtE = False			# starter & engine running; turn off starter
				if sf.guiP: sf.strtB.config(bg=sf.strtBbgRgb)	#	'SystemButtonFace')
			sf.fltCmds.starter = sf.strtE					# set eng. starter
			if sf.inCtl != 0: 				# set up current flight commands
				sf.fgCmdPkt = sf.fltCmds.encCmds(sf)
				sf.fg.putCmd(sf.fgCmdPkt)
			itr += 1
			if itr % 50 == 0: 
#				print('{:}: {:.2f} {:}'.format(itr, sf.fltData.time - lstTik, sf.fltData.time))
				lstTik = sf.fltData.time
		sf.fg.killFgfs()								# clean up on loop exit
		if sf.guiP: sf.myWin.destroy()
				
	def ai(sf,flightData,commandData):
		'''Override with an AI decision maker'''
		print('No AI present')
			
	def setStkCtl(sf,evnt):
		'''Post the aileron and elevator commands'''
		sf.fltCmds.aileron, sf.fltCmds.elevator = sf.jStk.pos2val(evnt)
		
	def strtEng(sf):
		'''start engine button'''
		# insure some throttle; max to avoid reducing to .1 w/ in-air restart
		sf.fltCmds.throttle = max(0.1, sf.fltCmds.throttle)		
		sf.fltCmds.mixture = 1.0				# mixture full rich
		sf.strtE = True							# crank engine
		if sf.guiP: sf.strtB.config(bg='light blue')
		print('Start engine')

	def strtFG(sf):
		'''launch FlightGear'''
		print('Start FGFS')
		sf.fg = Fgfs.Fgfs(sf.task, _CCDir)
		sf.fg.start()
		sf.runningP = True
		sf.selected()
		sf.recSnd()

	def endAll(sf):
		'''end loop, generating a flight path binary file LastFlight.fpb if rcrdP is True'''
		print('Quit')
		if sf.rcrdP:
			filNam = 'LastFlight.' + ('-' if sf.task=='notSet' else sf.task) + '.pkl'
			with open(filNam, 'wb') as outFil:
				pickle.dump(sf.fltPath, outFil)
				pickle.dump(sf.cmdPath, outFil)
			print('finished writing points to {}'.format(filNam))
		if sf.runningP: sf.runningP = False
		elif sf.guiP: sf.myWin.destroy()
		
	def endAllOLD(sf):
		'''end loop, generating a flight path binary file LastFlight.fpb if rcrdP is True'''
		print('Quit')
		if sf.rcrdP:
			filNam = 'LastFlight.' + ('-' if sf.task=='notSet' else sf.task) + '.fpb'
			with open(filNam, 'wb') as outFil:
				for pt in sf.fltPath:
#					if len(pt) == FltData.datPktLen: outFil.write(pt)
					if len(pt) == Utilities.FltData.datPktLen: outFil.write(pt)
					else: print('Bad length point', len(pt))
			print('finished writing points to {}'.format(filNam))
		if sf.runningP: sf.runningP = False
		elif sf.guiP: sf.myWin.destroy()
		
	def getWayPts(sf,tsk):
		'''allow AI Ckpt subclass access to the way points file for this task via Utilities'''
		return Utilities.getWayPts(tsk, sf.ccDir)
		
	def grade(sf,fn='notSet',ret=False):
		'''allow AI Ckpt subclass access to grading via Utilities'''
		if fn == 'notSet': filNam = 'LastFlight.' + ('-' if sf.task=='notSet' else sf.task) + '.pkl'
		else: filNam = fn
		return Utilities.grade(filNam, ret)
	
class JoyStick:
	
	def __init__(sf,canSz):
		'''Manage the joystick display and aileron & elevator control'''
		sf.hRes = canSz / 2
		sf.stkRad = 4
		sf.x = sf.hRes
		sf.y = sf.hRes
		
	def setup(sf,stkCan):
		'''build & attach the JoyStick circle to the cockpit joystick canvas'''
		sf.stkC = stkCan
		sf.stk = sf.stkC.create_oval(sf.hRes-sf.stkRad, sf.hRes-sf.stkRad, sf.hRes+sf.stkRad, sf.hRes+sf.stkRad, fill='black')

	def val2pos(sf,ailr,elev):
		'''Simulate a joystick mouse event'''
		sf.x = int(max(-1., min(1., ailr)) * sf.hRes) + sf.hRes 
		sf.y = int(max(-1., min(1., elev)) * sf.hRes) + sf.hRes 
		
	def pos2val(sf,evnt):
		'''service cockpit stick motions'''
		sf.stkC.coords(sf.stk, evnt.x-sf.stkRad, evnt.y-sf.stkRad, evnt.x+sf.stkRad, evnt.y+sf.stkRad)
		return max(-1., min(1., evnt.x / sf.hRes - 1.)), max(-1., min(1., 1. - evnt.y / sf.hRes))
	
	
