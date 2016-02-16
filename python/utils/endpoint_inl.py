# -*- coding: utf-8 -*-
"""
Created on Wed Feb 03 10:10:18 2016

@author: mark_t
"""



def endpoint_inl(data):
    import numpy as np
    length = len(data)
    inldata = np.ndarray(length, dtype=float)
    xmax = len(data) -1
#    data -= np.average(data)
    slope = (data[xmax] - data[0]) / (xmax - 0.0)# Rise over run
    intercept = data[xmax] - (slope * xmax)

    for i in range(0, len(data)):
        inldata[i] = (data[i] - (slope * i) - intercept)
    return inldata
    
if __name__ == "__main__": 

    import numpy as np
    from matplotlib import pyplot as plt

    # Keep track of start time
#    start_time = time.time()

    curve = np.ndarray(200, dtype=float)
    
    a = np.random.uniform(-2, 2)
    b = np.random.uniform(-100, 100)
    c = np.random.uniform(-50, 50)    
    
    for point in range(-100, 100):
        floatpoint = float(point) / 10.0

        curve[point + 100] = (a*floatpoint**2.0) + b*floatpoint -c
        np.random.uniform(-5, 5)
    inlcurve = endpoint_inl(curve)
        
    plt.figure(1)
    plt.plot(curve)
    plt.plot(inlcurve)
    plt.show()
        
        