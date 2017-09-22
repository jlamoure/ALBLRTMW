# must be installed
import numpy as np
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.optimize as optimize # for the fitter
# included with python
import os,sys,argparse,time
# from scripts in local directory
import makeTAPE5lblrtm as lblrtm
import makeTAPE5lnfl as lnfl
import run
import plot

# sciPy's fitting function requires that the parameters be like so.
# This means that parameters not being fitted must be given to it another way.
# Solution: make all other LBLRTM parameters global python variables.
def spectrumFromParams(xdata,moleculeParams):
    # write all parameters into a TAPE5 for the LBLRTM to ingest
    lblrtm.writeTAPE5lblrtm("model for "+runName, runDir+'/'+runName+'/', startWn, endWn, angle,height,moleculeParams)
    # run LBLRTM, produce model
    run.runLBLRTM(buildDir,runDir+'/'+runName+'/',runName)
    # get model data from file
    xmodel,ymodel,xTitle,yTitle = plot.getLBLRTMoutput(runDir+'/'+runName+'/'+'TAPE30_'+runName)
    # reduce the model resolution so the model and data are the same size
    ymodel = np.interp(xdata,xmodel,ymodel)
    return ymodel

def chiSquared(xdata,ydata,ymodel):
    # nudge values to prevent NAN's from division
    # TODO just add 1. to both ydata and ymodel
    ymodel[np.where(ymodel == 0)] = 0.00000001
    chiSquared = np.sum(np.square(ydata-ymodel))#/ymodel) matt said
    chiSquared = chiSquared/len(xdata)
    return chiSquared

def fitParams(xdata,ydata,moleculeParams,algorithm):

    # this list of most abundant molecules was obtained
    # from inspecting the MIPAS dataset.
    names = ["H2O","CO2","O3","N2O","CO","CH4","O2","NO","SO2","NO2","NH3","HNO3","ClO","OCS","HOCl","N2","HCN","H2O2","C2H2","C2H6","COF2","SF6","ClONO2"]

    #order = [15,  6,  0,  1,  4,  7,  2,  5,  3,  9, 11, 22, 16,  8, 19, 13, 17, 12, 20, 14, 18, 10, 21]
    # put H2O, CO2, N20, CH4, O3, first
    #order = [  0,  1,  3,  5, 15,  2,  6,  4,  7,  9, 11, 22, 16,  8, 19, 13, 17, 12, 20, 14, 18, 10, 21]

    # TEST:
    # determine transmission strength of molecules in this region,
    # with snapshot atmospheres for each molecule at 1.0*(MIPAS abundance)
    # TODO look at line list for picking fit (total strength at loc. lines)
    '''
    molSway = np.zeros(len(moleculeParams))
    order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
    for mol in xrange(len(moleculeParams)):
        print("running solo models to determine molecule sway: "+str(mol+1)+"/"+str(len(moleculeParams)))
        params = np.zeros(len(moleculeParams))+.0001
        params[mol] = 1.
        molSway[mol] = np.sum(spectrumFromParams(xdata,params))
    coupledAndSorted = zip(*sorted(zip(molSway,names,order)))
    molSway,names,order = (list(Tuple) for Tuple in coupledAndSorted)
    print("transmission sum: "+repr(molSway))
    print("molecules: "+repr(names))
    print("order: "+repr(order))
    exit()
    '''
    # product of test:
    #  ['H2O', 'CO2', 'N2O', 'HNO3', 'O3', 'SO2', 'NH3', 'NO2', 'C2H2', 'C2H6', 'CH4', 'CO', 'COF2', 'ClO', 'ClONO2', 'H2O2', 'HCN', 'HOCl', 'N2', 'NO', 'O2', 'OCS', 'SF6']
    order =  [0, 1, 3, 11, 2, 8, 10, 9, 18, 19, 5, 4, 20, 12, 22, 17, 16, 14, 15, 7, 6, 13, 21]
    # but try not H2O first
    #order =  [1, 0, 3, 11, 2, 8, 10, 9, 18, 19, 5, 4, 20, 12, 22, 17, 16, 14, 15, 7, 6, 13, 21]
    
    numMols = 10

    #
    # Find a fit using the function ChiSquared(xdata,ydata,ymodel) as a metric.
    #
    # algorithm == 0,1,2
    #
    # 0 -> find better minimums of a quadratic in X^2 with three points at a time
    #
    # 1 -> keep track of three points closest to the current minimum,
    #      sampling neighboring spaces at the halfway point in search of a better one.
    #      TODO: sample both sides instead of picking one or the other
    #
    # 2 -> two-stage linear sampling of a range of abundance ratios.
    #      coarse search, then fine search in best of coarse search.
    #
    
    # these algorithms run the LBLRTM many times.
    # the LNFL need only be obtained once for a given wavelength range.
    run.createLineList(buildDir,runDir+'/'+runName+'/',runName)
    
    algorithm = int(algorithm) 
    
    # QUADRATIC SEARCH ALGORITHM
    if algorithm == 0:
        # search bounds
        guessStart = 0.01
        guessEnd = 2.
        numGuesses = 30
        # make X^2 array
        chiSqs = np.ones( (len(moleculeParams),numGuesses+3) )*np.inf
        middleParams = np.ones(len(moleculeParams))
        for mol in xrange(numMols-1):
            # make the three adjacent guesses the same in all but one parameter
            # the middle point should be the minimum in X^2 of the three
            leftParams = np.copy(middleParams)
            rightParams = np.copy(middleParams)
            # make guesses array
            guesses = np.zeros((len(moleculeParams),numGuesses+3))
            # make three initial guesses
            leftParams[order[mol]] = guessStart
            middleParams[order[mol]] = (guessStart+guessEnd)/2.2
            rightParams[order[mol]] = guessEnd
            guesses[order[mol]][0] = leftParams[order[mol]]
            guesses[order[mol]][1] = middleParams[order[mol]]
            guesses[order[mol]][2] = rightParams[order[mol]]
            # run three initial models
            print("making initial guess 1/3 for "+names[order[mol]])
            leftYModel = spectrumFromParams(xdata,leftParams)
            print("making initial guess 2/3 for "+names[order[mol]])
            middleYModel = spectrumFromParams(xdata,middleParams)
            print("making initial guess 3/3 for "+names[order[mol]])
            rightYModel = spectrumFromParams(xdata,rightParams)
            # save X^2 values
            leftChiSq = chiSquared(xdata,ydata,leftYModel)
            middleChiSq = chiSquared(xdata,ydata,middleYModel)
            rightChiSq = chiSquared(xdata,ydata,rightYModel)
            chiSqs[order[mol]][0] = leftChiSq
            chiSqs[order[mol]][1] = middleChiSq
            chiSqs[order[mol]][2] = rightChiSq
            # if the first is the SAME the second,
            # and the second is the SAME as the third, 
            # then a plateau has been reached for that molecule parameter.
            if ( np.round(chiSqs[order[mol]][0],5) == np.round(chiSqs[order[mol]][1],5) ):
                if ( np.round(chiSqs[order[mol]][1],5) == np.round(chiSqs[order[mol]][2],5) ):
                    print("looks like a X^2 plateau, moving on to next molecule")
                    continue
            # do a quadratic search this deep
            for step in xrange(numGuesses): 
                # PROBLEM CASES:
                # middle higher than both ends
                if (leftChiSq < middleChiSq) and (rightChiSq < middleChiSq):
                    print("this X^2 curve doesn't look quadratic. Brute-force it?")
                    break
                # middle higher than left
                if (leftChiSq < middleChiSq):
                    print("the left of this quadratic is shorter than the middle! Insert test point into the left-middle")
                    # test midpoint of left-middle
                    rightParams = np.copy(middleParams)
                    rightChiSq = middleChiSq
                    middleParams[order[mol]] = (middleParams[order[mol]]+leftParams[order[mol]])/2.
                    middleModel = spectrumFromParams(xdata,middleParams)
                    middleChiSq = chiSquared(xdata,ydata,middleModel)
                    print("injected new point into left-middle, hopefully no longer lopsided")
                    continue
                # middle higher than right
                if (rightChiSq < middleChiSq):
                    print("the right of this quadratic is shorter than the middle! Insert test point into the middle-right")
                    # test midpoint of middle-right
                    leftParams = np.copy(middleParams)
                    leftChiSq = middleChiSq
                    middleParams[order[mol]] = (middleParams[order[mol]]+rightParams[order[mol]])/2.
                    middleModel = spectrumFromParams(xdata,middleParams)
                    middleChiSq = chiSquared(xdata,ydata,middleModel)
                    print("injected new point into right-middle, hopefully no longer lopsided")
                    continue
                # HAPPY CASE: the middle is the minimum
                # solve for a new quadratic minimum
                else:
                    # fit quadratic and calculate minimum with the three test points
                    # the index inclusion for the fit accounts for the first three guesses
                    '''
                    if step < 3:
                        popt, pcov = optimize.curve_fit(plot.quadratic, guesses[order[mol]][0:(step+3)], chiSqs[order[mol]][0:(step+3)])
                    else:
                        popt, pcov = optimize.curve_fit(plot.quadratic, guesses[order[mol]][step:(step+3)], chiSqs[order[mol]][step:(step+3)])
                    '''
                    popt, pcov = optimize.curve_fit(plot.quadratic,[leftParams[order[mol]],middleParams[order[mol]],rightParams[order[mol]]],[leftChiSq,middleChiSq,rightChiSq])
                    a = popt[0]
                    b = popt[1]
                    c = popt[2]
                    # want to minimize ax^2 + bx + c
                    # --> derivative = 0
                    # --> 2ax + b = 0 
                    # --> x = -b/2a 
                    minGuess = (-0.5*b)/a
                    minParams = np.copy(middleParams)
                    minParams[order[mol]] = minGuess
                    # make model with new parameter guess
                    minYModel = spectrumFromParams(xdata,minParams)
                    minChiSq = chiSquared(xdata,ydata,minYModel)
                    # save guess and X^2 for the quadratic fit array
                    chiSqs[order[mol]][step+3] = minChiSq
                    guesses[order[mol]][step+3] = minGuess
                    # decide where to put the new point
                    if (leftParams[order[mol]] < minGuess) and (minGuess < middleParams[order[mol]]): # minGuess is in between left and middle on guess axis
                        if (minChiSq < middleChiSq): # minChiSq is actually the new min
                            # make the middle the new right guess
                            # make minGuess the new middle
                            rightParams[order[mol]] = np.copy(middleParams[order[mol]])
                            middleParams[order[mol]] = minGuess
                            rightChiSq = middleChiSq
                            middleChiSq = minChiSq
                        else: # minGuess wasn't better than the current middleChiSq
                            # make minGuess the new left guess
                            leftParams[order[mol]] = minGuess
                            leftChiSq = minChiSq 
                    elif (middleParams[order[mol]] < minGuess) and (minGuess < rightParams[order[mol]]): # minGuess is in between middle and right on guess axis
                        if (minChiSq < middleChiSq): # minChiSq is actually the new min
                            # make the middle the new left guess
                            # make minGuess the new middle
                            leftParams[order[mol]] = np.copy(middleParams[order[mol]])
                            middleParams[order[mol]] = minGuess
                            leftChiSq = middleChiSq
                            middleChiSq = minChiSq
                        else: # minGuess wasn't better than the current middleChiSq
                            # make minGuess the new right guess
                            rightParams[order[mol]] = minGuess
                            rightChiSq = minChiSq 
                    else:
                        print("something went wrong! the new guess is out of expected bounds")
                # PRINTING
                print("\nQUADRATIC SEARCH PARAMETER FIT:\n")
                print("guess "+str(step+1)+"/"+str(numGuesses)+" for molecule "+str(mol+1)+"/"+str(numMols)+" complete: "+names[order[mol]])
                print("        all middle guesses: "+repr(guesses[order[mol]][:]))
                print("        all middle X^2: "+repr(chiSqs[order[mol]][:]))
                print("        left guess: "+repr(leftParams[order[:]]))
                print("        middle guess: "+repr(middleParams[order[:]]))
                print("        right guess: "+repr(rightParams[order[:]]))
                print("        left X^2: "+repr(leftChiSq))
                print("        middle X^2: "+repr(middleChiSq))
                print("        right X^2: "+repr(rightChiSq))
            # plot the X^2 array
            #plot.plotPoints(scatter=(guesses[order[mol]][:],chiSqs[order[mol]][:]),pointSize=2.)
            print(len(guesses[order[mol]][:]))
            print(len(chiSqs[order[mol]][:]))
            print(guesses[order[mol]][:])
            print(chiSqs[order[mol]][:])
        bestParams = np.copy(middleParams)
    # BINARY SEARCH ALGORITHM
    # do a binary search, minimizing X^2 between the model and reference, 
    # keeping track of three adjacent points in parameter-space.
    # TODO memoize all X^2 taken and plot
    elif algorithm == 1: 
        # search bounds
        guessStart = 0.01
        guessEnd = 2.
        numGuesses = 30

        middleParams = np.ones(len(moleculeParams))
        for mol in xrange(numMols-1):
            # make the three adjacent guesses the same in all but one parameter
            # the middle point should be the minimum in X^2 of the three
            leftParams = np.copy(middleParams)
            rightParams = np.copy(middleParams)
            # make three initial guesses
            leftParams[order[mol]] = guessStart
            middleParams[order[mol]] = (guessStart+guessEnd)/2.
            rightParams[order[mol]] = guessEnd
            # run a model with those guess parameters
            print("making initial guess 1/3 for "+names[order[mol]])
            leftYModel = spectrumFromParams(xdata,leftParams)
            print("making initial guess 2/3 for "+names[order[mol]])
            middleYModel = spectrumFromParams(xdata,middleParams)
            print("making initial guess 3/3 for "+names[order[mol]])
            rightYModel = spectrumFromParams(xdata,rightParams)
            # save X^2 values
            leftChiSq = chiSquared(xdata,ydata,leftYModel)
            middleChiSq = chiSquared(xdata,ydata,middleYModel)
            rightChiSq = chiSquared(xdata,ydata,rightYModel)
            # do a binary search this deep
            for i in xrange(numGuesses): 
                # PRINTING
                print("\nBINARY SEARCH PARAMETER FIT:\n")
                print("making guess "+str(i+1)+"/"+str(numGuesses)+" for molecule "+str(mol+1)+"/"+str(numMols)+": "+names[order[mol]])
                print("        left guess: "+repr(leftParams[order[:]]))
                print("        middle guess: "+repr(middleParams[order[:]]))
                print("        right guess: "+repr(rightParams[order[:]]))
                print("        left X^2: "+repr(leftChiSq))
                print("        middle X^2: "+repr(middleChiSq))
                print("        right X^2: "+repr(rightChiSq))

                # CASE 1: middle higher than both ends
                # the center point can be higher than one, but not both points.
                # assuming that X^2 curve for fit over parameters looks quadratic.
                if (leftChiSq < middleChiSq) and (rightChiSq < middleChiSq):
                    print("this X^2 curve doesn't look quadratic. Put brute-force search here?")
                    break
                # CASE 2: the middle is the minimum
                elif (leftChiSq > middleChiSq) and (rightChiSq > middleChiSq):
                    if ((rightParams[order[mol]]-middleParams[order[mol]]) > (middleParams[order[mol]]-leftParams[order[mol]])):
                        # test midpoint of middle-right
                        newGuess = (middleParams[order[mol]]+rightParams[order[mol]])/1.8
                        newGuessParams = np.copy(middleParams)
                        newGuessParams[order[mol]] = newGuess
                        # make model with new parameter guess
                        newYModel = spectrumFromParams(xdata,newGuessParams)
                        newChiSq = chiSquared(xdata,ydata,newYModel)
                        if (newChiSq > middleChiSq):
                            # move the right closer to the middle
                            rightParams[order[mol]] = newGuess
                            rightChiSq = newChiSq
                        else:
                            # make the left the middle
                            leftParams[order[mol]] = middleParams[order[mol]]
                            leftChiSq = middleChiSq
                            # move the middle to the middle-right
                            middleParams[order[mol]] = newGuess
                            middleChiSq = newChiSq
                    else:
                        # test midpoint of left-middle
                        newGuess = (middleParams[order[mol]]+leftParams[order[mol]])/2.2
                        newGuessParams = np.copy(middleParams)
                        newGuessParams[order[mol]] = newGuess
                        # make model with new parameter guess
                        newYModel = spectrumFromParams(xdata,newGuessParams)
                        newChiSq = chiSquared(xdata,ydata,newYModel)
                        if (newChiSq > middleChiSq):
                            # move the left closer to the middle
                            leftParams[order[mol]] = newGuess
                            leftChiSq = newChiSq
                        else:
                            # make the right the middle
                            rightParams[order[mol]] = middleParams[order[mol]]
                            rightChiSq = middleChiSq
                            # move the middle to the middle-left
                            middleParams[order[mol]] = newGuess
                            middleChiSq = newChiSq
        bestParams = np.copy(middleParams)
        bestChiSq = middleChiSq
    # BRUTE FORCE ALGORITHM
    # linear search for best fit
    elif algorithm == 2:
        # COARSE FIT
        guessStart = 0.01
        guessEnd = 2.
        numGuesses = 40
        guesses = np.round(np.linspace(guessStart,guessEnd,numGuesses),3)
        bestChiSq = np.inf
        chiSqs = np.ones( (len(moleculeParams),numGuesses) )*np.inf
        bestParams = np.ones(len(moleculeParams))
        for mol in xrange(numMols-1):
            # when moving on to a new molecule, reset current guess to
            # the previous molecules' best guesses
            guessParams = np.copy(bestParams)
            # step through coarse guess range
            for step in xrange(len(guesses)):
                # set current guess
                guessParams[order[mol]] = guesses[step]
                # run a model with those parameters
                ymodel = spectrumFromParams(xdata,guessParams)
                # save X^2 values
                chiSqs[order[mol]][step] = chiSquared(xdata,ydata,ymodel)
                # save best parameters
                if (chiSqs[order[mol]][step] < bestChiSq):
                    bestChiSq = chiSqs[order[mol]][step]
                    bestParams = np.copy(guessParams)
                # PRINTING
                print("\nCOARSE PARAMETER FIT:\n")
                for j in xrange(mol+1):
                    print(names[order[j]])
                    print("        guesses: "+repr(guesses)) 
                    print("        X^2: "+repr(chiSqs[order[j]]))
                print("guessParams:    "+repr(guessParams[order[:]]))
                print("bestParams:    "+repr(bestParams[order[:]]))
                # guess if it's worth it to keep trying parameters
                # look at previous three X^2 values (rounded to some decimal place)
                if (step >= 1):
                    # same X^2 obtained as last parameter guess:
                    # a plateau has been reached for that molecule parameter.
                    if ( np.round(chiSqs[order[mol]][step-1],5) == np.round(chiSqs[order[mol]][step],5) ):
                        print("looks like a X^2 plateau, moving on to next molecule")
                        break
                    # if the first is MORE than the second,
                    # and the second is the LESS than the third, 
                    # then a local minimum has been found for that molecule parameter.
                    if ( np.round(chiSqs[order[mol]][step-2],5) > np.round(chiSqs[order[mol]][step-1],5) ):
                        if ( np.round(chiSqs[order[mol]][step-1],5) < np.round(chiSqs[order[mol]][step],5) ):
                            print("looks like a X^2 local minumum, moving on to next molecule")
                            break
            # plot the X^2 array
            #plot.plotPoints(scatter=(guesses[:],chiSqs[order[mol]][:]),pointSize=2.)
        
        # FINE FIT
        numGuesses = 100
        # make array of guesses centered around the best results from the courase search
        fineGuesses = np.zeros((len(moleculeParams),numGuesses))
        for mol in xrange(numMols):
            guessStart = bestParams[order[mol]]+0.07
            guessEnd = np.maximum(bestParams[order[mol]]-0.07,0.00001) # no negative abundances!
            guesses = np.linspace(guessStart,guessEnd,numGuesses)
            for step in xrange(numGuesses):
                fineGuesses[mol][step] = guesses[step] 
        # reset the X^2 array
        bestChiSq = np.inf
        chiSqs = np.ones( (len(moleculeParams),numGuesses) )*np.inf
        for mol in xrange(numMols-1):
            # when moving on to a new molecule, reset current guess to
            # the previous molecules' best guesses
            guessParams = np.copy(bestParams)
            # step through coarse guess range
            for step in xrange(len(guesses)):
                # set current guess
                guessParams[order[mol]] = fineGuesses[mol][step]
                # run a model with those parameters
                ymodel = spectrumFromParams(xdata,guessParams)
                # save X^2 values
                chiSqs[order[mol]][step] = chiSquared(xdata,ydata,ymodel)
                # save best parameters
                if (chiSqs[order[mol]][step] < bestChiSq):
                    bestChiSq = chiSqs[order[mol]][step]
                    bestParams = np.copy(guessParams)
                # PRINTING
                print("\nFINE PARAMETER FIT:\n")
                for j in xrange(mol+1):
                    print(names[order[j]])
                    print("        guesses: "+repr(fineGuesses[j]))
                    print("        X^2: "+repr(chiSqs[order[j]]))
                print("guessParams:    "+repr(guessParams[order[:]]))
                print("bestParams:    "+repr(bestParams[order[:]]))
                # guess if it's worth it to keep trying parameters
                # look at previous three X^2 values (rounded to some decimal place)
                if (step >= 1):
                    # same X^2 obtained as last parameter guess:
                    # a plateau has been reached for that molecule parameter.
                    if ( np.round(chiSqs[order[mol]][step-1],7) == np.round(chiSqs[order[mol]][step],7) ):
                        print("looks like a X^2 plateau, moving on to next molecule")
                        break
                    # if the first is MORE than the second,
                    # and the second is the LESS than the third, 
                    # then a local minimum has been found for that molecule parameter.
                    if ( np.round(chiSqs[order[mol]][step-2],7) > np.round(chiSqs[order[mol]][step-1],7) ):
                        if ( np.round(chiSqs[order[mol]][step-1],7) < np.round(chiSqs[order[mol]][step],7) ):
                            print("looks like a X^2 local minumum, moving on to next molecule")
                            break
            # plot the X^2 array
            #plot.plotPoints(scatter=(guesses[:],chiSqs[order[mol]][:]),pointSize=2.)
    # QUADRATIC SEARCH ALGORITHM
    elif algorithm == 3:
        # search bounds
        guessStart = 0.01
        guessEnd = 2.
        numGuesses = 30
        # make X^2 array
        chiSqs = np.ones( (len(moleculeParams),numGuesses+3) )*np.inf
        threeParams = np.ones(len(moleculeParams))
        for mol in xrange(numMols-1):
            #
            # obtain 5 points on X^2 quadratic where 3 is the minimum
            #
            # make the three adjacent guesses the same in all but one parameter
            # the middle point should be the minimum in X^2 of the three
            oneParams = np.copy(threeParams)
            twoParams = np.copy(threeParams)
            fourParams = np.copy(threeParams)
            fiveParams = np.copy(threeParams)
            # make guesses array
            guesses = np.zeros((len(moleculeParams),numGuesses+3))
            # make initial guesses
            oneParams[order[mol]] = guessStart
            twoParams[order[mol]] = guessStart+((guessEnd-guessStart)*1./4.)
            threeParams[order[mol]] = guessStart+((guessEnd-guessStart)*2./4.)
            fourParams[order[mol]] = guessStart+((guessEnd-guessStart)*3./4.)
            fiveParams[order[mol]] = guessEnd
            guesses[order[mol]][0] = oneParams[order[mol]]
            guesses[order[mol]][1] = twoParams[order[mol]]
            guesses[order[mol]][2] = threeParams[order[mol]]
            guesses[order[mol]][3] = fourParams[order[mol]]
            guesses[order[mol]][4] = fiveParams[order[mol]]
            # run initial models
            print("making initial guess 1/5 for "+names[order[mol]])
            oneModel = spectrumFromParams(xdata,oneParams)
            print("making initial guess 2/5 for "+names[order[mol]])
            twoModel = spectrumFromParams(xdata,twoParams)
            print("making initial guess 3/5 for "+names[order[mol]])
            threeModel = spectrumFromParams(xdata,threeParams)
            print("making initial guess 4/5 for "+names[order[mol]])
            fourModel = spectrumFromParams(xdata,fourParams)
            print("making initial guess 5/5 for "+names[order[mol]])
            fiveModel = spectrumFromParams(xdata,fiveParams)
            # save X^2 values
            oneChiSq = chiSquared(xdata,ydata,oneModel)
            twoChiSq = chiSquared(xdata,ydata,twoModel)
            threeChiSq = chiSquared(xdata,ydata,threeModel)
            fourChiSq = chiSquared(xdata,ydata,fourModel)
            fiveChiSq = chiSquared(xdata,ydata,fiveModel)
            chiSqs[order[mol]][0] = oneChiSq
            chiSqs[order[mol]][1] = twoChiSq
            chiSqs[order[mol]][2] = threeChiSq
            chiSqs[order[mol]][3] = fourChiSq
            chiSqs[order[mol]][4] = fiveChiSq
            # INITIAL GUESSES PROBLEM CASES:
            while not ((twoChiSq > threeChiSq) and (threeChiSq < fourChiSq)):
                # make sure that the 3 is the minimum of the 5
                # three is higher than both two and four
                if (twoChiSq < threeChiSq) and (fourChiSq < threeChiSq):
                    print("this X^2 curve doesn't look quadratic. Brute-force it?")
                    break
                # two is the minimum
                elif (twoChiSq < threeChiSq):
                    print("the 2nd point of this quadratic is shorter than the 3rd! Insert test point into 1-2 region")
                    # make 4 the new 5, make 3 the new 4, make 2 the new 3, make 1-2 the new 2
                    fiveParams = np.copy(fourParams)
                    fourParams = np.copy(threeParams)
                    threeParams = np.copy(twoParams)
                    fiveChiSq = fourChiSq
                    fourChiSq = threeChiSq
                    threeChiSq = twoChiSq
                    twoParams[order[mol]] = (oneParams[order[mol]]+twoParams[order[mol]])/2.
                    twoModel = spectrumFromParams(xdata,twoParams)
                    twoChiSq = chiSquared(xdata,ydata,twoModel)
                    print("injected new point into 1-2, hopefully no longer lopsided")
                # four is the minimum
                elif (fourChiSq < threeChiSq):
                    print("the 4th point of this quadratic is shorter than the 3rd! Insert test point into the 3-4 region")
                    # make 2 the new 1, make 3 the new 2, make 4 the new 3, make 3-4 the new 4
                    oneParams = np.copy(twoParams)
                    twoParams = np.copy(threeParams)
                    threeParams = np.copy(fourParams)
                    oneChiSq = twoChiSq
                    twoChiSq = threeChiSq
                    threeChiSq = fourChiSq
                    fourParams[order[mol]] = (threeParams[order[mol]]+fourParams[order[mol]])/2.
                    fourModel = spectrumFromParams(xdata,threeParams)
                    fourChiSq = chiSquared(xdata,ydata,threeModel)
                    print("injected new point into 3rd-4th, hopefully no longer lopsided")
                # if the first is the SAME the second,
                # and the second is the SAME as the third, 
                # then a plateau has been reached for that molecule parameter.
                elif ( np.round(chiSqs[order[mol]][0],5) == np.round(chiSqs[order[mol]][1],5) ):
                    if ( np.round(chiSqs[order[mol]][1],5) == np.round(chiSqs[order[mol]][2],5) ):
                        print("looks like a X^2 plateau, moving on to next molecule")
                        continue
                # plot it
                plot.plotPoints(scatter=([oneParams[order[mol]],twoParams[order[mol]],threeParams[order[mol]],fourParams[order[mol]],fiveParams[order[mol]]],[oneChiSq,twoChiSq,threeChiSq,fourChiSq,fiveChiSq]),pointSize=2.)
            #
            # do a quadratic search this deep
            #
            for step in xrange(numGuesses): 
                # plot the X^2 array
                #plot.plotPoints(scatter=(guesses[order[mol]][:],chiSqs[order[mol]][:]),pointSize=2.)
                plot.plotPoints(scatter=([oneParams[order[mol]],twoParams[order[mol]],threeParams[order[mol]],fourParams[order[mol]],fiveParams[order[mol]]],[oneChiSq,twoChiSq,threeChiSq,fourChiSq,fiveChiSq]),pointSize=2.)
                # solve for a new quadratic minimum
                # fit quadratic and calculate minimum with the three test points
                # the index inclusion for the fit accounts for the first three guesses
                popt, pcov = optimize.curve_fit(plot.quadratic,[oneParams[order[mol]],twoParams[order[mol]],threeParams[order[mol]],fourParams[order[mol]],fiveParams[order[mol]]],[oneChiSq,twoChiSq,threeChiSq,fourChiSq,fiveChiSq])
                a = popt[0]
                b = popt[1]
                c = popt[2]
                # want to minimize ax^2 + bx + c
                # --> derivative = 0
                # --> 2ax + b = 0 
                # --> x = -b/2a 
                minGuess = (-0.5*b)/a
                minParams = np.copy(threeParams)
                minParams[order[mol]] = minGuess
                # make model with new parameter guess
                minModel = spectrumFromParams(xdata,minParams)
                minChiSq = chiSquared(xdata,ydata,minModel)
                # save guess and X^2 for the quadratic fit array
                chiSqs[order[mol]][step+3] = minChiSq
                guesses[order[mol]][step+3] = minGuess
                # decide where to put the new point
                if (oneParams[order[mol]] < minGuess) and (minGuess < twoParams[order[mol]]): # minGuess is between 1-2
                    if (minChiSq < threeChiSq): # minChiSq is actually the new min
                        # FIXME
                        print("unexpected minimum at 1-2!")
                        continue
                        # make 4 the new 5
                        # make 3 the new 4
                        # make minGuess the new 3
                        fiveParams[order[mol]] = fourParams[order[mol]]
                        fourParams[order[mol]] = threeParams[order[mol]]
                        threeParams[order[mol]] = minGuess
                        fiveChiSq = fourChiSq
                        fourChiSq = threeChiSq
                        threeChiSq = minChiSq
                    else: # minGuess wasn't better than the current threeChiSq
                        # make minGuess the new 1
                        oneParams[order[mol]] = minGuess
                        oneChiSq = minChiSq
                elif (twoParams[order[mol]] < minGuess) and (minGuess < threeParams[order[mol]]): # minGuess is between 2-3
                    if (minChiSq < threeChiSq): # minChiSq is actually the new min
                        # TODO: alternate placing left of 3, then right of 3
                        # make 4 the new 5
                        # make 3 the new 4
                        # make minGuess the new 3
                        fiveParams[order[mol]] = fourParams[order[mol]]
                        fourParams[order[mol]] = threeParams[order[mol]]
                        threeParams[order[mol]] = minGuess
                        fiveChiSq = fourChiSq
                        fourChiSq = threeChiSq
                        threeChiSq = minChiSq
                    else: # minGuess wasn't better than the current threeChiSq
                        # make 2 the new 1
                        # make minGuess the new 2
                        oneParams[order[mol]] = twoParams[order[mol]]
                        twoParams[order[mol]] = minGuess
                        oneChiSq = twoChiSq
                        twoChiSq = minChiSq 
                elif (threeParams[order[mol]] < minGuess) and (minGuess < fourParams[order[mol]]): # minGuess is between 3-4
                    if (minChiSq < threeChiSq): # minChiSq is actually the new min
                        # make 2 the new 1
                        # make 3 the new 2
                        # make minGuess the new 3
                        oneParams[order[mol]] = twoParams[order[mol]]
                        twoParams[order[mol]] = threeParams[order[mol]]
                        threeParams[order[mol]] = minGuess
                        oneChiSq = twoChiSq
                        twoChiSq = threeChiSq
                        threeChiSq = minChiSq
                    else: # minGuess wasn't better than the current middleChiSq
                        # make 4 the new 5
                        # make minGuess the new 4
                        fiveParams[order[mol]] = fourParams[order[mol]]
                        fourParams[order[mol]] = minGuess
                        fiveChiSq = fourChiSq
                        fourChiSq = minChiSq 
                elif (fourParams[order[mol]] < minGuess) and (minGuess < fiveParams[order[mol]]): # minGuess is between 4-5
                    if (minChiSq < threeChiSq): # minChiSq is actually the new min
                        # FIXME
                        print("unexpected minimum at 4-5!")
                        continue
                        # make 2 the new 1
                        # make 3 the new 2
                        # make minGuess the new 3
                        oneParams[order[mol]] = twoParams[order[mol]]
                        twoParams[order[mol]] = threeParams[order[mol]]
                        threeParams[order[mol]] = minGuess
                        oneChiSq = twoChiSq
                        twoChiSq = threeChiSq
                        threeChiSq = minChiSq
                    else: # minGuess wasn't better than the current middleChiSq
                        # make minGuess the new 5
                        fiveParams[order[mol]] = minGuess
                        fiveChiSq = minChiSq 
                else:
                    print("something went wrong! the new guess is out of expected bounds")
                    exit()
                # PRINTING
                print("\nQUADRATIC SEARCH PARAMETER FIT:\n")
                print("guess "+str(step+1)+"/"+str(numGuesses)+" for molecule "+str(mol+1)+"/"+str(numMols)+" complete: "+names[order[mol]])
                print("        all 3 guesses: "+repr(guesses[order[mol]][:]))
                print("        all 3 X^2: "+repr(chiSqs[order[mol]][:]))
                print("        1 guess: "+repr(twoParams[order[:]]))
                print("          2 guess: "+repr(twoParams[order[:]]))
                print("            3 guess: "+repr(threeParams[order[:]]))
                print("              4 guess: "+repr(fourParams[order[:]]))
                print("                5 guess: "+repr(twoParams[order[:]]))
                print("        1 X^2: "+repr(twoChiSq))
                print("          2 X^2: "+repr(twoChiSq))
                print("            3 X^2: "+repr(threeChiSq))
                print("              4 X^2: "+repr(fourChiSq))
                print("                5 X^2: "+repr(twoChiSq))

            print(len(guesses[order[mol]][:]))
            print(len(chiSqs[order[mol]][:]))
            print(guesses[order[mol]][:])
            print(chiSqs[order[mol]][:])
        bestParams = np.copy(threeParams)
    else:
        print("algorithm number not valid or parsing properly: "+repr(algorithm))
    
    return bestParams

def fitSpectrumToSpectrum(xdata,ydata,moleculeParams,algorithm):
    # generate a TAPE5 for the line file program if needed
    if not os.path.exists(runDir+'/'+runName+'/'+'TAPE1'):
        lnfl.writeTAPE5lnfl(runDir+runName,startWn-5.,endWn+5.)
        # run the line file program, creating a TAPE1 linked 
        #                  to the lnfl for the LBLRTM to use
        run.createLineList(buildDir,runDir+'/'+runName+'/',runName)
    bestParams = fitParams(xdata,ydata,moleculeParams,algorithm)
    return 0

if __name__ == "__main__":
    global buildDir
    global runDir 
    global runName
    global startWn
    global endWn
    global angle
    global height

    startTime = time.time()
    if len(sys.argv) == 3:
        if int(sys.argv[1]) == 0:
            print("algorithm 0: quadratic fit X^2 to find minimum X^2")
        elif int(sys.argv[1]) == 1:
            print("algorithm 1: guess by halves to the minimum X^2")
        elif int(sys.argv[1]) == 2:
            print("algorithm 2: coarse and then fine linear search to minimum X^2")
        elif int(sys.argv[1]) == 3:
            print("algorithm 3: better quadratic fit X^2 to find minimum X^2")
        else:
            print("not a valid algorithm number")
            exit()
        inputSpectrum = sys.argv[2]
    else:
        print("usage: python fitter.py algorithm-int input-spectrum-file")
        exit()
    
    buildDir = "testinstall/"
    runDir = "./"
    runName = "testmodel"

    # TODO: moleculeParams has no bearing on the initial guesses
    moleculeParams = np.array([0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01])
    startWn = 580.0
    endWn = 590.0
    angle = 66.6
    height = 4.205
    
    xdata, ydata = plot.getXYpoints(inputSpectrum)
    fitSpectrumToSpectrum(xdata,ydata,moleculeParams,sys.argv[1])
    endTime = time.time()
    print("Algorithm ran in "+str(np.round((endTime-startTime),2))+" seconds.")

    #TODO: allow start/end wn, angle, height, as command line params
    #TODO: allow FITS file as input, grab params from header data
