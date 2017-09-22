import numpy as np
import matplotlib.pyplot as plt 
import sys
import math

def getLBLRTMoutput(filelocation):
    # Pull data from text file 1
    f = open(filelocation,'r')
    lines=f.readlines()

    # identify beginning of data in file
    i = 0
    data = []
    copy=False
    while i<len(lines):
        if ("WAVENUMBER" in lines[i]): # the data starts after this line
            xTitle = "Wavenumber"
            if ("RADIANCE" in lines[i]):
                yTitle = "Radiance"
            elif ("TRANSMISSION" in lines[i]):
                yTitle = "Transmission"
            elif ("TEMPERATURE" in lines[i]):
                yTitle = "Temperature"
            elif ("OPTICAL DEPTH" in lines[i]):
                yTitle = "Optical Depth"
            else:
                yTitle = "unknown"
            copy = True
            i+=1
        if copy:
            data.append(lines[i]) 
        i+=1

    x = []
    y = []
    for item in data: # data points are formatted x y in lines
        try: # copy lines of data
            a = float(item[5:18]) #that line's wavenumber
            b = float(item[26:41]) #the corresponding radiance value
            x.append(a)
            y.append(b)
        except ValueError: # some lines are blank
            pass

    return x, y, xTitle, yTitle

def files(fileNames):
    i = 0
    color = ['r','g','b','y','m']
    for f in fileNames:
        if ("TAPE30" in f) or ("TAPE29" in f) or ("TAPE28" in f) or ("TAPE27" in f):
            x, y, xTitle, yTitle = getLBLRTMoutput(f)
        else:
            x, y = np.loadtxt(f, unpack=True)
            xTitle = 'x'
            yTitle = 'y'
        plt.plot(x, y, color[i], linewidth=0.9)
        i+=1
    plt.xlim(x[0],x[-1])
    plt.xlabel(xTitle)
    plt.ylabel(yTitle)
    plt.legend(tuple(fileNames),fontsize=9)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":

    if (len(sys.argv) == 7):
        files([ sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6] ])
    if (len(sys.argv) == 6):
        files([ sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5] ])
    elif (len(sys.argv) == 5):
        files([ sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4] ])
    elif (len(sys.argv) == 4):
        files([ sys.argv[1],sys.argv[2],sys.argv[3] ])
    elif (len(sys.argv) == 3):
        files([ sys.argv[1],sys.argv[2] ])
    else:
        files([ sys.argv[1] ])

