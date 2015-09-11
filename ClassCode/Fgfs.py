# Thread to interface w/ FlightGear running as a subprocess
# Directories and task-specific parameters are found in ClassCode/MPs.rc

import subprocess, socket, struct, time, threading, os.path
from collections import deque

import imp, sys
def rel():
	imp.reload(sys.modules['Fgfs'])
	
#	import Fgfs;	fg = Fgfs.Fgfs(); 	fg.start()
	
class Fgfs (threading.Thread):
	'''manage a Flightgear thread on UDP data / command ports dp & cp
		__init__ uses the mp line in the file MPs.rc to position the starting point for the aircraft 
		startFgfs opens a FlightGear process connected w/ bidirectional outest.xml protocol
		getDat() & putCmd provide an IO interface w/ AI or human cockpit
		a dataLock insulates changes to datByts & cmdByts between FlightGear & cockpit / AI
		datRate and cmdRate are higher than the process can support (more like 3/sec)'''
	
	def __init__(sf,tsk,ccd,dp=4040,cp=4041):
		'''build a thread to run FlightGear; tsk is the desired task name (e.g, MPx); ccdir is the full CourseCode directory to locate MPs.rc regardless of the current connected directory'''
		threading.Thread.__init__(sf)
		sf.host = 'localhost'		# host to process fgfs data packets and issue fgfs command packets
		sf.datPort = dp			# port for UDP data (fgfs output) packets
		sf.cmdPort = cp			# port for UDP command (fgfs input) packets
		sf.datRate = 5			# (max) rate for FG to send data packets
		sf.cmdRate = 5			# rate for FG to accept commnad packets
		sf.dataLock = threading.Lock()		# hold while reading or writing lastDat & nxtCmd
		sf.subProc = None		# subprocess handle for fgfs
		sf.datByts = b''			# tuple of last data received from fgfs
		sf.cmdByts = b''			# tuple of pending command data for fgfs or b'' (''.encode())
		sf.flying = False			# kill FG and terminate when becomes False in run loop
		sf.tskName = tsk			#	used w/ file MPs.rc to initalize plane location
		sf.ccdir = ccd				# directory to find file MPs.rc; passed from Ckpt
		sf.kbdCtl = None		# computer keyboard or joystick control is direct (not via outest protocol)

	def run(sf):
		'''initialize: start fgfs, set up sockets; protecting datByts and cmdByts with dataLock, loop updating datByts with fgfs data and sending cmdByts when they appear'''
		sf.startFgfs()		# should fail gracefullyif fgfs does not start
		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as datSoc, \
				socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cmdSoc:
			datSoc.bind((sf.host, sf.datPort))
			sf.flying = True
			try:
				while sf.flying:
					sndByts = b''
					recByts = datSoc.recv(1024)					# block waiting for fgfs data
					suc = sf.dataLock.acquire(timeout=10)		# get lock isolating both comByts
					if not suc: raise ValueError('Fgfs run failed to get dataLock')
					sf.datByts = recByts			# update data bytes from received UDP packet
					if sf.cmdByts:						# new command to send?
						sndByts = sf.cmdByts		# local copy for sending after lock release
						sf.cmdByts = b''				# delete to avoid resending commands
					sf.dataLock.release()
					if not sf.kbdCtl and sndByts: 
						cmdSoc.sendto(sndByts, (sf.host, sf.cmdPort))	# don't send if keyboard/joystick in control
			finally:
				sf.flying = False
				sf.exitFgfs()
				
	def setKbd(sf,kbdFlg):
		'''kbdFlg True means the computer keyboard or joystick is in control and should not be countermanded by protocol packet commands'''
#		print('setKbd', kbdFlg)
		sf.kbdCtl = kbdFlg
		
	def startFgfs(sf):
		'''Construct and return a list suitable for popen to start fgfs on machine problem sf.tskName; data from file MPs.rc'''
		global lne, fgloc, rootloc, fgfsExc
		fgfsExc = []
		with open(sf.ccdir + '/MPs.rc', 'r') as inFil:
			lne = inFil.readline()
			if lne == '': raise EOFError('Premature EOF; no MP lines found')
			fgloc = os.path.abspath(lne.strip())		# first line should be path to FG executable
			lne = inFil.readline()
			rootloc = os.path.abspath(lne.strip())	# second line should be $FG_ROOT
			lne = inFil.readline()
			lne = inFil.readline()
			lne = inFil.readline()
			lne = inFil.readline()
			if lne != '\n': raise IOError('Garbage in MPs.rc: {}'.format(lne))
#	maybe delete following, change print to pass, or just test for error
			if os.path.exists(fgloc + '.exe'): print('Windows')
			elif os.path.exists(fgloc): print('Posix')
			else: raise OSError('No FlightGear executable found at {}'.format(fgloc))
			fgfsExc.append(fgloc)
#			rootloc = os.path.join(os.path.split(os.path.split(fgloc)[0])[0], 'data')
			fgfsExc.append('--fg-root=' + rootloc)
			fgfsExc.append('--fg-scenery=' + os.path.join(rootloc, 'Scenery'))
			fgfsExc.append('--generic=socket,out,{},{},{},udp,outest'.format(sf.datRate, sf.host, sf.datPort))
			fgfsExc.append('--generic=socket,in,{},{},{},udp,outest'.format(sf.cmdRate, sf.host, sf.cmdPort))
			while sf.tskName != 'notSet':
				lne = inFil.readline()
				if lne == '': raise EOFError('Premature EOF; cannot find desired MP: {}'.format(sf.tskName))
				elif lne.startswith(sf.tskName):		# found the arguments for the desired MP
					for arg in (lne.split(' '))[1:]:		# skip mp indicator at front # & \n at end
						fgfsExc.append(arg)
					break
		if not os.path.basename(fgfsExc[0]) == 'fgfs': raise NameError('Not FlightGear')
		sf.subProc = subprocess.Popen(fgfsExc)

	def killFgfs(sf):
		'''Exit the run loop'''
		sf.flying = False
		
	def exitFgfs(sf):
		'''Called on run exit to kill FlightGear process'''
		sf.subProc.terminate()
		
	def getDat(sf):
		'''safely get sf.datByts & return it'''
		suc = sf.dataLock.acquire(timeout=10)		# get lock isolating both comByts
		if not suc: raise ValueError('Fgfs getData cant get dataLock')
		getByts = sf.datByts
		sf.dataLock.release()
		return getByts
		
	def putCmd(sf,putByts):
		'''safely set sf.cmdByts to command putByts; return True if prev command was serviced'''
		suc = sf.dataLock.acquire(timeout=10)		# get lock isolating both comByts
		if not suc: raise ValueError('Fgfs setCmd cant get dataLock')
		uptodate = sf.cmdByts == b''
		sf.cmdByts = putByts
		sf.dataLock.release()
		return uptodate
	
