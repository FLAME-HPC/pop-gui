#!/usr/bin/python
"""
    Experiment manager Library for EURACE
    
    Author: Mehmet Gencer, mgencer@cs.bilgi.edu.tr
    Bulent Ozel, bulent.ozel@gmail.com, Reykjavik University
"""

import sys,pickle,getopt
from poplib import *
if __name__=="__main__":
    try:
        setDebugValue(0)
    except:setDebug(0)
    optlist, args = getopt.getopt(sys.argv[1:],"rg")
    for o in optlist:
        o,v=o
        if o=="-r":
            setReplaceId()
            print "USING '",getReplaceId(), "' AS ID PREFIX"
        if o=="-g":
            setRegionReplaceId()
            print "USING '",getRegionReplaceId(), "' AS ID PREFIX"
    try:
        popfile=args[0]
        zerofile=args[1]
    except:
        print "usage:\n %s [-rg] popfile 0.xml"%sys.argv[0]
        print "OPTIONS: \n  -r : Prefix  IDs with replacement markers"
        print "OPTIONS: \n  -g : Prefix region IDs with string 'REPLACE_REGIONID_'"
        sys.exit()
    try:
        numthreads=int(sys.argv[3])
        print "WILL USE NUMBER OF THREADS:",numthreads
    except:
        try:
            if MULTIPROC:
                import multiprocessing
                numthreads=multiprocessing.cpu_count()
            else:
                numthreads=0
        except:
            numthreads=0
    pop=pickle.load(open(popfile,"rb"))
    globalSetNumRegions(pop.numregions)
    global popguinumregions
    popguinumregions=pop.numregions
    print "popguinumregions",popguinumregions
    #try:
    #    pop.instantiateMEMEFF(open(zerofile,"w"),numthreads=numthreads)
    #except:
    #    pop.instantiate(open(zerofile,"w"))
    pop.instantiate(open(zerofile,"w"))
    print "POPULATION IS INSTANTIATED SUCCESSFULLY IN ",zerofile
