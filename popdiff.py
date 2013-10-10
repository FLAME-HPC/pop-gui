#!/usr/bin/python
"""
    Experiment manager Library for EURACE
    
    Author: Mehmet Gencer, mgencer@cs.bilgi.edu.tr
            Bulent Ozel, bulent.ozel@gmail.com, Reykjavik University
"""

from poplib  import *
setDebug(0)
import sys, pickle
try:
    pop1=pickle.load(open(sys.argv[1],"rb"))
    pop2=pickle.load(open(sys.argv[2],"rb"))
except:
    print "Usage:\n  %s popfile1 popfile2"%sys.argv[0]
    sys.exit(0)
def compareforms(mv1,mv2,aname):
    for i in mv1.initforms.keys():
        if1=mv1.initforms[i]
        try:
            if2=mv2.initforms[i]
        except:
            print "Memvar %s-->%s does not have a component named %s"%(aname,mv2.name,i)
            continue
        #print if1
        if isinstance(if1,MemVar):
            compareforms(if1,if2,aname)
        elif if1.getFormStr()!=if2.getFormStr():
            print "Memvar %s-->%s initform %s differs in pop1 and pop2:\n  pop1: %s\n  pop2: %s"%(aname,mv1.name,i,if1.getFormStr(),if2.getFormStr())
        else:
            pass#print "Memvar %s initform %s same in pop1 and pop2:\n  pop1: %s\n  pop2: %s"%(mv1.name,i,if1.getFormStr(),if2.getFormStr())
        
            
for aname in pop1.model.getAgentNames():
    agent=pop1.getNumberedRegion(0).model.getAgentByName(aname)
    #print "AGENT: ", aname
    for mvname in agent.getMemVarNames():
        mv=agent.getMemVarByName(mvname)
        try:
            a2=pop2.getNumberedRegion(0).model.getAgentByName(aname)
        except:
            print "Perhaps pop2 does not have agent:",aname
            continue
        try:
            mv2=a2.getMemVarByName(mvname)
        except:
            print "Perhaps pop2 doesn't have the memvar: ",aname,mvname
            continue
        compareforms(mv,mv2,aname)
print "Comparison completed"