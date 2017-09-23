# included with python
import os,sys,argparse,time
# from scripts in local directory
import makeTAPE5lblrtm as lblrtm
import makeTAPE5lnfl as lnfl
import run

def feetTokm(feet):
    return (feet*12.*2.54/100.)/1000.

if __name__ == "__main__":
    global buildDir
    global runDir 
    global runName
    global startWn
    global endWn
    global angle
    global height

    # location of LBLRTM/LNFL build as installed by install.py
    buildDir = "aer/"
    # set location of model directories
    runDir = "models/"
    # set name for model (is subdirectory of runDir)
    runName = "maunakea" 
    wn1 = 580.0
    wn2 = 590.0
    angle = 66.6
    alt = 4.205
    mols = [.45,.5,1.,.4,1.,1.,.5,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.]
    
    if not os.path.exists(runDir+'/'+runName+'/'+'TAPE1'):
        # generate a TAPE5 with params for the line file program
        lnfl.writeTAPE5lnfl(runDir+runName,wn1-5.,wn2+5.)
        # using TAPE5, create a line file for the LBLRTM, link to with TAPE1
        run.createLineList(buildDir,runDir+'/'+runName+'/',runName)
    # generate a TAPE5 with params for LBLRTM
    lblrtm.writeTAPE5lblrtm("with convolution",runDir+'/'+runName+'/',wn1,wn2,angle,alt,mols, convolution=True,hwhm=.02)
    # run the LBLRTM using TAPE5
    run.runLBLRTM(buildDir,runDir+'/'+runName+'/',runName)
