# Simple example of taxiing as scripted behavior
# import Pilot; a=Pilot.Pilot(); a.start()

import Ckpt as Ckpt

import imp, sys
def rel():
	imp.reload(sys.modules['Pilot'])

class Pilot (Ckpt.Ckpt):			# subclass of the class Ckpt in the file Ckpt
	
	def __init__(sf,tsk='MP2',rc=False,gui=False):
		super().__init__(tsk, rc, gui)
		sf.strtTime = None
		sf.duration = None
			
	def ai(sf,fDat,fCmd):
		'''Override with the Pilot decision maker, args: fltData and cmdData from Utilities.py'''
		if not fDat.running:
			sf.strtTime = fDat.time
		sf.duration = fDat.time - sf.strtTime
		if abs(fDat.roll) > 5.:			# first check for excessive roll
			print('Points lost for tipping; {:.1f} degrees at {:.1f} seconds'.format(fDat.roll, sf.duration))
		if sf.duration < 2.0:			# full power for 2 seconds
			fCmd.throttle = 1.0
			fCmd.rudder = -0.7
		elif sf.duration < 7.0:		# reasonable taxiing for 5 seconds
			fCmd.throttle = 0.1
			fCmd.rudder = 0.8
		elif sf.duration < 14.:		# tipping from too much power; too tight a turn
			fCmd.throttle = 0.8
			fCmd.rudder = -1.0
		elif sf.duration < 40.:		# coast until 40 seconds then exit
			fCmd.throttle = 0.0
			fCmd.rudder = 0.7
		else: return 'stop'

		
		
		
