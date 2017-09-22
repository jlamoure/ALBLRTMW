import os, tarfile, shutil, time, sys, subprocess


def unpack(tarDir, sourceDir):
    # check that we have all tars
    # the two tars in tarDir: one for LNFL+LBLRTM programs and the other for the Line Parameter Database.
    tar1found = False
    tar2found = False
    for f in os.listdir(tarDir):
        if os.path.isfile(os.path.join(tarDir,f)):
            # assume this file is LBLRTM and LNFL
            if ((f.find("lblrtm_v") != -1) and (f.find("lnfl_v") != -1) and (f.find(".tar.gz") != -1)): 
                lblrtmlnfl = f
                print("found LBLRTM and LNFL "+f)
                tar1found = True
            # assume this file is the Parameter Database
            if ((f.find("aer_v") != -1) and (f.find(".tar.gz") != -1)): 
                lnfldb = f
                print("found Line Parameter Database "+f)
                tar2found = True
    if not (tar1found and tar2found):
        print(" tars are missing or have been renamed")

    # make sourceDir an actual directory or wipe it
    if not os.path.exists(sourceDir):
        print("creating directory "+sourceDir+" for install")
        os.makedirs(sourceDir)
    else:
        print("overwriting directory "+sourceDir+" for install")
        shutil.rmtree(sourceDir)
        os.makedirs(sourceDir)
    
    # completely extract all tars from tarDir into sourceDir
    tar1 = tarfile.open(os.path.join(tarDir,lblrtmlnfl), 'r')
    tar2 = tarfile.open(os.path.join(tarDir,lnfldb), 'r')
    print("extracting LNFL+LBLRTM "+tarDir+lblrtmlnfl)
    for item1 in tar1:
        tar1.extract(item1, sourceDir)
    print("extracting LPD "+tarDir+lnfldb)
    for item2 in tar2:
        tar2.extract(item2, sourceDir)
    tar1.close()
    tar2.close()
    # LNFL and LBLRTM are also compressed individually
    for item3 in os.listdir(sourceDir):
        if (item3.find(".tar.gz") != -1):
            if (item3.find("lblrtm") != -1):
                print("extracting LBLRTM "+sourceDir+item3)
                tar3 = tarfile.open(os.path.join(sourceDir,item3), 'r')
                for item4 in tar3:
                    tar3.extract(item4, sourceDir)
                tar3.close()
                os.remove(sourceDir+item3) # delete LBLRTM tar
            if (item3.find("lnfl") != -1):
                # the LNFL comes packaged without a containing folder -> make one
                os.makedirs(sourceDir+"lnfl/")
                print("extracting LNFL "+sourceDir+item3)
                tar3 = tarfile.open(os.path.join(sourceDir,item3), 'r')
                for item4 in tar3:
                    tar3.extract(item4,sourceDir+"lnfl/")
                tar3.close()
                os.remove(sourceDir+item3) # delete LNFL tar
    print("AER LNFL+LBLRTM+PDB extraction to build directory complete")

# getCompilerString() outputs the target name appropriate for your compiler
# - directly copied from the K. Gullikson's Telluric Fitter
# - the code: https://github.com/kgullikson88/Telluric-Fitter/blob/master/setup.py
# - the paper: http://adsabs.harvard.edu/abs/2014AJ....148...53G
def getCompilerString():
    """
    The following function determines what the operating system is,
      and which fortran compiler to use for compiling lnfl and lblrtm.
      It returns the string that the makefiles for lnfl and lblrtm
      need.
      NOTE: This should all work for linux or Mac OSX, but NOT Windows!!
    """
    #First, get the operating system
    p = sys.platform
    if "linux" in p:
        output = "linux"
    elif "darwin" in p:
        output = "osx"
    else:
        raise OSError("Unrecognized operating system: %s" % p)

    #Next, find the fortran compiler to use
    compilers = ["ifort",
                 "gfortran",
                 "g95"]
    comp_strs = ["INTEL",
                 "GNU",
                 "G95"]
    found = False
    for i in range(len(compilers)):
        compiler = compilers[i]
        try:
            subprocess.check_call([compiler, '--help'], stdout=open("/dev/null"))
            found = True
        except OSError:
            found = False
        if found:
            break
    if not found:
        raise OSError("Suitable compiler not found!")
    else:
        output = output + comp_strs[i] + "sgl"
    print("FORTRAN compiler target: "+output)
    return output

def compileLNFL(sourceDir,buildDir):
    if not os.path.exists(buildDir+"lnfl/"):
        print("copying LNFL source")
        shutil.copytree(sourceDir+"lnfl/",buildDir+"lnfl/",symlinks=True)
    print("compiling LNFL")
    subprocess.call(["make","-f","make_lnfl",getCompilerString()],cwd=buildDir+"lnfl/build/")

def compileLBLRTM(sourceDir,buildDir):
    if not os.path.exists(buildDir+"lblrtm/"):
        print("copying LBLRTM source")
        shutil.copytree(sourceDir+"lblrtm/",buildDir+"lblrtm/",symlinks=True)
    print("compiling LBLRTM")
    subprocess.call(["make","-f","make_lblrtm",getCompilerString()],cwd=buildDir+"lblrtm/build/")

    print("LNFL install complete")

def setupPD(sourceDir,buildDir):
    # figure out name of line parameter database folder
    aerFound = False
    for f in os.listdir(sourceDir):
        if ((f.find("aer_v") != -1) and os.path.isdir(sourceDir+f)): 
            aerFound = True
            print("assuming "+sourceDir+f+"/ is the Line Parameter Database")
            break
    if not aerFound:
        print("couldn't find Line Parameter Database in source directory! We need that")
        return
            
    # copy over the database - if buildDir==sourceDir then
    # files are already there from unpack()
    if (os.path.exists(buildDir+f+"/")):
        if (buildDir==sourceDir):
            print("source directory is also the build directory, no need to copy LPD")
        else:
            print("copying Line Parameter Database to "+buildDir+f+"/")
            shutil.rmtree(buildDir+f+"/")
            shutil.copytree(sourceDir+f+"/",buildDir+f+"/",symlinks=True)
    
    print("LPD install complete")

def setup(tarDir, sourceDir, buildDir):
    unpack(tarDir, sourceDir) # copy source from tar archives if needed
    compileLNFL(sourceDir,buildDir)
    compileLBLRTM(sourceDir,buildDir)
    setupPD(sourceDir,buildDir)

if __name__ == "__main__":

    if (len(sys.argv) == 4): # 3 args: sourceDir and buildDir are different
        tarDir = sys.argv[1]+'/'
        sourceDir = sys.argv[2]+'/'
        buildDir = sys.argv[3]+'/'
    elif (len(sys.argv) == 3):# 2 args: sourceDir and buildDir are same
        tarDir = sys.argv[1]+'/'
        sourceDir = sys.argv[2]+'/'
        buildDir = sys.argv[2]+'/'
    else:
        print("usage: python install.py AER-tars-dir source-dir build-dir, or")
        print("       python install.py AER-tars-dir source-and-build-dir")
        print("       where AER-tars-dir contains aer_lblrtm_v12.X_lnfl_v3.X.tar.gz and aer_v_3.X.tar.gz")
        print("       request AER tars from http://rtweb.aer.com/lblrtm_code.html")
        exit()

    # tarDir: unpack() will look for tars here
    # sourceDir: unpack() will extract tars here
    # buildDir: compileLBLRTM() and compileLNFL() and setupPD() will
    #           copy the files and make executables here
    setup(tarDir,sourceDir,buildDir)
