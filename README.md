# cs498_MP2 Feedback：

#About the fact that no code change or complete test log were uploaded:
Sorry about that, this testing is so addictive therefore I just realize that I should record all the testing result when I am writing this. I will do this when testing again tomorrow. And for the code, I chose not to upload my file since I only mess up with numbers without hurting the structure. And I really can't help much in coding.

#After testing for like 100 times with kind of random paras, here are what I noticed:

Something wrong with the close-enough function. waypoint 2-5 result in a big misdisplacement in lower speed. 

It's better in higher speed maybe because of the inertia. 

Don't know the math, but I change the parameter 0.794 to 1 or 0.5, and it does not affect the result much.


throttle speed higher than 0.4 + PID heading involving = tip

Between waypoint3 and waypoint4 there is an 180 degree turn, speed higher than 0.4 will probably tip. 

tip will raise the score by 5. So either no tip at all or just let it go.


(these assumption might be wrong since it's not a systematic test)

P: Kp value change will result in the how big the heading change, it's not sensitive enough to readjust the angle under 5, the error is too big to turn stably when it's bigger than around 18? I keep it under 10 for most time.

I: smaller Ki value can reduce the tendency of tail swinging when the plane going straight, bigger Ki value can help the plane stay straight but since we are turning a lot in this mp, I don't think we need to be that stable.

D: this may speed up the turing? I don't see big difference. I set it to 0 or 1 for most times.

#Attached with One of the test result run under fCmd.throttle = 0.6  sf.Head_PID = PID.PID(8,0.1,1)

Now going to waypoint1
Now going to waypoint2
Now going to waypoint3
Points lost for tipping; -6.4 degrees at 29.0 seconds
Points lost for tipping; -9.5 degrees at 29.2 seconds
Points lost for tipping; -14.0 degrees at 29.4 seconds
Points lost for tipping; -20.0 degrees at 29.6 seconds
Points lost for tipping; -12.7 degrees at 29.8 seconds
Points lost for tipping; -6.3 degrees at 30.0 seconds
Points lost for tipping; 6.4 degrees at 30.6 seconds
Points lost for tipping; 9.4 degrees at 30.8 seconds
Points lost for tipping; 13.6 degrees at 31.0 seconds
Points lost for tipping; 18.2 degrees at 31.2 seconds
Points lost for tipping; 22.0 degrees at 31.4 seconds
Points lost for tipping; 14.8 degrees at 31.6 seconds
Points lost for tipping; 9.5 degrees at 31.8 seconds
Points lost for tipping; -5.7 degrees at 35.0 seconds
Points lost for tipping; -7.5 degrees at 35.2 seconds
Points lost for tipping; -9.9 degrees at 35.4 seconds
Points lost for tipping; -13.0 degrees at 35.6 seconds
Points lost for tipping; -16.9 degrees at 35.8 seconds
Points lost for tipping; -21.5 degrees at 36.0 seconds
Points lost for tipping; -14.2 degrees at 36.2 seconds
Points lost for tipping; -13.1 degrees at 36.4 seconds
Points lost for tipping; -13.5 degrees at 36.6 seconds
Points lost for tipping; -13.3 degrees at 36.8 seconds
Points lost for tipping; -12.2 degrees at 37.0 seconds
Points lost for tipping; -10.1 degrees at 37.2 seconds
Now going to waypoint4
Points lost for tipping; -6.7 degrees at 37.4 seconds
Now going to waypoint5
Points lost for tipping; 5.5 degrees at 54.6 seconds
Points lost for tipping; 5.5 degrees at 54.6 seconds
Now going to waypoint6
Points lost for tipping; 6.0 degrees at 61.4 seconds
Points lost for tipping; 7.4 degrees at 61.6 seconds
Points lost for tipping; 9.6 degrees at 61.8 seconds
Points lost for tipping; 13.0 degrees at 62.0 seconds
Points lost for tipping; 18.1 degrees at 62.2 seconds
Points lost for tipping; 17.6 degrees at 62.4 seconds
Points lost for tipping; 7.0 degrees at 62.6 seconds
Finished all waypoints
Quit
finished writing points to LastFlight.MP2.pkl
D:\Download\CS 498\ClassCode/MP2.wpts
(Latitude, Longitude, Heading) waypoints for HW2 Figure 8:  7 pts
 >>> 22 1.4504144465
 >>> 79 17.9736534237
 >>> 143 8.23654654217
 >>> 202 11.6952389329
 >>> 233 13.0210301306
 >>> 304 0.0
 >>> 41 11.5581659244
Taxiing score, interval 22 to 42: 66.312
>>>

