# Shared utility files

import imp, sys
def rel():
	imp.reload(sys.modules['Utilities'])
	
import os.path
import struct, math, pickle
from tkinter import filedialog as tkf

# need numpy as np
_NUMPYP = True
try: import numpy as np
except ImportError:
	_NUMPYP = False
	print('Numpy is missing; no access to grade computation')

# Ensure access to ClassCode directory
_CCDir = os.path.abspath('.')
if os.path.basename(_CCDir) != 'ClassCode':
	_STDir = _CCDir
	_CCDir = os.path.join(_STDir, 'ClassCode')
	if not os.path.isdir(_CCDir): raise IOError('No ClassCode in {}'.format(os.path.dirname(_STDir)))
	
# latitude differences, measured along a longitude line and in longitude degrees are constant, 
# but longitude differences, measured along a latitude and in latitude degrees are shorter in higher lats
# multiply by _lat2lon to convert measurements along a latitude line into the same distance measured along a longitude line

_deg2met = 110977.			# meters in one degree latitude
_lat2lon = 0.794				# multiply degrees along longitude * this to get equiv dist in latitude degs
_eps = 1e-10						# epsilon to use for zero w/ roundoff errors

class FltData:
	
	datStrct = struct.Struct('>ffffffff?')					# structure to decode flight data packet
	datPktLen = struct.calcsize(datStrct.format)		# correct packet length

	@staticmethod
	def retData(pkt):
		'''unpack an fgfs data and return the data fields as a list'''
		return  FltData.datStrct.unpack(pkt)

	def __init__(sf):
		'''KIAS, altitude, heading, pitch, roll, latitude, longitude, time, running'''
		sf.kias = 0.0			# indicated air speed in knots
		sf.altitude = 0.0		# height in feet above mean sea level
		sf.head = 0.0			# aircraft heading in degrees CW from north
		sf.pitch = 0.0			# lateral axis up / down angle in degrees
		sf.roll = 0.0			# degree rotation about the aircraft's longitudinal axis
		sf.latitude = 0.0		# north latitude position
		sf.longitude = 0.0	# west longitude position (negative)
		sf.time = 0.0			# simulator clock time of this observation
		sf.running = False	# Boolean for engine running
		
	def getFData(sf):
		'''convenience function for easy access, returning all data in a tuple'''
		return sf.kias, sf.altitude, sf.head, sf.pitch, sf.roll, sf.latitude, sf.longitude, sf.time, sf.running

	def decFData(sf,pkt):
		'''unpack an fgfs data packet into data fields'''
		sf.kias, sf.altitude, sf.head, sf.pitch, sf.roll, sf.latitude, sf.longitude, sf.time, sf.running =  sf.datStrct.unpack(pkt)

class CmdData:

	cmdStrct = struct.Struct('>fffffi?')						# structure to encode command packet:

	@staticmethod
	def retData(pkt):
		'''unpack an command data and return the data fields as a list'''
		return  CmdData.cmdStrct.unpack(pkt)

	def __init__(sf):
		'''aileron, elevator, rudder, throttle, mixture, magnitos, starter'''
		sf.aileron = 0.0
		sf.elevator = 0.0
		sf.rudder = 0.0
		sf.throttle = 0.0
		sf.mixture = 0.0
		sf.magnitos = 3
		sf.starter = False
		
	def encCmds(sf,ckpt):
		'''Update the display and return a packet reflecting the current command values'''
		if ckpt.guiP:
			ckpt.rudS.set(sf.rudder)
			ckpt.thrS.set(sf.throttle)
			ckpt.mixS.set(sf.mixture)
		return sf.cmdStrct.pack(sf.aileron, sf.elevator, sf.rudder, sf.throttle, sf.mixture, sf.magnitos, sf.starter)
		
def getWayPts(tsk,ccDir='notSet',fnam='notSet'):
	'''read in a waypoints file, return the list of (lat, long, heading) points'''
	if ccDir == 'notSet': ccDir = _CCDir
	if fnam == 'notSet': wpFilNam = ccDir + '/' + tsk + '.wpts'
	else: wpFilNam = fnam
	pts = []
	with open(wpFilNam, 'r') as inFil:
		fileTitle = inFil.readline()[:-1]
		inFil.readline()
		while True:
			pt = inFil.readline()
			if pt in ('', '\n'): break
			pts.append([float(num.strip()) for num in pt.split(',')])
	print('{}\n{}:  {} pts'.format(wpFilNam, fileTitle, len(pts)))
	return pts
	
def getPathData(fnam='flt.pkl',crashed=False):
	'''return a numpy array of the 9 flight data values and 7 command data values from the pickle file of the flight path and command path'''
	with open(fnam, 'rb') as fd:
		fltPath = pickle.load(fd)
		cmdPath = pickle.load(fd)
	fullPath = np.zeros((16, len(fltPath)), dtype=float)
	i = 0
	gdIdxs = []
	lstTm = 1.0
	for flt,cmd in zip(fltPath, cmdPath):	# insert in numpy array, removing temporal duplicates
		fullPath[:9, i] = FltData.retData(flt)
		fullPath[9:, i] = CmdData.retData(cmd)
		dt = fullPath[7, i] - lstTm
		if dt > 0.0 and dt < 5.0:	# ignore duplicate times and long pauses during startup
#			if fullPath[7, i] > lstTm:
			gdIdxs.append(i)
		lstTm = fullPath[7, i]
		i += 1
	path = fullPath[:, gdIdxs]
	if crashed:
		path = path[:, :-5]		# delete the last 5 time points so crashing doesn't corrupt chart normalization
	return path

def readFP(fltFil='LastFlight.pkl'):
	'''load a pckled Flight Path file; each point contains:
	kias, altitude, head, pitch, roll, latitude, longitude, time, runningP
	collect all but runningP into a Numpy array which is returned'''
	path = getPathData(fltFil)
	return path[:8].T

	
#~ def readFpbOLD(fltFil='LastFlight.fpb'):
	#~ '''read in a Flight Path Binary file; each packed point contains:
	#~ kias, altitude, head, pitch, roll, latitude, longitude, time, runningP
	#~ collect all but runningP into a Numpy array which is returned'''
#~ #	global flt, pt
	#~ datStrct = struct.Struct('>ffffffff?')					# structure to decode flight data packet
	#~ datPktLen = struct.calcsize(datStrct.format)		# correct packet length
	#~ flt = []
	#~ with open(fltFil, 'rb') as inFil:
		#~ while True:
			#~ pt = inFil.read(datPktLen)
			#~ if pt == b'': break
			#~ flt.append(datStrct.unpack(pt)[:-1])
	#~ return flt
	
def dist(lli,llf):
	'''return the distance in latitude dgrees from lat/lon lli to lat/lon llf'''
	dLat = llf[0] - lli[0]
	dLon = (llf[1] - lli[1]) * _lat2lon			# w/ same number of degrees, longitude dist is less
	dst = math.sqrt(dLat**2 + dLon**2)
	return dst

# top level function for grading a flightpath against a set of waypoints
# given a packed binary flightpath file 
#		a sequence flight data packets of kias, altitude, head, pitch, roll, latitude, longitude, time, runningP
#		and a weighpoint file .wpts; see getWayPts
# return the total minimum distances of the path to the waypoints, the time duration of the critical portion of the path, the number of times the plane tipped, and a vector of the minimal distances to the individual waypoints

def grade(fltFil='notSet',ret=True):
	'''Given a LastFlight file, extract the MP task string, grade the LastFlight file wrt the task's waypoints returning the solution's total distance travelled, time duration, sum dists to waypts, num tips, intervals & distances by waypoints '''
#	global spds, fltPath
	if not _NUMPYP:
		print('Numpy is missing; no access to grade computation')
		return
	if fltFil == 'notSet':
		fltFil = tkf.askopenfilename(
					title='Choose a LastFlight file',
					initialdir=(_STDir),
					filetypes=[('Fligt Path file', '.pkl')] )
	tsk = fltFil.split('.')[1]
#	wpts = Utilities.getWayPts(tsk, _CCDir)
	wpts = getWayPts(tsk, _CCDir)
	fltPath = np.array(readFP(fltFil))
	wpidxs,wpdsts = dsts2wps(wpts, fltPath)				# waypt index array & waypt distance array
	totDst = 0.;					# total distance traveled
	strtIdx = wpidxs[0];		lstIdx = wpidxs[-1] + 1		# beginning & end of the solution's intervals
	spds = np.zeros(lstIdx - strtIdx+2, dtype=float)
	for i in range(strtIdx, lstIdx):
		dst = dist(fltPath[i, 5:7], fltPath[i+1, 5:7]) * _deg2met
		spds[i-strtIdx] = dst / (fltPath[i+1, 7] - fltPath[i, 7])
		totDst += dst
#	print('speed', spds[20:].min(), spds.max(), spds.mean(), spds.var())
	wptErrs = wpdsts.sum()
	spdVar = spds.var()
	dur = fltPath[lstIdx, -1] - fltPath[strtIdx, -1]				# time end of last inteval less start of first
	durMin = dur / 60.
	score = wptErrs + spdVar + durMin
	fltPitRol = np.abs(fltPath[strtIdx : lstIdx, 3 : 5])		# from flight path get abs pitch & roll
	tipd = np.logical_and(fltPitRol[:, 0] > 5., fltPitRol[:,1] > 5.).sum()	# Number pitch/roll > 5 deg.
	if tipd > 0: score += 5.
	print('Taxiing score, interval {:} to {:}: {:.3f}'.format(strtIdx, lstIdx, score))
	if ret: return score, wptErrs, spdVar, durMin, tipd, totDst, wpidxs, wpdsts

def dsts2wps(wps,fltPath):
	'''return two arrays: 1) for each waypoint, the low-index of the closest interval, 2) the distance to that waypoint'''
	wptIdxs = []
	wptDsts = []
	for wp in wps:
		idx,dst = minDist2Fp(wp, fltPath)
		wptIdxs.append(idx)
		wptDsts.append(dst)
#		wptDsts.append(minDist2Fp(wp, fltPath))
	return np.array(wptIdxs), np.array(wptDsts)
	
def minDist2Fp(wp, fp):
	'''return the left index of the minimum distance segment in FlightPath fp to waypoint wp and its distance'''
	nwp = np.array(wp[:2])
	bst = pt2lne(fp[0,5:7], fp[1,5:7], nwp) * _deg2met
	bstIdx = 0
	for i in range(1, fp.shape[0] - 1):		# consider each remaining segment
		dst = pt2lne(fp[i,5:7], fp[i+1,5:7], nwp) * _deg2met
		if dst < bst:
			bst = dst
			bstIdx = i
	print(' >>>', bstIdx, bst)
	return bstIdx, bst

def pt2lne(pt0,pt1,pt2):
	'''compute the Euclidean distance from (y2, x2) point pt2 to the line segment between points pt0 and pt1'''
	global a2, a0, a1, v01, u01, v02, d2s, e02, v12, e12, minDirect, proj02on01, d2lne
	a0 = np.array(pt0);		a1 = np.array(pt1);		a2 = np.array(pt2)
	v02 = a2 - a0
	e02 = v02.dot(v02)				# squared distance from line pt0 to pt2
	v12 = a2 - a1
	e12 = v12.dot(v12)				#			and from line pt1 to pt2
	minDirect = np.sqrt(min(e02, e12))		# min dist pt2 to a seg end point
	v01 = a1 - a0
	e01 = v01.dot(v01)
	if e01 < _eps: return minDirect			# very short segment is virtually a single point
	d01 = np.sqrt(e01)
	u01 = v01 / d01					# unit vec along line segment from pt0 to pt1
	proj02on01 = u01.dot(v02)
	if proj02on01 < 0. or proj02on01 > d01:	
		return minDirect				# point projects outside of segment
	e2lne = e02 - proj02on01 * proj02on01	# inside seg so use projected dist
	if abs(e2lne) < 1e-10: return 0.0
	return np.sqrt(e2lne)
