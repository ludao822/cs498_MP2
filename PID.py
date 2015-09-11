import imp, sys

class PID():
    integral = 0
    prev_err = 0
    prev_time = 0
    def __init__(sf, Kp, Ki, Kd):
        sf.Kp = Kp
        sf.Ki = Ki
        sf.Kd = Kd

    def compute_pid(sf, curr, target, time):
        if time != prev_time:
            integral = integral + (time - prev_time) * err
            deriv = (err - prev_err)/(time - prev_time)
            sf.prev_err = err
            sf.prev_time = time
            return sf.Kp * err + sf.Ki * sf.integral + sf.Kd * deriv



