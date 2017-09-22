import os, subprocess

##
## BEGIN FUNCTIONS
##

def writeTAPE5lnfl(runDir,wn1,wn2):

    if not os.path.exists(runDir):
        os.makedirs(runDir)
    if not os.path.exists(runDir+'/TAPE5_lnfl'):
        subprocess.call(["touch",'TAPE5_lnfl'],cwd=runDir)
    txt = open(runDir+'/'+"TAPE5_lnfl","w")

    #          maunakea  sofia
    # height    4.205    12.2
    txt.write('\
$ f100 format\n'+
('%10s'%wn1)+('%10s'%wn2)+'\n\
11111111111111111111111111111111111111111111111    LNOUT EXBRD\n\
%%%%%%%%%%%%%%%%%%\n\
12345678901234567890123456789012345678901234567890123456789012345678901234567890') 
    txt.close()

    return 0

###
### END FUNCTIONS
###
