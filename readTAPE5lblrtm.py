#
# run as: python readTAPE5lblrtm.py ./path/to/TAPE5
#

##
## TODO
##
#   currently have to cut whitespace from string records, this is bad because it makes records like JCHAR in record 3.5 useless.

import sys, re, math

# defines the structure which stores the information needed to retrieve the records from an LBLRTM TAPE3 file
class Record:
    name = "" # the name of the record
    entryNames = [] # what each entry in the line is called
    start = [] # entries start at these columns
    end = []   # entries stop at these columns
    isString = [] # whether that entry is a string or a value
    entries = dict() # entry information here after TAPE3 has been read

#
# populate information needed to find each record in the TAPE3 file
# record documentation is in your local installation:
# $LBLRTM_DIR/aer_lblrtm_vXX.X_lnfl_vX.X/lblrtm/docs/html/lblrtm_instructions.html
#

R12 = Record()
R12.name = "1.2"
R12.entryNames = ["IHIRAC","ILBLF4","ICNTNM","IAERSL","IEMIT","ISCAN","IFILTR","IPLOT","ITEST","IATM","IMRG","ILAS","IOD","IXSECT","MPTS","NPTS","ISOTPL","IBRD"]
R12.start = [5,10,15,20,25,30,35,40,45,50,55,60,65,70,72,77,81,86]
R12.end = [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90]
R12.isString = [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]

R13 = Record()
R13.name = "1.3"
R13.entryNames = ["V1","V2","SAMPLE","DVSET","ALFAL0","AVMASS","DPTMIN","DPTFAC","ILNFLG","DVOUT","NMOL_SCAL"]
R13.start = [1,11,21,31,41,51,61,71,85,90,105]
R13.end = [10,20,30,40,50,60,70,80,85,100,105]
R13.isString = [False,False,False,False,False,False,False,False,False,False,False]

R14 = Record()
R14.name = "1.4"
R14.entryNames = ["TBOUND","SREMIS1","SREMIS2","SREMIS3","SRREFL1","SRREFL2","SRREFL3","surf_refl"]
R14.start = [1,11,21,31,41,51,61,71]
R14.end = [10,20,30,40,50,60,70,75]
R14.isString = [False,False,False,False,False,False,False,True]

# TODO implement record 1.6a

R21 = Record()
R21.name = "2.1"
R21.recordNames = ["IFORM","NLAYRS","NMOL","SECNTO","ZH1","ZH2","ZANGLE"]
R21.start = [0,3,6,11,41,53,66]
R21.end = [2,5,10,20,48,60,73]
R21.isString = [False,False,False,False,False,False,False]

R2d1d1 = Record()
R2d1d1.name = "2.1.1"
R2d1d1.entryNames = ['PAVE','TAVE','SECNTK','ITYL','IPATH','ALTZ','PZ','TZ','ATLZ','PZ','TZ']
R2d1d1.start = [1,11,21,31,34,37,44,52,59,66,74]
R2d1d1.end = [10,20,30,33,35,43,51,58,65,73,80]
R2d1d1.isString = [False,False,False,False,False,False,False,False,False,False,False]

# TODO implement records 2.1.2 - 2.3.4

R31 = Record()
R31.name = "3.1"
R31.entryNames = ["MODEL","ITYPE","IBMAX","ZERO","NOPRNT","NMOL","IPUNCH","IFXTYP","MUNITS","RE","HSPACE","VBAR","REF_LAT"]
R31.start = [1,6,11,16,21,26,31,36,39,41,51,61,81]
R31.end = [5,10,15,20,25,30,35,37,40,50,60,70,90]
R31.isString = [False,False,False,False,False,False,False,False,False,False,False,False,False]

R32 = Record()
R32.name = "3.2"
R32.entryNames = ["H1","H2","ANGLE","RANGE","BETA","LEN","HOBS"]
R32.start = [1,11,21,31,41,51,61]
R32.end = [10,20,30,40,50,55,70]
R32.isString = [False,False,False,False,False,False,False]

R33a = Record()
R33a.name = "3.3a"
R33a.entryNames = ["AVTRAT","TDIFF1","TDIFF2","ALTD1","ALTD2"]
R33a.start = [1,11,21,31,41]
R33a.end = [10,20,30,40,50]
R33a.isString = [False,False,False,False,False]

# there are abs(IBMAX) number of layers in user atmosphere profile,
# this record has two possibilities:
# IBMAX is nonzero positive: layer boundary altitudes
R33b1 = Record()
R33b1.name = '3.3b'
R33b1.entryNames = ['ZBND(1)','ZBND(2)','ZBND(3)','ZBND(4)','ZBND(5)','ZBND(6)','ZBND(7)','ZBND(8)']
R33b1.start = [1,11,21,31,41,51,61,71]
R33b1.end = [10,20,30,40,50,60,70,80] # documentation unclear
R33b1.isString = [False,False,False,False,False,False,False,False]
# IBMAX is nonzero negative: layer boundary pressures
R33b2 = Record()
R33b2.name = '3.3b'
R33b2.entryNames = ['PBND(1)','PBND(2)','PBND(3)','PBND(4)','PBND(5)','PBND(6)','PBND(7)','PBND(8)']
R33b2.start = [1,11,21,31,41,51,61,71]
R33b2.end = [10,20,30,40,50,60,70,80] # documentation unclear
R33b2.isString = [False,False,False,False,False,False,False,False]

R34 = Record()
R34.name = "3.4"
R34.entryNames = ["IMMAX","HMOD"]
R34.start = [1,6]
R34.end = [5,29]
R34.isString = [False,True]

R35 = Record()
R35.name = "3.5"
R35.entryNames = ["ZM","PM","TM","JCHARP","JCHART","JLONG","JCHAR(M)"]
R35.start = [1,11,21,31,37,38,41]
R35.end = [10,20,30,36,37,39,80]
R35.isString = [False,False,False,True,True,True,True]

R36n = Record()
R36n.name = '3.6n'
R36n.entryNames = ['VMOL(1)','VMOL(2)','VMOL(3)','VMOL(4)','VMOL(5)','VMOL(6)','VMOL(7)','VMOL(8)']
R36n.start = [1,16,31,46,61,76,91,106]
R36n.end = [15,30,45,60,75,90,105,120] # documentation unclear
R36n.isString = [False,False,False,False,False,False,False,False]

R37 = Record()
R37.name = "3.7"
R37.entryNames = ["IXMOLS","IPRFL","IXSBIN"]
R37.start = [1,6,11]
R37.end = [5,10,15]
R37.isString = [False,False,False]

R371 = Record()
R371.name = '3.7.1'
R371.entryNames = ['XSNAME(1)','XSNAME(2)','XSNAME(3)','XSNAME(4)','XSNAME(5)','XSNAME(6)','XSNAME(7)','XSNAME(8)']
R371.start = [1,11,21,31,41,51,61,71]
R371.end = [10,20,30,40,50,60,70,80]
R371.isString = [True,True,True,True,True,True,True,True]

R38 = Record()
R38.name = "3.8"
R38.entryNames = ["LAYX","IZORP","XTITLE"]
R38.start = [1,6,11]
R38.end = [5,10,60]
R38.isString = [False,False,True]

R381 = Record()
R381.name = "3.8.1"
R381.entryNames = ["ZORP","JCHAR(K)"]
R381.start = [1,16]
R381.end = [10,50]
R381.isString = [False,True]

R38n = Record()
R38n.name = '3.8.n'
R38n.entryNames = ['DENX(1)','DENX(2)','DENX(3)','DENX(4)','DENX(5)','DENX(6)','DENX(7)','DENX(8)']
R38n.start = [1,11,21,31,41,51,61,71]
R38n.end = [10,20,30,40,50,60,70,80]
R38n.isString = [True,True,True,True,True,True,True,True]

R81 = Record()
R81.name = "8.1"
R81.entryNames = ["HWHM","V1","V2","JEMIT","JFN","JVAR","SAMPL","IUNIT","IFILST","NIFILS","JUNIT","NPTS","param"]
R81.start = [1,11,21,34,39,44,46,59,64,69,74,76,81]
R81.end = [10,20,30,35,40,45,55,60,65,70,75,80,90]
R81.isString = [False,False,False,False,False,False,False,False,False,False,False,False,True]

R91 = Record()
R91.name = "9.1"
R91.entryNames = ["DVO","V1","V2","JEMIT","I4PT","IUNIT","IFILST","NIFILS","JUNIT","NPTS"]
R91.start = [1,11,21,31,36,56,61,66,71,76]
R91.end = [10,20,30,35,40,60,65,70,75,80]
R91.isString = [False,False,False,False,False,False,False,False,False,False]

R101 = Record()
R101.name = "10.1"
R101.entryNames = ["HWHM","V1","V2","JEMIT","JFNin","MRATin","DVOUT","IUNIT","IFILST","NIFILS","JUNIT","IVX","NOFIX"]
R101.start = [1,11,21,31,36,41,46,56,61,66,71,76,79]
R101.end = [10,20,30,35,40,45,55,60,65,70,75,78,80]
R101.isString = [False,False,False,False,False,False,False,False,False,False,False,False,True]

R12d1 = Record()
R12d1.name = "12.1"
R12d1.entryNames = ['CPRGID','CEX']
R12d1.start = [1,79]
R12d1.end = [60,80]
R12d1.isString = [True,True]
        
R12d2a = Record()
R12d2a.name = '12.2a'
R12d2a.entryNames = ['V1','V2','XSIZE','DELV','NUMSBX','NOENDX','LFILE','LSKIPF','SCALE','IOPT','I4P','IXDEC']
R12d2a.start = [1,11,21,31,41,46,51,56,61,71,73,76]
R12d2a.end = [10,20,30,40,45,50,55,60,70,72,75,80]
R12d2a.isString = [False,False,False,False,False,False,False,False,False,False,False,False]

R12d2d1a = Record()
R12d2d1a.name = '12.2.1.a'
R12d2d1a.entryNames = ['CFILEN']
R12d2d1a.start = [1]
R12d2d1a.end = [25]
R12d2d1a.isString = [False]

R12d3a = Record()
R12d3a.name = '12.3a'
R12d3a.entryNames = ['YMIN','YMAX','YSIZE','DELY','NUMSBY','NOENDY','IDEC','JEMIT','JPLOT','LOGPLT','JHDR','JOUT','JPLTFL']
R12d3a.start = [1,11,21,31,41,46,51,56,61,66,71,73,78]
R12d3a.end = [10,20,30,40,45,50,55,60,65,70,72,77,80]
R12d3a.isString = [False,False,False,False,False,False,False,False,False,False,False,False,False]
            
R12d2b = Record()
R12d2b.name = '12.2b'
R12d2b.entryNames = ['V1','V2','JFILE','JSKIPF','LFILE','LSKIPF','IOPT','MFILE']
R12d2b.start = [10,20,45,50,55,60,72,80]
R12d2b.end = [10,20,45,50,55,60,72,80]
R12d2b.isString = [False,False,False,False,False,False,False,False]

R12d2d1b = Record()
R12d2d1b.name = '12.2.1b'
R12d2d1b.entryNames = ['CFILEN']
R12d2d1b.start = [1]
R12d2d1b.end = [25]
R12d2d1b.isString = [False]

R12d2d2b = Record()
R12d2d2b.name = '12.2.2b'
R12d2d2b.entryNames = ['CFILEN']
R12d2d2b.start = [1]
R12d2d2b.end = [25]
R12d2d2b.isString = [False]

R12d2d3b = Record()
R12d2d3b.name = '12.2.3b'
R12d2d3b.entryNames = ['CFILEN']
R12d2d3b.start = [1]
R12d2d3b.end = [25]
R12d2d3b.isString = [False]


#
# given a line and a record, will find and print the record entries from that line
#
def getRecord(record, line):

    print("\n### RECORD "+record.name+" ###")

    if ( (len(record.entryNames)!=len(record.start)) or (len(record.start)!=len(record.end)) or (len(record.entryNames)!=len(record.isString)) ):
        print("entryName, entries, start, end, isString arrays do not all match in length for record "+record.name)

    i = 0
    for entryName in record.entryNames:
        # specify start and end column of TAPE5 entry
        startChar = record.start[i] - 1
        endChar = record.end[i]

        #print line[startChar:endChar]
    
        # get entry from cols in line 
        entry = line[startChar:endChar]

        # cut whitespace
        entry = re.sub(" ","",entry)
        entry = re.sub("\r","",entry)
        entry = re.sub("\n","",entry)

        if (len(entry) != 0):
            # treat as a value or a string
            if not record.isString[i]: # the entry is a value
                # convert the strings to proper data format
                if '.' in entry:
                    entry = float(entry)
                else:
                    entry = int(entry)
        else:
            if not record.isString[i]:
                entry = 0 

        # print out value
        print(record.entryNames[i]+": "+str(entry))

        # store the entry in the record structure
        record.entries[record.entryNames[i]] = entry
        
        i = i+1
    return 0

#
# given the set of lines from a TAPE3 file, will 
#
def runRecord(lines):
    # pass a set of lines to this function
    # the first line must include the CXID signal symbol $ 
    # which indicates that we start at Record 1.1 from there
    i = 0

    # print out the first record based on header
    if ("$") in lines[i]:
        print("\n### RECORD 1.1 ###")
        print(lines[i])
        i += 1
    
    # should always be present
    getRecord(R12, lines[i])
    i += 1

    if (R12.entries["IHIRAC"] != 0): # if = 0, HIRAC not activated; line-by-line calculation is bypassed, skip to other functions
        if (R12.entries["ICNTNM"] == 6):
            print("need to implement record 1.2a")
        if (R12.entries["IEMIT"] == 2):
            print("need to implement record 1.2.1")

        if (R12.entries["IHIRAC"] > 0) or (R12.entries["IAERSL"] > 0) or (R12.entries["IEMIT"] == 1) or (R12.entries["IATM"] == 1) or (R12.entries["ILAS"] > 0):
            getRecord(R13, lines[i])
            i += 1
            if (R13.entries["NMOL_SCAL"] > 0):
                print("need to implement record 1.3.a and 1.3.b" )

        # FIXME surf_refl specifies the surface type used in computing the reflected downward radiance: 's' or ' ' is for a specular surface, 'l' is for a lambertian surface
        if (R12.entries["IEMIT"] == 1) or ( (R12.entries["IEMIT"] == 2) and (R1d2d1.entries["IOTFLG"] == 2) ): # from 1.2.1, not implemented
            getRecord(R14, lines[i])
            i += 1

        if (R12.entries["IEMIT"] == 3) and ( (R12.entries["IMRG"] == 40) or (R12.entries["IMRG"] == 41) or (R12.entries["IMRG"] == 42) or (R12.entries["IMRG"] == 43) ):
            print("need to implement record 1.5")

        if (35 < R12.entries["IMRG"] < 36) or (40 < R12.entries["IMRG"] < 41) or (45 < R12.entries["IMRG"] < 46):
            print("need to implement record 1.6a")

        if (R12.entries["IATM"] == 0 and R12.entries["IPLOT"] == 0):
            getRecord(R21, lines[i])
            for layer in xrange(record21["NLAYRS"]):
                i += 1
                getRecord(R2d1d1, lines[i])
            print("need to implement records 2.1.2 - 2.3.4")

        if (R12.entries["IATM"] == 1):
            getRecord(R31, lines[i])
            i += 1

            if (R31.entries["ITYPE"] == 1):
                print("need to implement record 3.2H")
            else:
                getRecord(R32, lines[i])
                i += 1

            # at most 8 layer boundaries specified per line
            numberOfR31Lines = int(math.fabs(R31.entries["IBMAX"])/8) + 1
            if (R31.entries["IBMAX"] == 0):
                getRecord(R33a, lines[i])
                i += 1
            elif (R31.entries["IBMAX"] > 0):
                for layers in xrange(numberOfR31Lines):
                    getRecord(R33b1, lines[i]) # layers specified by altitude
                    i += 1
            elif (R31.entries["IBMAX"] < 0):
                for line in xrange(numberOfR31Lines):
                    getRecord(R33b2, lines[i]) # layers specified by pressure
                    i += 1

            if ( R12.entries["MODEL"] == 0 ):
                getRecord(R34, lines[i])
                i += 1
                if (R34.entries["IMMAX"] != 0):
                    for layer in xrange(int(math.fabs(R31.entries["IMMAX"]))):
                        getRecord(R35, lines[i])
                        i += 1
                        # at most 8 molecules specified per line
                        numberOfR36nLines = (len(R35.entries["JCHAR(M)"])/8) + 1
                        for line in xrange(numberOfR36nLines):
                            getRecord(R36n, lines[i])
                            i += 1
            
            if (R12.entries["IXSECT"] == 1):
                getRecord(R37, lines[i])
                i += 1
                getRecord(R371, lines[i])
                i += 1
                getRecord(R38, lines[i])
                i += 1
                for line in xrange(R371.entries["LAYX"]):
                    getRecord(R381, lines[i])
                    i += 1
                    getRecord(R38n, lines[i])
                    i += 1

            if ( R12.entries["ISOTPL"] == 1 ):
                print("need to implement records 3.9 - 3.9.4")
            
            if ( R12.entries["IAERSL"] == 5 ):
                print("need to implement records Abs.1 - Abs.4.2")
            
            if ( (R12.entries["IAERSL"] == 1) or (R12.entries["IAERSL"] == 7) ):
                print("need to implement records 4.1 - 4.6.2")
            
            if ( R12.entries["ILAS"] > 2 ):
                print("need to implement records 5.1 - 5.N")
            
            if ( R12.entries["IMRG"] != 0 ):
                print("need to implement records 7.1 - 7.N")
                
    # END if (IHIRAC != 0)

    if (R12.entries["ISCAN"] == 1):
        getRecord(R81, lines[i])
        i += 1
    if (R12.entries["ISCAN"] == 2):
        getRecord(R91, lines[i])
        i += 1
    if (R12.entries["ISCAN"] == 3):
        getRecord(R101, lines[i])
        i += 1

    if (R12.entries["IPLOT"] == 1):
        # this should print text if there is a title but the program treats it like a number
        getRecord(R12d1, lines[i])
        i += 1
        
        IOPT = int(lines[i][71:72])
        while ("-1." not in lines[i][0:10]):
            if ((IOPT == 0) or (IOPT == 1)):
                getRecord(R12d2a, lines[i])
                i += 1
                if (R12d1.entries['CEX'] == 'EX'):
                    getRecord(R12d2d1da, lines[i])
                    i += 1
                getRecord(R12d3a, lines[i])
                i += 1
            elif (IOPT == 2) or (IOPT == 3):
                getRecord(R12d2b, lines[i])
                i += 1
                getRecord(R12d2d1b, lines[i])
                i += 1
                getRecord(R12d2d2b, lines[i])
                i += 1
                getRecord(R12d2d3b, lines[i])
                i += 1
            # REPEAT RECORD 12.2A or RECORD 12.2B
            # A '-1.' within columns 1-10 will terminate plotting.

if __name__ == "__main__":
    
    filelocation = sys.argv[1]
    #filelocation = "./aer_lblrtm_v12.4_lnfl_v3.0/lblrtm/run_examples/run_example_built_in_atm_upwelling/TAPE5"
    #filelocation = "./aer_lblrtm_v12.4_lnfl_v3.0/lblrtm/run_examples/run_example_nonlte/TAPE5"
    
    with open("./"+filelocation,'r') as f:
        lines=f.readlines()

        # remove comments
        #for line in lines:
        #    if ("#") in line:
        #        lines.remove(line)

        # pass all lines after the '$'
        i = 0
        while i<len(lines):
            if ("-1." in lines[i][0:3]):
                print("")
                print(lines[i][0:3])
                i+=1
            if ("$") in lines[i]:
                runRecord(lines[i:])
            i+=1
        



