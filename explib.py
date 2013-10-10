#!/usr/bin/python
"""
  Experiment manager Library for EURACE

  Author: Mehmet Gencer, mgencer@cs.bilgi.edu.tr
          Bulent Ozel, bulent.ozel@gmail.com, Reykjavik University
"""
__docformat__="restructuredtext en"

import sys, os, os.path, pickle
from  poplib import *

MODELSDIR="testdata/models"
XPARSERDIR="xparser"

def debug(msg):
    print msg

def getModelPath(modelname,modeltype):
    return "%s/%s/%s" % (MODELSDIR,modeltype,modelname)

class ExplibException(Exception):
    pass

class SimulationEnvironment:
    """
    Abstraction for the environement where simulations are executed.
    """
    def __init__(self,xparserdir=XPARSERDIR,modelsdir=MODELSDIR):
        self.xparserdir=xparserdir
        self.modelsdir=modelsdir
        if not os.path.exists(self.xparserdir):
            raise ExplibException("Xparser directory not found")
        debug("Checking for xparser executable")
        if not os.path.exists("%s/xparser"%self.xparserdir):
            raise ExplibException("Xparser executable not found")
        debug("OK")

    def checkModel(self,model,modeltype="xmml"):
        debug("Checking if model %s(%s) is ready for execution"%(model,modeltype))
        mdir=getModelPath(model,modeltype)
        if not os.path.exists(mdir):
           raise ExplibException("Model directory not found : %s"%mdir)
        mexec="%s/main"%mdir
        if not os.path.exists(mexec):
           raise ExplibException("Model executable not found : %s"%mexec)
        return 1

    def run(self,modelname,modeltype,startxml,numsteps):
        self.checkModel(modelname,modeltype)
        sxmlpath=os.path.abspath(startxml)
        mdir=getModelPath(modelname,modeltype)
        cmd="cd %s && ./main %d %s" % (mdir,numsteps,sxmlpath)
        print "Executing '%s'"%cmd
        stat=os.system(cmd)
        return stat

SIMENV=SimulationEnvironment()

class Specification:
    def __init__(self,modelname,modeltype="xmml"):
        self.modelname=modelname
        self.modeltype=modeltype
        self.scenarios={}

    def addScenario(self,name,desc="No description"):
        self.scenarios[name]=Scenario(name,self.modelname,self.modeltype,desc=desc)

    def setScenario(self,name,sce):
        self.scenarios[name]=sce

    def delScenario(self,name):
        del self.scenarios[name]

    def getScenario(self,name):
        return self.scenarios[name]
        
    def summary(self):
        rv="Specification Model: %s (%s)\n" % (self.modelname,self.modeltype)
        rv+="Scenarios:\n"
        for s in self.scenarios.keys():
            rv+=self.scenarios[s].summary()
        return rv

class Scenario:
    def __init__(self,name,modelname,modeltype,desc="No Description"):
        self.name=name
        self.desc=desc
        self.modelname=modelname
        self.modeltype=modeltype
        self.pop=None
        try:
            os.mkdir("scenario-%s"%name)
        except:
            pass
        if os.path.exists(self.getPopobjPath()):
            print "Restoring population"
            self.pop=pickle.load(open(self.getPopobjPath(),"rb"))
        else:
            self.pop=Population(self.name,getModelPath(self.modelname,self.modeltype)+"/model.xml")
            persist(self.pop,self.getPopobjPath())
        self.experiments={}

    def getDir(self):
         return "scenario-%s"%self.name

    def getZeroxmlPath(self):
        return "scenario-%s/0.xml"%self.name

    def getPopobjPath(self):
        return "scenario-%s/pop.pyobj"%self.name

    def isReady(self):
        if self.pop:
            return 1
        return 0

    def editPopulationNumAgents(self):
        self.pop.readNumAgents()
        persist(self.pop,self.getPopobjPath())

    def editPopulationInitForms(self):
        self.pop.readInitForms()
        persist(self.pop,self.getPopobjPath())

    def editPopulation(self):
        editpop(self.getDir())

    def createInitState(self):
        self.pop.recreatePop()
        open(self.getZeroxmlPath(),"w").write(self.pop.popToXML())

    def addExperiment(self,name):
        self.experiments[name]=Experiment(self.pop,self.modelname,self.modeltype)

    def setExperiment(self,name,exp):
        self.experiments[name]=exp

    def delExperiment(self,name):
        del self.experiments[name]

    def getExperiment(self,name):
        return self.experiments[name]

    def setExperimentRun(self,expname,runname,numsteps):
        self.experiments[expname].setRun(runname, self.getZeroxmlPath(), numsteps)

    def runExperiment(self,expname):
        self.experiments[expname].runBatch()

    def summary(self):
        rv="Scenario '%s' : %s\n" % (self.name,self.desc)
        rv+="  Experiments:\n"
        for e in self.experiments.keys():
            rv+="    %s : " %e
            for r in self.experiments[e].runs.keys():
                rv+="%s (%d steps) " % (r,self.experiments[e].runs[r].numsteps)
            rv+="\n"
        return rv

class Run:
    """A scenario run"""
    def __init__(self,runname,startxml,numsteps,modelname,modeltype):
        self.name=runname
        self.startxml=startxml
        if not os.path.exists(startxml):
            raise ExplibException("No such start XML : "+startxml)
        self.numsteps=numsteps
        self.modelname=modelname
        self.modeltype=modeltype

    def run(self):
        print "Starting run : ", self.name
        SIMENV.run(self.modelname,self.modeltype,self.startxml,self.numsteps)

class Experiment:
    """A scenario Experiment"""
    def __init__(self,pop,modelname,modeltype="xmml"):
        self.pop=pop
        self.modelname=modelname
        self.modeltype=modeltype
        self.runs={}
        
    def setRun(self,runname,startxml,numsteps):
        """Create or update a run"""
        r=Run(runname,startxml,numsteps,self.modelname,self.modeltype)
        self.runs[runname]=r

    def delRun(self,runname):
        del self.runs[runname]

    def run(self,runname):
        if not self.runs.has_key(runname):
            raise ExplibException("No such run defined: "+runname)
        self.runs[runname].run()

    def runBatch(self):
        for r in self.runs.values():
            r.run()

def persist(x,path):
    pickle.dump(x,open(path,"wb"))

def restore(path):
    return pickle.load(open(path,"rb"))

def test():
    spe=Specification("bielefeld","xmml")
    spe.addScenario("bie-testscenario",desc="test scenario")
    spe.prepareScenarioPopulation("bie-testscenario")
    spe.getScenario("bie-testscenario").addExperiment("testexp")
    spe.getScenario("bie-testscenario").setExperimentRun("testexp","testrun",5)
    spe.getScenario("bie-testscenario").runExperiment("testexp")
    print spe.summary()

if __name__=="__main__":
    test()
