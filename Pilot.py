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
    
    def __init__(sf,tsk='MP2',rc=True,gui=True):
        super().__init__(tsk, rc, gui)
        sf.strtTime = None
        sf.duration = None
        sf.wpts = sf.getWayPts(tsk);
        sf.Head_PID = PID.PID(13,0.1,6)
        sf.Throttle_PID = PID.PID(0.12,0,0)
        sf.target_speed = 10.0 
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
        if distance < 0.000000024:
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
        #Compute how much we want to move the rudder
        #TODO Make this a seperate function
        heading_t=sf.computeTargetHeading(fDat)
        err = heading_t - fDat.head
        computed = (sf.Head_PID).compute_pid(err,sf.duration,True)
        print("computer number is " + str(computed));
        print("target heading is " + str(heading_t))
        print("current heading is " + str(fDat.head))
        if computed is not None: 
            fCmd.rudder = computed
        fCmd.throttle = 0.45
        if(sf.closeEnough(fDat)):
            sf.currentWpt = sf.currentWpt + 1
            if sf.currentWpt >= len(sf.wpts):
                print("Finished all waypoints")
                return 'stop'
            else:
                (sf.Head_PID).clear_integral
                (sf.Throttle_PID).clear_integral
                print("Now going to waypoint" + str(sf.currentWpt))
        
        #Compute how much we want to move the throttle
        #TODO Make this a seperate function
        speed = (sf.Throttle_PID).compute_speed(fDat, sf.duration)
        err = sf.target_speed - speed
        throttle_temp = (sf.Throttle_PID).compute_pid(err,sf.duration,False)

        print("Current throttle is " + str(throttle_temp))
        if throttle_temp is not None:
            fCmd.throttle = throttle_temp
        if sf.duration > 300:
            return 'stop'
		
