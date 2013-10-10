#!/usr/bin/python
"""
    Experiment manager Library for EURACE
    
    Author: Mehmet Gencer, mgencer@cs.bilgi.edu.tr
            Bulent Ozel, bulent.ozel@gmail.com, Reykjavik University
"""
import sys, os, os.path, pickle, traceback, getopt, thread
from poplib import *

def getRepType():
    print "Enter the report type. One of the following :"
    print "   constants : report environment constants as a LaTeX table"
    print "   regions   : report conposition of regions as a LaTeX table"
    print "   memory    : report memory initialization forms as a LaTeX table"
    return raw_input("Report type ? (just press ENTER to exit):")
def isValidType(outtype):
    if outtype in ["constants","regions","memory", ""]:return 1
    return 0
def escape(x):
    y=x.replace("_","\\_")
    y=y.replace("%","\\%")
    return y
def dump(*args):
    lastarg=0
    for a in args:
        outputfile.write(str(a))
        lastarg=a
    if not lastarg==None:outputfile.write("\n")
    outputfile.flush()
def constants(pop):
    dump()
    dump( "\\begin{longtable}{ll}")
    for cname in pop.model.getConstantNames():
        c=pop.model.getConstantByName(cname)
        dump("%s & %s \\\\" %(escape(cname),escape(c.getExpression())))
    dump( "\\end{longtable}")
def regions(pop):
    dump()
    dump( "\\begin{longtable}{l",)
    numreg=pop.getNumRegions()
    agents=pop.model.getAgentNames()
    for a in agents:dump( "l",)
    dump( "}")
    dump( "REGION NO ",)
    for a in agents:dump( "&",escape(a),)
    dump("\\\\")
    for rno in range(1,numreg+1):
        r=pop.getNumberedRegion(rno-1)
        print rno,
        for a in agents:
            dump( "&",r.getNumAgents(a),)
        dump("\\\\")
    dump("\\end{longtable}")
def memory(pop):
    numreg=pop.getNumRegions()
    for rno in range(1,numreg+1):
        dump( "************************  MEMORY VARIABLES FOR REGION ",rno)
        regionMemory(pop,rno)
def regionMemory(pop,rno):
    dump()
    def printVar(aname,mv,prefix=""):
        for k in mv.getKeys():
            vname,vtype=k
            initform=mv.getForm(vname)
            if isinstance(initform,MemVar):#Will need to recurse into this var!
                printVar(aname,initform,prefix=prefix+"."+vname)
            else: 
                pref=""
                if prefix:
                    pref=escape(prefix)
                dump( "%s%s.%s & %s \\\\"%(escape(aname),pref,escape(vname),escape(initform.getFormStr())))
    dump( "\\begin{longtable}{ll}")
    agents=pop.model.getAgentNames()
    r=pop.getNumberedRegion(rno-1)
    for aname in agents:
        a=r.model.getAgentByName(aname)
        for mv in a.memvars:
            printVar(aname,mv)
    dump( "\\end{longtable}")
outputfile=sys.stdout
if __name__=="__main__":
    print "Usage:\n  %s [outputfile.tex]"%sys.argv[0]
    try:
        outputfile=open(sys.argv[1],"w")
        outputfile.write("\\documentclass{article}\n\\usepackage{longtable}\n\\begin{document}\n")
    except:pass
    popfile=raw_input("Enter the path to population file : ")
    print "Loading population ..."
    pop=pickle.load(open(popfile,"rb"))
    print "Loaded"
    while 1:
        outtype="None"
        while not isValidType(outtype):
            outtype=getRepType()
        if not outtype:
            outputfile.write("\\end{document}\n")
            print "Bye"
            sys.exit(0)
        if outtype=="constants":
            constants(pop)
        elif outtype=="regions":
            regions(pop)
        elif outtype=="memory":
            memory(pop)
        else:
            print "Invalid report type"
    