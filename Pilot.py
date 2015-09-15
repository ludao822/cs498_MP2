# Simple example of taxiing as scripted behavior
# import Pilot; a=Pilot.Pilot(); a.start()
#!/usr/bin/python -tt

import ClassCode.Ckpt as Ckpt
import PID as PID

import imp, sys
from math import pi,atan2

def rel():
	imp.reload(sys.modules['Pilot'])

class Pilot (Ckpt.Ckpt):			# subclass of the class Ckpt in the file Ckpt
    currentWpt = 0

    def __init__(sf,tsk='MP2',rc=True,gui=False):
        super().__init__(tsk, rc, gui)
        sf.strtTime = None
        sf.duration = None
        sf.wpts = sf.getWayPts(tsk);
        sf.Head_PID = PID.PID(18 ,0.2, 0.2)

    def computeTargetHeading(sf,fDat):
        ydiff = ((sf.wpts)[sf.currentWpt][0] - fDat.latitude) * 0.794
        xdiff = (sf.wpts)[sf.currentWpt][1] - fDat.longitude
        radian = atan2(ydiff*1000,xdiff*1000);
        if(radian >= 0) and (radian < pi/2):
            radian_h = pi/2 - radian
        elif radian >= pi/2:
            radian_h = 2 * pi - (radian - pi/2)
        else:
            radian_h = pi/2 - radian
        radian_h = radian_h / (2*pi) * 360
            
        return radian_h	

    def closeEnough(sf,fDat):
        ydiff = ((sf.wpts)[sf.currentWpt][0] - fDat.latitude) * 0.794
        xdiff = (sf.wpts)[sf.currentWpt][1] - fDat.longitude
        distance = ydiff * ydiff + xdiff * xdiff
        print ("current distance is " + str(distance))
        if distance < 0.0000001:
            return True
        else:
            return False

    def ai(sf,fDat,fCmd):
        '''Override with the Pilot decision maker, args: fltData and cmdData from Utilities.py'''
        if not fDat.running:
            sf.strtTime = fDat.time
        sf.duration = fDat.time - sf.strtTime
        if abs(fDat.roll) > 5.:			# first check for excessive roll
            print('Points lost for tipping; {:.1f} degrees at {:.1f} seconds'.format(fDat.roll, sf.duration))
        
        heading_t=sf.computeTargetHeading(fDat)
        computed = (sf.Head_PID).compute_pid(fDat.head,heading_t,sf.duration)
        print("computer number is " + str(computed));
        print("target heading is " + str(heading_t))
        print("current heading is " + str(fDat.head))
        if computed is not None: 
            fCmd.rudder = computed
        #heading_diff = heading_t - fDat.head
        fCmd.throttle = 0.4
        '''
        if heading_diff == 0:
            fCmd.rudder = 0
        elif(heading_diff > 0) and (heading_diff < 180):
            fCmd.rudder = 0.3
        elif(heading_diff > 0) and (heading_diff > 180):
            fCmd.rudder = -0.3
        elif(heading_diff < 0) and (heading_diff > -180):
            fCmd.rudder = -0.3
        else:
            fCmd.rudder = 0.3
        '''
        if(sf.closeEnough(fDat)):
            sf.currentWpt = sf.currentWpt + 1
            if sf.currentWpt >= len(sf.wpts):
                print("Finished all waypoints")
                return 'stop'
            else:
                (sf.Head_PID).clear_integral
                print("Now going to waypoint" + str(sf.currentWpt))
        #elif sf.duration < 40.:		# coast until 40 seconds then exit
        #    fCmd.throttle = 0.7
        #    fCmd.rudder = 0.1
        if sf.duration > 300:
            return 'stop'
		
