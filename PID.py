import imp, sys
from math import fabs

class PID():
    integral = 0
    prev_err = 0
    prev_time = 0
    
    def __init__(sf, Kp, Ki, Kd):
        sf.Kp = Kp
        sf.Ki = Ki
        sf.Kd = Kd
        sf.prev_time = 0
        sf.prev_err = 0
        sf.integral = 0
    def compute_pid(sf, err, time, isHead):
        if time != sf.prev_time:
            if isHead is True:
                #normalize the heading difference so we know which direction to turn
                if(err > 0) and (err <= 180):
                    err = err/180.0
                elif (err > 0) and (err > 180):
                    err = (-1.0) * (360.0 - err) / 180.0
                elif (err < 0) and (err >= -180):
                    err = err/180.0
                else:
                    err = (360.0 + err) / 180.0
            
            sf.integral = sf.integral + (time - sf.prev_time) * err
            deriv = float(err - sf.prev_err)/float(time - sf.prev_time)
            sf.prev_err = err
            sf.prev_time = time
            print("P is " + str(sf.Kp * err))
            print("I is " + str(sf.Ki * sf.integral))
            print("D is " + str(sf.Kd * deriv))
            return sf.Kp * err + sf.Ki * sf.integral + sf.Kd * deriv
    
    def clear_integral(sf):
        sf.integral = 0


