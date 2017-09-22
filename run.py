import os, subprocess, shutil, sys
import plot # this is plot.py
import argparse

def fixLineListLinks(buildDir,runDir):
    # find location of line file in line parameter database
    lnflFound = False
    for f in os.listdir(buildDir):
        if (f.find("aer_v") != -1): 
            lnflFound = True
            break
    if not lnflFound:
        print("couldn't find Line Parameter Database!")
        return
    lineFile = f+"/"

    print("fixing links to line parameter database files...")
    for f in ["co2_co2_brd_param","co2_h2o_brd_param","o2_h2o_brd_param","wv_co2_brd_param"]:
        link = os.path.relpath(buildDir+lineFile+"extra_brd_params/"+f,start=runDir)
        if os.path.lexists(runDir+f):
            os.remove(runDir+f)
        os.symlink(link,runDir+f)
    link = os.path.relpath(buildDir+lineFile+"spd_dep/"+"spd_dep_param",start=runDir)
    if os.path.lexists(runDir+"spd_dep_param"):
        os.remove(runDir+"spd_dep_param")
    os.symlink(link,runDir+"spd_dep_param")

def createLineList(buildDir,runDir,runName):
    print("creating line list...")

    # clear TAPE files from runDir
    for TAPE in ["TAPE1","TAPE2","TAPE3","TAPE5","TAPE6","TAPE10"]:
        if os.path.lexists(runDir+TAPE):
            print("clearing "+runDir+TAPE)
            os.remove(runDir+TAPE)
    
    # Set up link to AER line file (e.g. aer_v_3.5) that comes in the AER line parameter database

    # find location of line file in line parameter database
    lnflFound = False
    for f in os.listdir(buildDir):
        if (f.find("aer_v") != -1): 
            lnflFound = True
            print("assuming "+buildDir+f+"/line_file/"+f+"/ is the line file")
            break
    if not lnflFound:
        print("couldn't find line file in Line Parameter Database!")
        return
    lineFile = buildDir+f+"/line_file/"+f

    # find location of LNFL executable
    execFound = False
    for f in os.listdir(buildDir+"lnfl/"):
        if ((f.find("lnfl_v") != -1) and (f.find("sgl") != -1) and (f[0] != '.')): 
            execFound = True
            print("assuming "+buildDir+"lnfl/"+f+" is the LNFL executable")
            break
    if not execFound:
        print("couldn't find Line file in Line Parameter Database!")
        return
    lnflExecutable = buildDir+"lnfl/"+f
    lnflExecutableLink = os.path.relpath(buildDir+"lnfl/"+f, start=runDir)

    # symlink TAPE1
    lineFileLink = os.path.relpath(lineFile,start=runDir)
    print(lnflExecutableLink)
    print(lineFileLink)
    print(runDir)
    print(runDir+"TAPE1")
    os.symlink(lineFileLink,'./'+runDir+"TAPE1")
    # symlink TAPE5
    TAPE5Found = False
    for f in os.listdir(runDir):
        if ( (f.find("lnfl") != -1) and (f.find("TAPE5") != -1) ):
            TAPE5Name = f
            TAPE5Found = True
            break
    if not TAPE5Found:
        print("could not find a TAPE5 with \'lnfl\' in filename")
        exit()
    TAPE5Link = os.path.relpath(runDir+TAPE5Name,start=runDir)
    os.symlink(TAPE5Link,'./'+runDir+"TAPE5")
    # fix links to Line Parameter Database files
    fixLineListLinks(buildDir,runDir)

    # generate line list
    print("generating line list")
    subprocess.call([lnflExecutableLink,"TAPE1"], cwd=runDir)

    # save the output TAPEs with runName
    for TAPE in ["TAPE3","TAPE6","TAPE7"]:
        if os.path.exists(runDir+TAPE):
            print("saving "+TAPE+" as "+runDir+TAPE+"_"+runName)
            shutil.move(runDir+TAPE, runDir+TAPE+"_"+runName)


def runLBLRTM(buildDir,runDir,runName):

    #set runtype = "lblrtm_7-8um_41000ft_030515UTC15_lat50_elev23_zenh2o7p3um_transm"
    
    # clear TAPE files from runDir
    for TAPE in ["TAPE3","TAPE5","TAPE6","TAPE7","TAPE9","TAPE10","TAPE11","TAPE12","TAPE27","TAPE28","TAPE29","TAPE30"]:
        if os.path.lexists(runDir+TAPE):
            print("clearing "+runDir+TAPE)
            os.remove(runDir+TAPE)

    # find location of LBLRTM executable
    execFound = False
    for f in os.listdir(buildDir+"lblrtm/"):
        if ((f.find("lblrtm_v") != -1) and (f.find("sgl") != -1)): 
            execFound = True
            print("assuming "+buildDir+"lblrtm/"+f+" is the LBLRTM executable")
            break
    if not execFound:
        print("couldn't find LBLRTM executable")
        return
    lblrtmExecutable = buildDir+"lblrtm/"+f
    lblrtmExecutableLink = os.path.relpath(buildDir+"lblrtm/"+f, start=runDir)
    
    # symlink TAPE3
    TAPE3Link = os.path.relpath(runDir+"TAPE3_"+runName,start=runDir)
    os.symlink(TAPE3Link,runDir+"TAPE3")
    # symlink TAPE5
    for f in os.listdir(runDir):
        if ( (f.find("lblrtm") != -1) and (f.find("TAPE5") != -1) and (f[0] != '.')):
            print("assuming lblrtm's TAPE5 is "+runDir+f)
            TAPE5Name = f
            TAPE5Found = True
            break
    if not TAPE5Found:
        print("could not find a TAPE5 with \'lblrtm\' in filename")
        return
    os.symlink(f,runDir+"TAPE5")

    # run LBLRTM
    print("creating transmission spectrum...")
    subprocess.call([lblrtmExecutableLink], cwd=runDir)

    # save the output TAPEs with runName
    for TAPE in ["TAPE6","TAPE7","TAPE9","TAPE10","TAPE11","TAPE12","TAPE27","TAPE28","TAPE29","TAPE30"]:
        if os.path.exists(runDir+TAPE):
            print("saving "+TAPE+" as "+runDir+TAPE+"_"+runName)
            shutil.move(runDir+TAPE, runDir+TAPE+"_"+runName)

if __name__ == "__main__":
    
    # optional argument behavior (dir required):
    #     none: runs LNFL and LBLRTM
    #   --lnfl: runs LNFL only
    # --lblrtm: runs LBLRTM only
    parser = argparse.ArgumentParser(description='parse command flags')
    parser.add_argument('--lblrtm', dest='lblrtm', help="run only LBLRTM to produce model", action='store_true')
    parser.add_argument('--lnfl', dest='lnfl', help="run only LNFL to produce linefile for LBLRTM", action='store_true')
    parser.add_argument("buildDir", type=str, help="LBLRTM build location")
    parser.add_argument("modelDir", type=str, help="LBLRTM model directory containing TAPEs")
    parser.set_defaults(lblrtm=False)
    parser.set_defaults(lnfl=False)
    args = parser.parse_args()
    if (args.modelDir[-1] == "/"): # strip trailing / on directory if exists
        runDir,runName = os.path.split(args.modelDir[:-1])
    else:
        runDir,runName = os.path.split(args.modelDir)
    print('assuming TAPEs will be in '+runDir+'/'+runName+'/')
    buildDir = args.buildDir

    if args.lnfl and not args.lblrtm:
        createLineList(buildDir,'./'+runDir+'/'+runName+'/',runName)
    elif args.lblrtm and not args.lnfl:
        runLBLRTM(buildDir,'./'+runDir+'/'+runName+'/',runName)
    else:
        createLineList(buildDir,runDir+'/'+runName+'/',runName)
        runLBLRTM(buildDir,'./'+runDir+'/'+runName+'/',runName)
        
