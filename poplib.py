#!/usr/bin/python
"""
  PopLib : Population management library for EURACE.

  Author(s) : Mehmet Gencer, mgencer@cs.bilgi.edu.tr, TUBITAK-UEKAE
              Bulent Ozel, bulent.ozel@gmail.com, Reykjavik University
"""

__docformat__="restructuredtext en"

import xml.dom.minidom as xmldom
import sys,pickle, os, os.path, random, re, traceback, time,datetime
random.seed()
from math import exp
try:
    import readline
except:
    pass
global DEBUG
global GLOBALMSG
this=None
REPLACEID=""
REGIONREPLACEID=""
def setReplaceId():
    global REPLACEID
    REPLACEID="REPLACE_ID_"
def getReplaceId():
    return REPLACEID
def setRegionReplaceId():
    global REGIONREPLACEID
    REGIONREPLACEID="REPLACE_REGIONID_"
def getRegionReplaceId():
    return REGIONREPLACEID
def resetGlobalMsg():
    global GLOBALMSG
    GLOBALMSG=""
def getGlobalMsg():
    try:
        rv= GLOBALMSG
        resetGlobalMsg()
        return rv
    except:
        return ""
def setDebug(v):
    global DEBUG
    try:
        DEBUG+=v
    except:
        DEBUG=v
    debug( "DEBUGGING LEVEL IS : %d"%DEBUG)
def globalSetNumRegions(n):
    global popguinumregions
    popguinumregions=n
def debug(*args):
    try:
        d=0
        if DEBUG:
            d=1
    except:
        d=1
    if not d:return
    for a in args:
        print a,
    print
def debug2(*args):
    try:
        if DEBUG>=2:
            for a in args:
                print a,
            print
    except:
        pass
class IDReplacer:
    def __init__(self,n,marker):
        self.n=n
        self.marker=marker
    def convert(self,other):
        if isinstance(other,IDReplacer):return other.n
        else:return int(other)
    def __cmp__(self,other):
        #print "*************IDREPLACER CMP",type(other)
        if self.n<self.convert(other):return -1
        elif self.n>self.convert(other):return 1
        return 0
    def __ne__(self,other):
        #print "*************IDREPLACER NE",type(other)
        if self.n==self.convert(other):return False
        return True
    def __eq__(self,other):
        #print "*************IDREPLACER EQ",type(other)
        if self.n==self.convert(other):return True
        return False
    def __str__(self):
        return "%s%d"%(self.marker,self.n)
    def __coerce__(self,other):
        #print "*************IDREPLACER COERCION",type(other)
        if type(other)==float:
            return (float(self.n),other)
        elif type(other)==int:
            return (self.n,other)
        elif type(other)==str:
            return ("%s%d"%(self.marker,self.n),other)
        else:
            #return (self.n,int(other))
            print "IDREPLACER COERSION:",type(other),other.__class_
            raise Exception("Cannot coerce IDReplacer")
    def __int__(self):
        #print "*************IDREPLACER CONVERSION (INT)"
        raise Exception("IDREPLACER TEST")
        return self.n
    def __float__(self):
        return float(self.n)
    
##############################################################
################# UTILITIES ##################################
##############################################################
class MultiDict:
    """A dictionary implementation which allows multiple entries with the same key"""
    def __init__(self,casesens=0):
        self.dic={}
        self.cs=casesens
    def _conv(self,okey):
        if self.cs:
            key=okey
        else:
            try:
                key=okey.lower()
            except:
                key=okey
        return key
    def put(self,okey,val):
        key=self._conv(okey)
        if self.dic.has_key(key):
            self.dic[key].append(val)
        else:
            self.dic[key]=[val]
    def keys(self):
        return self.dic.keys()
    def has_key(self,okey):
        key=self._conv(okey)
        return self.dic.has_key(key)
    def get(self,okey):
        key=self._conv(okey)
        return self.dic[key]
    def getAny(self,okey):
        key=self._conv(okey)
        """Returns an emptry list if no such key is found"""
        if self.dic.has_key(key):
            return self.dic[key]
        else:
            return []
    def getOne(self,okey):
        key=self._conv(okey)
        "if only one value for that key return it, otherwise raise an exception"
        x=self.dic[key]
        if len(x)==1:
            return x[0]
        else:
            raise Exception("Multiple entries %d"%len(x))
    def getOneOrDefault(self,okey,default=""):
        key=self._conv(okey)
        try:
            return self.getOne(key)
        except:
            return default

def getDomAsMultiDict(element,depth=1):
    """turn an XML DOM object into a MultiDict, and return a tuple (roottagname,MultiDictInstance)"""
    rv=MultiDict()
    ln=element.localName
    if element.hasChildNodes():
        for child in element.childNodes:
            x=getDomAsMultiDict(child,depth=depth+1)
            if x:
                n,t=x
                if not type(t)==unicode:
                    k=t.keys()
                    if len(k)==1 and not k[0]:
                        rv.put(n,t.get(k[0])[0])
                    else:
                        rv.put(n,t)
                else:
                    rv.put(n,t)
        return (ln,rv)
    else:
        #if element.nodeType==xmldom.Attr.TEXT_NODE:
        try:
            t= element.data.strip()
            if t:
                #print " "*depth,ln,t
                return (ln,t)
        except:
            return

def reprMultiDictAsTXT(dic,depth=1):
    rv=""
    for k in dic.keys():
        for v in dic.get(k):
            if not type(v)==unicode:
                rv+="%s%s:\r\n" % (depth*"    ",k)
                rv+="%s\r\n"%reprMultiDictAsTXT(v,depth+1)
            else:
                rv+="%s%s : %s\r\n" % ("    "*depth,k,v)
    return rv

##############################################################

##############################################################
################# CLASSES   ##################################
##############################################################
class SpecialVarsGenerator:
    def __init__(self):
        self.idseed=1
        #self.numregions=numregions
        self.specialnames=["id","region_id"]

    def reset(self):
        self.idseed=1

    def isSpecial(self,name):
        if name in self.specialnames:
            return 1
        else:
            return 0

    def generate(self,varname,regionid):
        if varname=="id":
            rv=self.idseed
            self.idseed+=1
            return rv
        elif varname=="region_id":
            if REGIONREPLACEID:
                return IDReplacer(regionid+1,REGIONREPLACEID)
            else:
                return regionid+1#random.randint(1,self.numregions)
        else:
            raise PoplibException("Unknown special variable")

SPECIALVARSGENERATOR=SpecialVarsGenerator()

class PoplibException(Exception):
    pass

class PoplibDependencyException(PoplibException):
    pass
class PoplibInvalidDependencyException(PoplibException):
    pass
class PoplibInvalidSiblingDependencyException(PoplibException):
    pass

class DummyMemVar:
    """
    Dummy memory variable which will return an instance of the same class when a subvar is accessed and will pass for a numeric variable
    """
    def __init__(self,nolengthlimit=0):
        self.parent=None
        self.name="None"
        self.nolengthlimit=nolengthlimit
    def __str__(self):
        return "Dummy"
    def __len__(self):
        if self.nolengthlimit:return 100
        return 1
    def has_key(self,i):
        return 1
    def __getitem__(self,i):
        if type(i)==str:
            return DummyMemVar()
        if i==0 or self.nolengthlimit:
            return DummyMemVar()   
        else:
            raise IndexError("No such element") 
    def __coerce__(self,other):
        #print type(other)
        if type(other)==float:
            return (1.0,other)
        elif type(other)==int:
            return (1,other)
        elif type(other)==list:
            return ([],other)
        else:
            return (1.0,other)
            #debug("Coercion problem:"+str(other))
            #raise PoplibException("Cannot coerce memory variable value to %s"%other.__class__.__name__)#str(type(other)))
    def __int__(self):
        return 1 #to avoid division by zero errors
    def __float__(self):
        return 1.0 # to avoid division by zero errors

class MemVarRegistry:
    """
    Keeps instances of memory variables of an agent and their dependencies.
    An instance of this is intended for use as the global variable 'this' by Agent or AgentInstance during validation or instantiation
    to allow access to other memory variables from within initform of a memory variable.
    """
    def __init__(self,agent,agentinstance,relaxed=0):
        """
        agentinstance can be none for cross-agent dependency checking pahse. in such cases relaxed must also set to 1
        """
        self.agent=agent
        self.agentinstance=agentinstance
        self.relaxed=relaxed
        self.depmap={}
        self.valmap={}
        #self.varorder=[] #the order in which variables must be instantiated to account for referential dependencies
        #self.mode="dummy" #dummy means that a generic object will be returned just to account for dependencies
    
    #def getVar(self,var,fromvar):
    #    return self.getSelfVar(var,fromvar)

    def getNumRegions(self):
        if self.agentinstance==None:
            try:
                global popguinumregions
                return popguinumregions
            except:
                return 1
        else:
            return self.agentinstance.region.parentpop.getNumRegions()
    def getAgentVar(self,var):
        if self.relaxed:
            return DummyMemVar()
        else:
            return self.getSelfVar(var)

    def buildSelfVarDependencies(self):
        #INCOMPLETE
        rexp=re.compile("getSelfVar\([\"\'](.+?)[\"\']\)")
        for m in self.agent.getMemVarNames():
            mv=selg.agent.getMemVarByName(m)
            
    def checkCyclicDep(self,var,acc):
        if self.depmap.has_key(var):
            if var in self.depmap[var]:
                raise PoplibInvalidDependencyException("Invalid dependency: In agent %s variable references itself %s"%(self.agent.name,var))
        if var in acc:
            msg=""
            for a in acc:
                if msg:msg+="-->"
                msg+=a
            msg+="-->"+var
            raise PoplibInvalidDependencyException("Invalid dependency: In agent %s cyclic reference %s"%(self.agent.name,msg))
        if self.depmap.has_key(var):
            for v in self.depmap[var]:
                self.checkCyclicDep(v,acc+[var])
    def getSelfVar(self,var,fromvar=None):
        """
        Get an already instantiated memory variable, or throw a PoplibDependencyException after keeping record of dependency
        when fromvar is None, this is cross-agent access, so no inernal dependency recording is provided
        """
        if self.agent.getMemVarByName(var)==None:
            raise PoplibInvalidDependencyException("No such variable in the agent %s->%s"%(self.agent.name,var))
        if not (fromvar==None):
            if not self.depmap.has_key(fromvar):
                self.depmap[fromvar]=[]
            if var in self.depmap[fromvar]:
                pass
            else:
                self.depmap[fromvar].append(var)
                debug("DDDDDDDDDDDDDDDDDDDDDDDD Adding getSelfVar() dependency %s to %s"%(fromvar,var))
                #checkCyclicDep(var,[])
            fromvarstr=fromvar
        else:
            fromvarstr="None"
        if self.valmap.has_key(var):
            if var=="region_id":
                if REGIONREPLACEID:
                    return  IDReplacer(self.valmap[var]+1,REGIONREPLACEID)
                else:
                    return  self.valmap[var]+1
            else:
                return self.valmap[var]
        else:
            debug("In Agent %s, Dependency not satisfiable: from %s to %s"%(self.agent.name,fromvarstr,var))
            debug("All I know are:%s"%(str(self.valmap.keys())))
            #debug("Agent variable init order: %s"%str(self.agent.getVarInitOrder()))
            raise PoplibDependencyException("Dependency self variable is not satisfiable in agent %s: from variable %s to %s"%(self.agent.name,fromvarstr,var))

    def getAgentRegional(self,aname,conditions=[],exclusive=0,referername="No name",depfinetune=0):
        return self._getAgent(aname,conditions=conditions,exclusive=exclusive,search="region",referername=referername,depfinetune=depfinetune)
    def getAgentGlobal(self,aname,conditions=[],exclusive=0,referername="No name",depfinetune=0):
        return self._getAgent(aname,conditions=conditions,exclusive=exclusive,search="global",referername=referername,depfinetune=depfinetune)
    def getAllAgentsRegional(self,aname,conditions=[],exclusive=0,randomize=1,referername="No name",depfinetune=0):
        return self._getAgent(aname,conditions=conditions,exclusive=exclusive,search="region",multiple=1,randomize=randomize,referername=referername,depfinetune=depfinetune)
    def getAllAgentsGlobal(self,aname,conditions=[],exclusive=0,randomize=1,referername="No name",depfinetune=0):
        return self._getAgent(aname,conditions=conditions,exclusive=exclusive,search="global",multiple=1,randomize=randomize,referername=referername,depfinetune=depfinetune)
    def getAgentIDListRegional(self,*args):
        idlist=[]
        if self.agentinstance==None: #dependency recording only, produce phony list:
            for aname in args:
                #self.agent.addDependence(aname,"region")#for registering dependency only
                num=self.agent.model.getRegionalAgentCount(aname)
                for i in range(num):
                    idlist.append(0)
        else:
            for aname in args:
                idlist.extend(self.agentinstance.region.getAgentIDListRegional(aname))#idlist.extend(self._getAgent(aname,search="region",getidlist=1))
        return idlist
    def getAgentIDListGlobal(self,*args):
        idlist=[]
        if self.agentinstance==None: #dependency recording only, produce phony list:
            for aname in args:
                #self.agent.addDependence(aname,"global")#for registering dependency only
                num=self.agent.model.getGlobalAgentCount(aname)
                for i in range(num):
                    idlist.append(0)
        else:
            for aname in args:
                idlist.extend(self.agentinstance.region.getAgentIDListGlobal(aname))#idlist.extend(self._getAgent(aname,search="global",getidlist=1))
        return idlist
    def getAgentByID(self,aname,ID):
        ag=self.agent.model.getAgentByName(aname)
        if self.agentinstance==None:#special case for dependency recording only
            return MemVarRegistry(ag,None,relaxed=1)
        else:
            self.agentinstance.region.parentpop.getAgentByID(ID)
    def _getAgent(self,aname,conditions=[],exclusive=0,search="",getidlist=0,multiple=0,randomize=1,referername="No name",depfinetune=0):
        """
        Returns memvarregistry of the selected agent from the same region
        conditions is a list of condition checking lambda functions with return value true or false
        search parameter should be one of "regional" or "global"
        Turning on the "getidlist" option changes the behavior to returning list of ids of all mathcing agents. Be careful
        if you use this option with exclusive!
        If multiple flag is turned on returns all matching agents' memvarregistries as a list
        """
        if multiple and exclusive:
            raise PoplibException("You cannot exlusively get all agents at once. Exlusive get is only allowed for single agent choosing")
        idlist=[]
        retval=[]
        if aname==self.agent.name:
            raise PoplibInvalidDependencyException("getAgent() Dependency not satisfiable in agent %s: reference to same agent not acceptable"%(self.agent.name))
        ag=self.agent.model.getAgentByName(aname)
        if ag==None:
            raise PoplibInvalidDependencyException("getAgent() Dependency not satisfiable. Referred agent class '%s' does not exist: in agent %s"%(aname,self.agent.name))
        if self.agentinstance==None:#special case for dependency recording only
            ar= MemVarRegistry(ag,None,relaxed=1)
            self.agent.addDependence(aname,search,referername=referername,depfinetune=depfinetune)
            if getidlist:
                return idlist
            else:
                if multiple:
                    return [ar]
                else:
                    return ar
        else:
            satisfied=0
            result=None
            if search=="region":
                candidates=self.agentinstance.region.popmap[aname]
            elif search=="global":
                candidates=self.agentinstance.region.parentpop.popmap[aname]
            else:
                raise PoplibException("search parameter value '%s' is unknown in _getAgent()"%search)
            if randomize:
                candidates=random.sample(candidates,len(candidates))
            for x in candidates:
                if exclusive and x.exclusivelytaken:
                    continue
                passed=1
                for cp in conditions:
                    v,c=cp
                    val=x.varreg.getAgentVar(v)
                    try:
                        debug2(val)
                        debug2(c)
                    except:pass
                    if c(val):
                        passed=1
                    else:
                        passed=0
                    #exec("if %s %s:passed=1"%(val,c))
                    if not passed:break
                if not passed:
                    continue
                else:
                    satisfied=1
                    result=x
                    if not getidlist:
                        if multiple:
                            retval.append(result.varreg)
                        else:
                            break
                    else:
                        idlist.append(x.varreg.getAgentVar("id"))
            if multiple:
                return retval
            if satisfied:
                if exclusive:
                    result.exclusivelytaken=1
                if not getidlist:
                    try:
                        return result.varreg
                    except:
                        debug("Error in _getAgent from %s to %s: %s"%(self.agent.name, aname,result))
                        raise Exception("There is possibly a bug in the program and agent initialization order is wrong. Error in _getAgent from %s to %s"%(self.agent.name, aname))
                else:
                    return idlist
            else:
                if getidlist:
                    return idlist
                else:
                    raise PoplibException("Agent with given conditions cannot be found: in agent %s, seeking agent %s"%(self.agent.name,aname))

class DataType:
    """Represents a data type definition of model environment"""
    def __init__(self,name,desc):
        self.name=name
        self.desc=desc
        self.vars={} # a dict of varname:{"type":int or double, "desc":description text}
        self.varorder=[]

class Agent:
    def __init__(self,model,name,desc):
        self.model=model
        self.name=name
        self.desc=desc
        self.memvars=[]
        self.memvarorder=[]
        self.depends=[] # list of agents on which the agent depends upon because of getAgent() calls in memvar initializations
        self.globaldepends=[]
        self.dependencereferers={}
    def reportDependencyProblems(self):
        for aname in self.depends:
            if self.name in self.model.getAgentByName(aname).depends or self.name in self.model.getAgentByName(aname).globaldepends:
                raise PoplibInvalidDependencyException("Cyclic Regional dependency %s --> %s"%(self.name,aname))
        for aname in self.globaldepends:
            if self.name in self.model.getAgentByName(aname).depends or self.name in self.model.getAgentByName(aname).globaldepends:
                raise PoplibInvalidDependencyException("Cyclic Global dependency %s --> %s"%(self.name,aname))
    def getFineDependencies(self):
        try:
            return self.finedependencies
        except:
            self.finedependencies=[]
            return self.finedependencies
    def addFineDependence(self,depfinetune):
        self.getFineDependencies().append(depfinetune)
    def addDependence(self,aname,scope,referername="No name",depfinetune=0):
        """
        Update agent dependencies so that it depends on the named agent
        scope can be "global" (ie coming from getAgentGlobal() or "regional" (coming from getAgentRegional)
        """
        if depfinetune:
            frommemvar,deptype,toagentname,tomemvarname,delay=depfinetune
            print "!!!!!!! Attempting dependency fine tuning:",self.name,frommemvar.name,deptype,toagentname,tomemvarname,delay
            if self.name!=frommemvar.agent.name:
                msg= "You may have a mistake in dependencyFineTuning. It indicates dependency from %s-->%s but you are inside agent %s !!"%(frommemvar.agent.name,frommemvar.name,self.name)
                print msg
                raise PoplibException(msg) 
            self.addFineDependence(depfinetune)
            return
        if not (aname in self.depends):
            self.depends.append(aname)
            print "Agent Regional dependency %s (%s) --> %s"%(self.name,referername,aname)
        if scope=="global":
            if not (aname in self.globaldepends):
                self.globaldepends.append(aname)
                print "Agent Global dependency %s (%s) --> %s"%(self.name,referername,aname)
        if not self.dependencereferers.has_key(aname):self.dependencereferers[aname]=[]
        if not referername in self.dependencereferers[aname]:
            self.dependencereferers[aname].append(referername)
        #self.reportDependencyProblems()
        #self.model.region.parentpop.getInitializationOrder()
    def getMemVarRegistry(self,reset=0):
        if reset:
            self.memvarreg=MemVarRegistry(self,None,relaxed=1)
        try:
            return self.memvarreg
        except:
            self.memvarreg=MemVarRegistry(self,None,relaxed=1)
            return self.memvarreg

    def getVarInitOrder(self,check=1):
        """
        Determine memvar initialization order by looking at dependencies
        """
        reg=self.getMemVarRegistry()
        varnames=self.getMemVarNames()
        if check and len(reg.valmap)<len(varnames):
            raise PoplibException("Agent memory initforms were not checkd for referential dependencies. This must be done before I can produce an initialization order")
        varorder=[]
        def pushVar(v):
            if reg.depmap.has_key(v):
                for d in reg.depmap[v]:
                    pushVar(d)
            if not (v in varorder):
                varorder.append(v)
        for von in self.memvarorder:#varnames:
            m=self.getMemVarByOriginalName(von)
            pushVar(m.name)
        self.varinitorder=varorder
        #debug("#######################  VARINITORDER FOR AGENT : %s ##################"%self.name)
        #debug(str(varorder))
        #debug(str(self.depmap))
        return varorder
            
    def validateReferenceDependencies(self,use=""):
        """
        validate reference dependencies to make sure there are no cyclic dependencies 
        and also make an ordering of the variable initializations.
        If 'use' is 'candidates' candidate forms are used, otherwise saved forms are used
        """
        global this
        self.depends=[]
        self.globaldepends=[]
        self.finedependencies=[]
        this=self.getMemVarRegistry(reset=1)
        goon=1
        #repass=0
        l=len(this.valmap)
        its=0
        debug("VALIDATE REFERENCE DEPENDENCIES: Using '%s'"%use)
        def tryout(mv,noraise=0):
            try:
                if use=="candidates":
                    mv.validateForms(use=use)
                    this.valmap[mv.name]=DummyMemVar()
                else:
                    tmp=mv.instantiate(0,regionid=0,validateOnly=1)
                    this.valmap[mv.name]=tmp
            except PoplibInvalidDependencyException:
                i=sys.exc_info()
                debug("Dependency validation exception: %s\n%s"%(i,traceback.print_tb(i[2])))
                raise PoplibException("Dependency validation exception in agent %s in variable %s: \n%s"%(self.name,mv.name,i[1]))
                #raise PoplibException(i)
            except PoplibDependencyException:#when this is thrown, dependency is already registered in MemVarRegistry instance
                debug("CHAINING: %s --> %s"%(mv.name,this.depmap[mv.name]))
                this.checkCyclicDep(mv.name,[])
                for x in this.depmap[mv.name]:
                    tryout(self.getMemVarByName(x))
                return
                #break
                if noraise:
                    pass
                else:
                    raise
        while goon:# or repass:
            its+=1
            #repass=0
            for mv in self.memvars:
            #for mvoname in self.getVarInitOrder(check=0):
            #    mv=self.getMemVarByName(mvoname)
                try:
                    #if use=="candidates":
                    #    mv.validateForms(use=use)
                    #    this.valmap[mv.name]=DummyMemVar()
                    #else:
                    #    tmp=mv.instantiate(0,regionid=0,validateOnly=1)
                    #    this.valmap[mv.name]=tmp
                    getGlobalMsg()
                    tryout(mv)
                #except PoplibInvalidDependencyException:
                #    i=sys.exc_info()
                #    debug("Dependency validation exception: %s\n%s"%(i,traceback.print_tb(i[2])))
                #    raise PoplibException("Dependency validation exception in agent %s in variable %s: \n%s"%(self.name,mv.name,i[1]))
                #    #raise PoplibException(i)
                except PoplibDependencyException:#when this is thrown, dependency is already registered in MemVarRegistry instance
                    #tryout(self.getMemVarByName(this.depmap[mv.name][-1]),noraise=1)
                    #break
                    resetGlobalMsg()
                    break
            #if l<len(this.valmap):
            #    l=len(this.valmap)
            #else:
            #    goon=0
            if len(self.memvars)==len(this.valmap):
                goon=0
        for mv in self.memvars:
            this.checkCyclicDep(mv.name,[])
        isok=1
        if len(this.valmap)!=len(self.memvars):
            debug("Some variables couldn't be instantiated")
            isok=0
        debug("AGENT:%s, Num iterations %d"%(self.name,its))
        for mv in self.memvars:
            if this.valmap.has_key(mv.name):
                hasit="yes"
            else:
                hasit="no"
            depends=""
            if this.depmap.has_key(mv.name):
                depends=str(this.depmap[mv.name])
            #debug("%s - %s - %s"%(mv.name,hasit,depends))
        this=None
        if not isok:
            raise PoplibInvalidDependencyException("There are possibly cyclic references in agent %s"%self.name)
        #debug("Variable initialization order:")
        debug("#######################  VARINITORDER FOR AGENT : %s ##################"%self.name)
        debug(str( self.getVarInitOrder()))
        debug("(DEPENDENCIES:"+str(self.memvarreg.depmap)+")")

    def getMemVarByName(self,mvname):
        #debug("AgentMemVar attempting",mvname)
        for mv in self.memvars:
            if mv.name==mvname:
                return mv
        return None
    def getMemVarByOriginalName(self,mvname):
        #debug("AgentMemVar attempting",mvname)
        for mv in self.memvars:
            if mv.originalname==mvname:
                return mv
        return None
    def getMemVarNames(self):
        n=[]
        for mv in self.memvars:
            n.append(mv.name)
        return n

#############################################################################################################
#############################################################################################################
##################################   MEMVAR   ###############################################################
#############################################################################################################
#############################################################################################################
class BaseForm:
    def __init__(self,vtype,parent=None,name=None):
        self.form="0"
        self.vtype=vtype
        self.parent=parent
        self.name=name
    def getName(self):
        if self.parent==None:
            return self.name
        else:
            return self.parent.name+"."+self.name
    def setFormStr(self,form):
        self.form=form
    def getFormStr(self):
        return self.form
    def validate(self,form):
        return self._instantiate(form,siblings=DummyMemVar(nolengthlimit=1))

    def instantiate(self,sequenceno=0,siblings=[]):
        return self._instantiate(self.form,fixtype=1,sequenceno=sequenceno,siblings=siblings)

    def _convert(self,what,totype):
        if type(what)==list:
            retval=[]
            for w in what:
                retval.append(self._convert(w,totype))
        else:
            retval=totype(what)
        return retval

    def _getRootMemvar(self):
        root=self.parent
        while root.parent!=None:
            root=root.parent
        return root

    def _instantiate(self,form,fixtype=0,sequenceno=0,globalmsgreg=1,usealternatethis=0,alternatethis=None,siblings=[]):
        """
        if strict, then check types
        if fixtype, then do int/double conversion if necessary
        """
        if usealternatethis:
            global this
            this=alternatethis
        if self.vtype=="int":
            rand=random.randint
        else:
            rand=random.uniform
        choice=random.choice
        normal=random.normalvariate
        sample=random.sample
        global depfinetune
        depfinetune=0#dependency fine tuning
        def delayedExecution(expr,getlocals=locals(),delay=1):
            global depfinetune
            depfinetune=(self._getRootMemvar(),None,None,None,delay)
            getlocals["depfinetune"]=depfinetune
            #print "IN DEPFINETUNE",getlocals
            try:
                retval=eval(expr,globals(),getlocals)
            except:
                raise
            finally:
                depfinetune=0
            return retval
        def dependencyFineTune(deptype,toagentname,tomemvarname,expr,getlocals=locals(),delay=1):
            global depfinetune
            depfinetune=(self._getRootMemvar(),deptype,toagentname,tomemvarname,delay)
            getlocals["depfinetune"]=depfinetune
            #print "IN DEPFINETUNE",getlocals
            try:
                retval=eval(expr,globals(),getlocals)
            except:
                raise
            finally:
                depfinetune=0
            return retval
        def permutation(l):
            x=l
            random.shuffle(x)
            return x
        def discrete(*l):
            sump=0.0
            for p,v in l:
                sump+=p
            if sump!=1.0:
                raise PoplibException("The discrete probability list does not add up to 1.0 probability: %s"%str(l))
            sump=0.0
            point=random.random()
            for p,v in l:
                if point>=sump and point < sump+p:
                    return v
                sump+=p
        #sequence=lambda j,k,l:range(j,k+1,l)
        def sequence(j,k,l):
            return range(j,k+1,l)
        
        def repeat(v,n):
            return [v for i in range(1,n+1,1)]
        def realsequence(x,y,s):
            retval=[]
            c=float(x)
            while c<=y:
                retval.append(c)
                c+=s
            return retval
        def getSelfVar(v):
            return this.getSelfVar(v,self._getRootMemvar().name)
        def getSibling(s,level=0):
            if not siblings:raise PoplibInvalidSiblingDependencyException("No known siblings")
            elif len(siblings)<level:raise PoplibInvalidSiblingDependencyException("No siblings at given level")
            elif siblings[level].has_key(s):
                if not siblings[level][s]==None:return siblings[level][s]
            raise PoplibInvalidSiblingDependencyException("Cannot retrieve sibling '%s'. Either no such sibling, or violation of initialization order. Known siblings are %s"%(s,siblings))
        def getAgentRegional(a,conditions=[],exclusive=0):
            return this.getAgentRegional(a,conditions=conditions,exclusive=exclusive,referername=self.getName(),depfinetune=depfinetune)
        def getAgentGlobal(a,conditions=[],exclusive=0):
            return this.getAgentGlobal(a,conditions=conditions,exclusive=exclusive,referername=self.getName(),depfinetune=depfinetune)
        def getAllAgentsRegional(a,conditions=[],exclusive=0,randomize=1):
            return this.getAllAgentsRegional(a,conditions=conditions,exclusive=exclusive,randomize=randomize,referername=self.getName(),depfinetune=depfinetune)
        def getAllAgentsGlobal(a,conditions=[],exclusive=0,randomize=1):
            return this.getAllAgentsGlobal(a,conditions=conditions,exclusive=exclusive,randomize=randomize,referername=self.getName(),depfinetune=depfinetune)
        def equals(what):
            return lambda x:x==what
        def subequals(sub,what):
            return lambda x:x[sub]==what
        def subsubequals(sub,sub2,what):
            try:
                debug2(x)
                try:debug2(x.keys())
                except:pass
                debug2(x[sub])
                try:debug2(s[sub].keys())
                except:pass
            except:pass
            return lambda x:x[sub][sub2]==what
        def between(a,b):
            return lambda x:x>=a and x<=b
        def contains(x):
            return lambda l: x in l
        def MooreNeighbour(ncols,no):
            return lambda x:abs((x-1)%ncols-(no-1)%ncols)<=1 and abs((x-1)/ncols-(no-1)/ncols)<=1 and x!=no
        def getConstant(cname):
            c= self.parent.model.getConstantByName(cname)
            if c==None:
                raise PoplibException("Cannot find constant in the model: %s"%cname)
            try:
                retval=eval(c.getValue()) #hack to fix initiallly assigned string "0" for constants of unknown nature
            except:
                retval=c.getValue()
            return retval
        def getAgentCount(aname):
            return self.parent.model.getGlobalAgentCount(aname)
        def getAgentCountGlobal(aname):
            return self.parent.model.getGlobalAgentCount(aname)
        def getAgentCountRegional(aname):
            return self.parent.model.getRegionalAgentCount(aname)
        def getNumRegions():
            return this.getNumRegions()
        def deterministic(min,max,function):
            if max<min:
                raise PoplibException("Max value is less than Min value in deterministic initialization")
            vrange=int(max)-int(min)+1
            pos=sequenceno%vrange+min
            return function(pos)
        def getAgentIDListRegional(*args):
            return this.getAgentIDListRegional(*args)
        def getAgentIDListGlobal(*args):
            return this.getAgentIDListGlobal(*args)
        def getAgentByID(aname,ID):
            return this.getAgentByID(aname,ID)
        #v=eval(form)
        try:
            resetGlobalMsg()
            v=eval(form)
        except:
            if globalmsgreg:
                i=sys.exc_info()
                msg="initform instantiation exception in memvar %s, agent %s\n initform was: %s\n%s\n%s"%(self._getRootMemvar().name,self._getRootMemvar().agent.name,form,i,traceback.print_tb(i[2]))
                debug2(msg)
                global GLOBALMSG
                GLOBALMSG=msg
            raise #PoplibException("initform instantiation exception in memvar %s, agent %s\n initform was: %s\n%s"%(self._getRootMemvar().name,self._getRootMemvar().agent.name,form,i[1]))
        #    raise Exception(msg)
        #fix integer values entered for double, or vice verse
        if fixtype:
            if self.vtype=="int":
                if REPLACEID or REGIONREPLACEID:
                    try:
                        v=self._convert(v,int)
                    except:
                        v=self._convert(v,str)
                else:
                    v=self._convert(v,int)
            elif self.vtype=="double" or self.vtype=="float":
                v=self._convert(v,float)
            if type(v)==list:#INDICATES AN ARRAY INITIALIZATION IS ENABLED
                debug("TODO: LIST INITIALIZATION in memvar %s, form %s"%(self._getRootMemvar().name,self.form))
                debug(v)
            else:
                if not type(v) in [str,int,float]:
                    raise PoplibException("The instantiated value has an invalid type: %s (%s)"%(v,type(v)))
        return v

class BaseFormStatic(BaseForm):
    def validate(self,form):
        return self._instantiate(form)
    def instantiate(self,sequenceno=0):
        return self._instantiate(self.form,fixtype=0,sequenceno=sequenceno)
    def _instantiate(self,form,fixtype=0,sequenceno=0):
        debug("STATIC INSTANCE",self.parent.name)
        return eval(self.parent.static)
    def getFormStr(self):
        return str(self._instantiate(""))

class BaseFormConstant(BaseForm):
    def validate(self,form):
        return self._instantiate(form)
    def instantiate(self,sequenceno=0):
        return self._instantiate(self.form,fixtype=0,sequenceno=sequenceno)
    def _instantiate(self,form,fixtype=0,sequenceno=0):
        debug("CONSTANT INSTANCE",self.parent.static.name)
        try:
            v=eval(self.parent.static.getValue())
            return v
        except:
            raise PoplibException("Error using constant value '%s' (%s)"%(self.parent.static.name,self.parent.name))
    def getFormStr(self):
        return str(self._instantiate(""))

class OrderedDict(dict):
    """
    The original dict returns values() in random order. This class returns them in insertion order, which was needed for structures as memory variables.
    """
    def __init__(self):
        dict.__init__(self)
        self.keyorder=[]
    def __setitem__(self,key,value):
        dict.__setitem__(self,key,value)
        if not (key in self.keyorder):
            self.keyorder.append(key)
    def values(self):
        retval=[]
        for k in self.keyorder:
            retval.append(dict.__getitem__(self,k))
        return retval
class MemVar:
    help="""You can use the following initialization forms in setting up agent memory variables:
   constant : a numeric or character constant or arithmetic expression such as 2, 3.14, 2*2+3, 'abc'. The expressions can indeed be any valid Python expression such as 2**16 or "abc"*4. 
   rand(int,int): a random integer from the inclusive range.
   rand(real,real): a random real number from the range.
   choice([v1,v2,...]): Choose a value from the list randoly.
   normal(mu, sigma): Normal distribution. mu is the mean, and sigma is the standard deviation.
   discrete( (probability,value), (probability,value),... ): Choose value given discrete probabilities. Probabilities must add up to 1.0.
You can combine any of the above in arithmetic expressions, e.g. '2+rand(0,5)', etc.
Please note that discrete versions of random distributions are automatically chosen during instantiation. 

You can also access constants and size of the population:
   getConstant(constantname): e.g. getConstant("alpha") to retrieve the value of constant.
   getAgentCount(agentname): get global agent count
   getAgentCountRegional(agentname): get regional agent count

One function is provided for deterministic initialization:
   deterministic(min,max, lambda function):  assign values by taking one value at a time from inclusive range and applying function to selected value. Min and Max must be integer, and Max must be greater than Min.
    e.g. deterministic(0,10,lambda x:x*10) will initialize as
      agent[0]=0
      agent[1]=10
      ...
      agent[10]=100
      agent[11]=0
      ...

For initializing arrays, one can initialize all the elements of the array at once, by using an initialization form that generates a list of values, instead of a single value:
    constant lists: [1, 2, 3, ...]
    sample([1,2,3,...],k) : Return a k length list of unique elements chosen from the sequence. Used for random sampling without replacement
    permutation([x,y,z,...]) : Shuffle the elements of the list.
    sequence(start,end,increment): generate a sequence of integers with given increment within the inclusive interval: [start, start+increment, start+2*increment, ..., END] where END<=end.
    realsequence(start,end,increment): generate a sequence of real numbers
REFERENCING GLOBAL PROPERTIES:
    getNumRegions() : Return the number of regions in the population
REFERENCING VARIABLES:
If you want to refer to other memory variables of the agent, a function named 'getSelfVar()' is provided. For example 'getSelfVar("id")' will return the id of agent. However, if the memory variable referred to is an array or a composite type, rather than a simple variable, one can refer to its elements as below:
    getSelfVar("somearray")[0] --> returns first (zero indexed) element of array variable.
    getSelfVar("somecomposite")["x"] --> returns field named 'x' of the composite variable
    getSelfVar("somecomposite")["x"][1] --> if field "x" is an array, returns its second element
and so on.
When variable referencing is used, PopGUI will impose strict dependency conditions. getSelfVar() can only refer to top level memory variables (since reference to their elements or fields use the above syntax), and a variable cannot use getSelfVar() to refer to itself. Therefore it is not possible to refer to sibling fields of a data structure, or middle level variables in a deeply nested structure using this function. In order to do that, use the following:
    getSibling("sibling variable name")
If the referred variable is higher up inside the ADT structure (say an uncle rather than a sibling), use the 'level'
parameter to indicate how many levels to climb up (it defaults to 0, i.e. the siblings literally)
    getSibling("some variable name", level=1)
    
REFERENCING OTHER AGENTS:
It is also possible to refer to other agents. This is done using conditional selection of agents, rather than using agent ids. In order to
select an agent one can use getAgentRegional(agentname) or getAgentGlobal(agentname), where the former selects a random agent whose name is given, from the same region with the referring agent, the latter selects one from all population. 
Both variants can be provided with conditions on the agent to be selected using the following format:
   getAgentRegional("Bank",conditions=[("gives_credit",equals(1)),("bad_reputation",equals(0),...])
Please note that conditions is a list of tuples (variable_name,condition). Variable name must be a variable of the selected agent class, and condition is one of the special functions defined. These functions can be one of the following:
   equals(what): is the value of selected variable equals  to the value
   between(a,b): is the value of selected variable within the range
   contains(x): is the value of selected variable (which must be a list) contains the value
   MooreNeighbour(numcolumns,no): checks whether the variable (an integer) is in the Moore neighbourhood of "no" in a geography where regions are laid out in rows with a width of 'numcomulmns'. For example if there are 9 regions laid out as follows:
      1    2    3
      4    5    6
      7    8    9
    then neighbours of region 1 are 2,5,4, whereas neighbours of region 5 are1,2,3,4,6,7,8,9, etc.

Two similar functions get a list of all agents that satisfy the conditions:
   getAllAgentsRegional(...)
   getAllAgentsGlobal(...)
The parameters are similar to getAgentRegional(), however what is returned is a list. Therefore if you need to process specific variables of these agents, do as in the following example:
   sum([a.getAgentVar("x") for a in getAllAgentsRegional("Bank",conditions=[("gives_credit",equals(1)),("bad_reputation",equals(0),...])])
The getAllAgentsRegional(...) and getAllAgentsGlobal(...) have an optional parameter to turn of randomization of ordering of returned agent list. For example:
   getAllAgentsRegional("Firm",randomize=0)
will always return the same list in the same order whenever it is called.

One can use a valid expression as a parameter to these functions. For example equals(getSelfVar("id")) will work. 
Furthermore conditions can be defined as so called lambda functions in Python language, such as  "lambda x: x<100 and x>=5":
   getAgentRegional("Employee",conditions=[("skill",lambda skill:skill<100 and skill>50)])
(NOTE: Since Lambda functions are evaluated in the local context, some difficulties arise. For example:
    lambda x:x["somesub"]==getSelfVar("id")
  will fail to find getSelfVar("id") as it will not be evaluated until the lambda function is used. There is no general
  solution to the problem. However we have introduced some functions to overcome the difficulties in the above example:
    subequals(sub,what): checks if x[sub]==what
    subsubequals(sub1,sub2,what): check if x[sub1][sub2]==what
    )

Once an agent is selected, its variables can be accessed using getAgentVar(variablename). For example:
  getAgentGlobal("Bank",conditions=[("region_id",MooreNeighbour(10,getSelfVar("region_id"))]).getAgentVar("id")
and if the selected variable is a struct or a list, its elements can be accessed using a syntax similar to the examples given for getSelfVar().
Finally if one wishes to prevent others from selecting the same agent, it is possible to do so by setting the 'exclusive' flag to 1 in getAgent variants, i.e:
   getAgentRegional("Employee",exclusive=1)
Once you do this, the selected employee will never be selected again. However one must be careful since it is possible, depending on the composition of the population, that such conditions may not be satisfied once all agents are taken.

Two additional functions allow shortcut access to list of agent IDs to ease syntax since this is a frequently encountered situation:
   getAgentIDListRegional(agentname, agentname, ...)
   getAgentIDListGlobal(agentname, agentname, ...)
both functions will return IDs of all listed agent types in the regional or global population, respectively.

NOTE ABOUT DEPENDENCIES:
 The group of functions getAgentGlobal/Regional() and getAllAgentsGlobalRegional() create a dependency between agents.
 In some cases this creates cyclic dependencies which cannot be resolved by the PopGUI. If desired you can
 solve such situations by using one of the following:
   delayedExecution("some expression"): the expression is executed after all agents and their variables are executed. 
 to evoid syntax errors due to quotes in your own expressions, use long string syntax in Python by putting
 your expression in triple quotes. e.g.:
   delayedExecution(\"""getAgentGlobal("Bank").getAgentVar("id")\""")
 
 Another function is available to fine tune dependencies at the level of variables instead of agents:
   dependencyFineTune(type,toagent,tomemvar,expression)
e.g.:
   dependencyFineTune("Global","Government","gov_id",\"""getAgentGlobal("Government",conditions=[("regions",MooreNeighbour(3,getSelfVar("region_id")))]).getAgentVar("gov_id")   
"""
    types=["int","double","float","char"]
    def __init__(self,name,type,desc,model,agent=None,parent=None):
        self.model=model
        self.parent=parent
        self.agent=agent
        self.name=name
        self.static=0
        self.originalname=name
        self.originaltype=type
        if type[-6:]=="_array" or type[-6:]==" array":#HACK FOR NEW XMML EXAMPLE
            self.isarray=1
            self.type=type[:-6]
        else:
            self.isarray=0
            self.type=type
        search=re.compile("\[.+\]")
        finded=search.findall(type)
        if finded:
            self.isarray=1
            self.type=type[:type.find(finded[0])]
            try:
                #self.static=eval(finded[0])[0]
                eval(finded[0])[0]
                self.static=finded[0][1:-1]
            except:#POSSIBLY A CONSTANT
                tmp=finded[0][1:-1]
                if tmp in self.model.getConstantNames():
                    self.static=self.model.getConstantByName(tmp)
                else:
                    raise PoplibException("Array length is a constant but it is not found in the model: Agent %s, Memory variable:%s, constant:%s"%(agent.name,name,tmp))
                
        #HACK for when variable name, not type, indicates it is an array
        finded=search.findall(name)
        if finded:
            self.isarray=1
            self.name=name[:name.find(finded[0])]
            try:
                #self.static=eval(finded[0])[0]
                eval(finded[0])[0]
                self.static=finded[0][1:-1]
            except:#POSSIBLY A CONSTANT
                tmp=finded[0][1:-1]
                if tmp in self.model.getConstantNames():
                    self.static=self.model.getConstantByName(tmp)
                else:
                    raise PoplibException("Array length is a constant but it is not found in the model: Memory variable:%s, constant:%s"%(name,tmp))
        self.desc=desc
        #self.initform=InitForm(self.name,self.type,self.isarray,self)
        self.initforms={}
        if not self.isSimple():
            for k in self.getKeys():
                vname,vtype=k
                tmpmv=MemVar(vname,vtype,"no desc",model,agent=agent,parent=self)
                if tmpmv.isSimple():
                    #debug("InitForm NOT RECURSING into ",vname,vtype)
                    if tmpmv.static:
                        if isinstance(tmpmv.static,Constant):
                            self.initforms[vname]=BaseFormConstant(vtype,parent=self,name=vname)
                        else:
                            self.initforms[vname]=BaseFormStatic(vtype,parent=self,name=vname)
                    else:
                        self.initforms[vname]=BaseForm(vtype,parent=self,name=vname)
                else:
                    debug("InitForm RECURSING into ",vname,vtype)
                    self.initforms[vname]=tmpmv
                    #self.initforms[tmpmv.name]=tmpmv#HACK
                    #self.info[tmpmv.name]=tmpmv
        else:#SIMPLE
            for k in self.getKeys():
                vname,vtype=k
                if self.static:
                    if isinstance(self.static,Constant):
                        self.initforms[vname]=BaseFormConstant(vtype,parent=self,name=vname)
                    else:
                        self.initforms[vname]=BaseFormStatic(vtype,parent=self,name=vname)
                else:
                    self.initforms[vname]=BaseForm(vtype,parent=self,name=vname)
        if self.static:
            if isinstance(self.static,Constant):
                self.initforms["array length"]=BaseFormConstant("",parent=self)
            else:
                self.initforms["array length"]=BaseFormStatic("",parent=self)
        if self.isSpecial():
            self.initforms[self.name]=BaseForm("",parent=self)

    def getForm(self,field):
        if self.hasKey(field):
            #debug(self.initforms.keys())
            #if self.isSpecial():debug("RETRIEVING INITFORM %s"%self.name)
            return self.initforms[field]
        else:
            debug(self.getKeys())
            raise PoplibException("Memory Variable %s->%s has no key %s"%(self.agent.name,self.name,field))

    def setForm(self,field,val):
        if self.hasKey(field):
            self.initforms[field].setFormStr(val)
        else:
            raise PoplibException("Memory Variable %s->%s has no key %s"%(self.agent.name,self.name,field))

    def isSimple(self):
        if self.isarray or not (self.type in MemVar.types):return 0
        return 1

    #def __str__(self):
    #    if self.isarray:
    #        return "%s(ARRAY of %s)"%(self.name,self.type)
    #    else:
    #        return "%s(%s)"%(self.name,self.type)

    def isSpecial(self):
        """Some root level memory variables are special and do not use initforms"""
        if self.parent==None:
            return SPECIALVARSGENERATOR.isSpecial(self.name)
        else:
            return 0

    def getTypeStr(self):
        rv=""
        if self.isarray:rv+="array of "
        if not (self.type in MemVar.types):rv+=""#composite data type "
        rv+=self.type
        return rv

    def isComposite(self):
        if not (self.type in MemVar.types):return 1
        return 0

    def hasKey(self,key):
        if key in self.getKeyNamesOnly():
            return 1
        return 0

    def getKeys(self):
        """get a list of key names needed to complete this initform, in the form of a list of (keyname,type) tuples where type is int or double"""
        if self.isSpecial():
            return [(self.name,self.type)]
        elif self.isSimple():
            keys=[(self.name,self.type)]
        else:
            keys=[]
            if self.isarray:
                keys.append(("array length","int"))
            if self.type in MemVar.types:
                keys.append((self.name,self.type))
            else:#COMPOSITE
                mydt=self.model.getDatatypeByName(self.type)
                if mydt==None:
                    print "Unknown data type: %s. Here are all I know:"%self.type
                    for dt in self.model.datatypes:
                        print "   ",dt.name
                    raise PoplibException("Unknown data type in agent '%s' memory variable '%s': '%s'"%(self.agent.name,self.name,self.type))
                #for v in mydt.vars.keys():
                for v in mydt.varorder:#s.keys():
                    keys.append((v,mydt.vars[v]["type"]))
        return keys
               
    def getKeyNamesOnly(self):
        names=[]
        for v in self.getKeys():
            n,t=v
            names.append(n)
        return names

    def getOrderedDatatypeKeyNames(self):
        mydt=self.model.getDatatypeByName(self.type)
        return mydt.varorder

    def getCandidates(self):
        try:
            return self.candidates
        except:
            self.candidates={}
            return self.candidates

    def setCandidate(self,field,val):
        self.getCandidates()[field]=val

    def validateForms(self,use=""):
        """
        Validates if candidate forms are valid
        """
        #for f in self.getCandidates().keys():
        #    self.validateForm(f,self.getCandidates()[f])
        if use=="candidates":
            for i in self.initforms.keys():
                if self.getCandidates().has_key(i):
                    self.validateForm(i,self.getCandidates()[i])
                elif isinstance(self.initforms[i],MemVar):#RECURSE
                    self.initforms[i].validateForms(use=use)
        elif use=="forms":
            raise PoplibException("NOT IMPLEMENTED")
        else:
            raise PoplibException("I dont understand what to use  for initform validation: unknwon 'use' parameter value'%s'"%use)

    def validateForm(self,field,val):
        """Return an instance of the form or raise an exception if form is invalid"""
        if not self.hasKey(field):
            raise PoplibException("In agent %s, memory Variable %s has no key %s"%(self.agent.name,self.name,field))
        #debug("Initform attempting validation value:",self.agent.name,"->",self.name,"->",field,"(",self.initforms[field].__class__,") :",val)
        try:
            v=self.initforms[field].validate(val)
        except (PoplibException,PoplibDependencyException,PoplibInvalidDependencyException):
            raise
        except:
            raise Exception("Validation error in agent %s memvar %s (expression: %s): %s"%(self.agent.name,field,val, sys.exc_info()))
        #debug("    result-->",v)
        return v

    def instantiate(self,sequenceno, regionid=None,agentInstance=None,validateOnly=0,siblings=[]):
        """
        If memvar is simple, return a value, otherwise return a dict.
        If it is an array return a list.
        Note the siblings is unused, but is there for recursive span of structures
        """
        #if sequenceno==0:
        #    print "Sequence no is zero"
        typestr=""
        if self.isSimple():
            typestr="SIMPLE"
            if self.isSpecial():
                typestr="SPECIAL"
                if validateOnly:
                    rv=0
                else:
                    rv= agentInstance.getSpecialVar(self.name)#SPECIALVARSGENERATOR.generate(self.name,regionid)
            else: #TODO: take care of array initialization for simple vars
                rv= self.initforms[self.name].instantiate(sequenceno=sequenceno)
                if type(rv)==list:
                    raise PoplibException("The initform %s -->%s assigns an array value to a simple value: %s"%(self.agent.name,self.name,str(rv)))
        elif self.isarray:
            typestr="ARRAY"
            keyorder=self.getKeyNamesOnly()
            #prepare for array initialization
            preparts={}
            for k in self.getKeyNamesOnly():
                if k!="array length":
                    preparts[k]=self.initforms[k].instantiate(sequenceno=sequenceno,siblings=[DummyMemVar(nolengthlimit=1)]*10)
            #Done
            al=self.initforms["array length"].instantiate(sequenceno=sequenceno)
            if self.isComposite():#an array of composite, return a list of lists
                keyorder=self.getOrderedDatatypeKeyNames()
                retval=[]
                for i in range(al):
                    parts=OrderedDict()#[]#{}
                    missingduetosiblingdep=[]
                    for k in keyorder:#self.getKeyNamesOnly():
                        if k!="array length":
                            #parts[k]=self.initforms[k].instantiate()
                            if isinstance(self.initforms[k],BaseForm):
                                if type(preparts[k])==list:#not implemented yet
                                    if len(preparts[k])!=al:
                                        if validateOnly:
                                            parts[k]=preparts[k][0]
                                        else:
                                            raise PoplibException("The initform for memory variable %s->%s seems to indicate an array initialization, but its length (%d) is different from array length (%d)" % (self.agent.name,self.name,len(preparts[k]),al))
                                    else:
                                        parts[k]=preparts[k][i]#parts.append(preparts[k][i])
                                else:
                                    try:
                                        parts[k]=self.initforms[k].instantiate(sequenceno=sequenceno,siblings=[parts]+siblings)#parts.append(self.initforms[k].instantiate(sequenceno=sequenceno))
                                    except PoplibInvalidSiblingDependencyException:
                                        missingduetosiblingdep.append(k)
                                        parts[k]=None
                            else:#itself a memvar
                                #parts[k]=self.initforms[k].instantiate(sequenceno=sequenceno)#parts.append(self.initforms[k].instantiate(sequenceno=sequenceno))
                                try:
                                    parts[k]=self.initforms[k].instantiate(sequenceno=sequenceno,siblings=[parts]+siblings)#parts.append(self.initforms[k].instantiate(sequenceno=sequenceno))
                                except PoplibInvalidSiblingDependencyException:
                                    missingduetosiblingdep.append(k)
                                    parts[k]=None
                    #tmplen=len(missingduetosiblingdep)
                    for k in missingduetosiblingdep:
                        parts[k]=self.initforms[k].instantiate(sequenceno=sequenceno,siblings=[parts]+siblings)
                    retval.append(parts)
                rv= retval
            else:#an array of simple type
                rv=[]
                for k in keyorder:#self.getKeyNamesOnly():
                    if k!="array length":
                        thekey=k
                        break
                if type(preparts[thekey])==list:
                    if len(preparts[thekey])!=al:
                        raise PoplibException("The initform for memory variable %s->%s seems to indicate an array initialization, but its length (%d) is different from array length (%d)" % (self.agent.name,self.name,len(preparts[thekey]),al))
                    rv=preparts[thekey]
                else:
                    for i in range(al):
                        rv.append(self.initforms[k].instantiate(sequenceno=sequenceno,siblings=[{}]+siblings))
        else:
            typestr="STRUCT"
            if 1:
                parts=OrderedDict()
                missingduetosiblingdep=[]
                #for k in self.getKeyNamesOnly():
                for k in self.getOrderedDatatypeKeyNames():
                    try:
                        parts[k]=self.initforms[k].instantiate(sequenceno=sequenceno,siblings=[parts])
                    except PoplibInvalidSiblingDependencyException:
                        parts[k]=None
                        missingduetosiblingdep.append(k)
                    #parts.append(self.initforms[k].instantiate())
                for k in missingduetosiblingdep:
                    parts[k]=self.initforms[k].instantiate(sequenceno=sequenceno,siblings=[parts])
            else:
                parts=[]#{}
                #for k in self.getKeyNamesOnly():
                for k in self.getOrderedDatatypeKeyNames():
                    #parts[k]=self.initforms[k].instantiate()
                    parts.append(self.initforms[k].instantiate(sequenceno=sequenceno))
            rv= parts        
        typestr+="("+str(self.static)+")"
        #debug("MemVar instantiate ",self.originalname,typestr+str(self.getKeyNamesOnly())," returning ",rv)
        return rv

class Constant:
    def __init__(self,name,ctype,desc,model):
        self.model=model
        self.name=name
        self.ctype=ctype
        self.desc=desc
        if not ctype in ["int","double","float"]:
            raise PoplibException("Constant %s has invalid type: %s",name,ctype)
        self.value="0"
        self.constanttype=None
        self.isevaluated=0
    def reset(self):
        self.isevaluated=0
    def getType(self):
        """Returns 'value' or 'expression'"""
        self.getValue()
        return self.constanttype
    def setExpression(self,val):
        debug( "Setting constant",self.name,val)
        if not type(val)==str:raise Exception("Trying to set a non-string value as constant expression")
        self.value=val
        self.isevaluated=0
    def getExpression(self):
        return self.value
    def getValue(self,alternate=""):
        #debug("CONSTANT",self,self.name," returning value ",self.value)
        if self.isevaluated and not alternate:
            debug("CONSTANT %s is already evaluated"%self.name)
            return self.evaluatedvalue
        debug("CONSTANT %s evaluating"%self.name)
        getAgentCount=self.model.getGlobalAgentCount
        totry=self.value
        if alternate:totry=alternate
        self.constanttype="expression"
        try:
            v=float(totry)
            self.constanttype="value"
        except:pass
        try:
            v=eval(totry)
        except:
            i=sys.exc_info()
            print i
            traceback.print_tb(i[2])
            raise
        if self.ctype=="int" and not type(v)==int:
            raise Exception("Constant %s is an int but value given (%s) is not"%(self.name,totry))
        if self.ctype=="double" and not type(v)==float:
            raise Exception("Constant %s is a float but value given (%s) is not"%(self.name,totry))
        self.isevaluated=1
        self.evaluatedvalue=v
        return v
class ModelXMLRegistry:
    """
    This class is created because the populations needs to remember source of models, especially nested models,
    so that importing can be done when population is imported or reused on a machine where the original model.xml file(s)
    are no longer available. 
    An instance of this class is kept in the population and passed on to Model constructor for reuse.
    """
    def __init__(self):
        self.map={}
    def getKeys(self):
        return self.map.keys()
    def getModelXML(self,modelxmlpath):
        if self.map.has_key(modelxmlpath):
            debug("ModelXMLRegistry found record for %s"%modelxmlpath)
            return self.map[modelxmlpath]
        else:
            debug("ModelXMLRegistry missing record for %s"%modelxmlpath)
            tmp=open(modelxmlpath,"rb").read()
            self.map[modelxmlpath]=tmp
            return tmp
    def parse(self,modelxmlpath):
        return xmldom.parseString(self.getModelXML(modelxmlpath))
    
class Model:
    """Represents a model given in XMML or XMME format"""
    def __init__(self,modelXMMLFilePath,modeltype="xmml",silent=0,toplevelpop=None,region=None,xmlregistry=None,popforconstants=None):
        self.toplevelpop=toplevelpop
        self.popforconstants=popforconstants
        self.region=region
        self.info={}
        self.datatypes=[]
        self.constants=[]
        self.agents=[]
        if modeltype=="xmml":
            #Check if it is a new style XMML
            dom = xmlregistry.parse(modelXMMLFilePath)#xmldom.parse(modelXMMLFilePath)
            domdic=getDomAsMultiDict(dom)[1]
            self.info["domdic"]=domdic
            version=""
            try:
                root=domdic.getOne("xmachine_agent_model") #old style
                version="0"
                #print "Model XMML is old style. Version : ", version
            except:pass
            try:
                root=domdic.getOne("xmodel") #new style
                #print "Model XMML is new style"
                version="new"
            except:pass
            if version=="new":
                #print "Checking XMML version"
                root=dom.getElementsByTagName("xmodel")[0]
                if root.hasAttribute("version"):
                    version=root.getAttribute("version")
                    #print "Version is ",version
                else:
                    raise PoplibException("This is a new style XMML file (%s), but no version attribute is given!"%modelXMMLFilePath)
            if version=="0":
                root=domdic.getOne("xmachine_agent_model")
                self.makeModelFromXMML(root)
            elif version==None:
                raise PoplibException("I cannot determine version of the XMML")
            else:
                if version=="2":
                    root=domdic.getOne("xmodel")
                    self.makeModelFromXMMLv2(root,xmldir=os.path.dirname(modelXMMLFilePath),silent=silent,xmmefilename=modelXMMLFilePath,xmlregistry=xmlregistry)
                else:
                    raise PoplibException("I don't know how to parse  XMML models with version > 2!")
        else:
            raise PoplibException("Unknown model format: %s"%modeltype)

    def getGlobalAgentCount(self,aname):
        try:
            return self.toplevelpop.getAgentCount(aname)
        except:
            return self.popforconstants.getAgentCount(aname)
    def getRegionalAgentCount(self,aname):
        return self.region.getNumAgents(aname)
    def getAgentNames(self):
        n=[]
        for a in self.agents:
            n.append(a.name)
        return n

    def getAgentByName(self,aname):
        for agent in self.agents:
            if agent.name==aname:
                return agent
        return None

    def _getConstantsList(self):
        if not self.toplevelpop==None:
            clist=self.toplevelpop.model.constants
        else:
            clist=self.constants
        return clist
    def getConstantNames(self):
        n=[]
        for c in self._getConstantsList():
            n.append(c.name)
        return n

    def getConstantByName(self,cname):
        for c in self._getConstantsList():
            if c.name==cname:
                return c
        return None

    def cleanUpConstants(self):
        for c in self._getConstantsList():
            c.reset()
    def setConstant(self,cname,val):
        for c in self._getConstantsList():
            if c.name==cname:
                c.setExpression(val)
                return
        raise PoplibException("Trying to set unknown constant %s"%cname)

    def getDatatypeByName(self,dname):
        for d in self.datatypes:
            if d.name==dname:
                return d
        return None

    def makeModelFromXMML(self, root):
        """
        For old style XMML files.
        """
        #dom = xmldom.parse(xmlfile)
        #domdic=getDomAsMultiDict(dom)[1]
        #root=domdic.getOne("xmachine_agent_model")
        #self.info["domdic"]=domdic
        self.info["name"]=root.getOne("name")
        self.info["date"]=root.getOne("date")
        self.info["author"]=root.getOne("author")
        for datatype in root.getOne("environment").get("datatype"):
            name=datatype.getOne("name")
            try:
                desc=datatype.getOne("desc")
            except:
                desc=""
            dt=DataType(name,desc)
            for var in datatype.get("var"):
                vartype=var.getOne("type")
                varname=var.getOne("name")
                dt.vars[varname]={"type":vartype,"desc":"no description"}
            self.datatypes.append(dt)
        for agent in root.get("xmachine"):
            agentname=agent.getOne("name")
            ag=Agent(self,agentname,"no desc")
            for memvar in agent.getOne("memory").get("var"):
                memvartype=memvar.getOne("type")
                memvarname=memvar.getOne("name")
                ag.memvars.append(MemVar(memvarname,memvartype,"no desc",self,agent=ag))
                ag.memvarorder.append(memvarname)
            self.agents.append(ag)

    def makeModelFromXMMLv2(self, root,toplevel=1,xmldir="",silent=0,subfile="",xmmefilename="",xmlregistry=None):
        """
        For XMML version 2.
        """
        if toplevel:
            self.info["name"]=root.getOne("name")
            self.info["date"]=""#root.getOne("date")
            self.info["author"]=""#root.getOne("author")
            self.submodels={}
        else:
            try:
                self.submodels[subfile]=root.getOne("name")
            except:
                self.submodels[subfile]="No name"
        if root.has_key("environment"):
            if root.getOne("environment").has_key("datatypes"):
                for datatype in root.getOne("environment").getOne("datatypes").getAny("datatype"):
                    name=datatype.getOne("name")
                    desc=datatype.getOneOrDefault("description",default="No desc")
                    dt=DataType(name,desc)
                    for var in datatype.getOne("variables").getAny("variable"):
                        vartype=var.getOne("type")
                        varname=var.getOne("name")
                        vardesc=var.getOneOrDefault("description",default="no desc")
                        dt.varorder.append(varname)
                        dt.vars[varname]={"type":vartype,"desc":vardesc}
                    self.datatypes.append(dt)
            if root.getOne("environment").has_key("constants"):
                for constant in root.getOne("environment").getOne("constants").getAny("variable"):
                    name=constant.getOne("name")
                    desc=constant.getOneOrDefault("description",default="No desc")
                    dtype=constant.getOne("type")
                    #print "FOUND CONSTANT:",name,dtype, desc
                    self.constants.append(Constant(name,dtype,desc,self))
        if toplevel:
            if root.has_key("models"):
                for model in root.getOne("models").getAny("model"):
                    f=model.getOne("file")
                    e=model.getOne("enabled")
                    if e.lower()=="true":
                        debug( "Recursing into (sub) model file:", f)
                        if not silent:
                            pass
                            #debug( "Recursing into (sub) model file:", f)
                            #print "Recursing into (sub) model file:", f
                        fpath="%s/%s"%(xmldir,f)
                        subdom = xmlregistry.parse(fpath)#xmldom.parse(fpath)
                        subdomdic=getDomAsMultiDict(subdom)[1]
                        subroot=subdomdic.getOne("xmodel") #NO XMML VERSION CHECKING FOR SUB MODELS
                        self.makeModelFromXMMLv2(subroot,toplevel=0,silent=0,subfile=fpath,xmmefilename=f,xmlregistry=xmlregistry)
                    else:
                        #print "Skipping disabled model file:", f
                        pass
        for agent in root.getOne("agents").getAny("xagent"):
            agentname=agent.getOne("name")
            hasagent=self.getAgentByName(agentname)
            if hasagent==None:
                ag=Agent(self,agentname,agent.getOneOrDefault("description",default="no desc"))
                self.agents.append(ag)
            else:
                ag=hasagent
            if agent.has_key("memory"):
                mem=agent.getOne("memory")
                if isinstance(mem,MultiDict):
                    for memvar in agent.getOne("memory").getAny("variable"):
                        memvartype=memvar.getOne("type")
                        memvarname=memvar.getOne("name")
                        try:
                            ag.memvars.append(MemVar(memvarname,memvartype,memvar.getOneOrDefault("description",default="no desc"),self,agent=ag))
                        except PoplibException:
                            raise PoplibException("(While processing file '%s')\n%s"%(xmmefilename,sys.exc_info()[1]))
                        ag.memvarorder.append(memvarname)
    def printSummary(self):
        print self.summary()

    def summary(self):
        rv= "MODEL: %s \n" % self.info["name"]
        rv+= "  Author: %s \n" % self.info["author"]
        rv+="  Date: %s\n"% self.info["date"]
        rv+="  AGENTS: \n"
        for a in self.agents:
            rv+= "    %s : " % a.name
            for mv in a.memvars:
                rv+="%s "% mv
            rv+="\n"
        rv+= "  DATATYPES: \n"
        for d in self.datatypes:
            rv+= "     %s : " % d.name
            for v in d.vars.keys():
                rv+= "%s(%s) "%(v,d.vars[v]["type"])
            rv+="\n"
        return rv
    
    def printInitForms(self):
        debug("MODEL INITFORMS ")
        for a in self.agents:
            debug("AGENT:",a.name)
            for mv in a.memvars:
                mv.printInitForm()

    def __str__(self):
        return reprMultiDictAsTXT(self.info["domdic"])

class AgentInstance:
    def __init__(self,model,agentname,region,sequenceno,ID):
        self.model=model
        self.region=region
        self.agentname=agentname
        self.sequenceno=sequenceno ## position of agent within same type of agents
        self.ID=ID
        self.instantiated=0
        self.values={}
        self.exclusivelytaken=0 #if another agent has taken this one
    def getSpecialVar(self,varname):
        if varname=="id":
            if REPLACEID:
                return "%s%d"%(REPLACEID,self.ID)
            else:
                return self.ID
        elif varname=="region_id":
            if REGIONREPLACEID:
                return IDReplacer(self.region.regionid,REGIONREPLACEID)
            else:
                return self.region.regionid
    def instantiate(self,popmap,regionid,singlememvar=""):
        """Instantiate the variables of the agent. If necessary refer to other agents in the population. See popmap of Population class"""
        if self.instantiated:
            if not singlememvar:
                raise PoplibException("Already instantiated")
        for a in self.model.agents:
            if self.agentname==a.name:
                agent=a
        if not self.instantiated:
            self.varreg=MemVarRegistry(agent,self)
            self.values=self.varreg.valmap
        global this
        this=self.varreg
        if singlememvar:
            debug( "Instantiating Agent single memvar %s-->%s sequence no %d"%(self.agentname,singlememvar,self.sequenceno))
            mv=agent.getMemVarByName(singlememvar)
            self.varreg.valmap[singlememvar]=mv.instantiate(self.sequenceno,regionid=regionid,agentInstance=self)
        else:
            debug( "Instantiating Agent %s sequence no %d"%(self.agentname,self.sequenceno))
            for mvn in agent.varinitorder:
                mv=agent.getMemVarByName(mvn)
                self.varreg.valmap[mvn]=mv.instantiate(self.sequenceno,regionid=regionid,agentInstance=self)
                #this.valmap[mvn]=self.values[mvn]
        self.instantiated=1
        this=None

    def __str__(self):
        rv= "AGENT : "+self.agentname+"\n"
        for k in self.values.keys():
            rv+="   "+k+" : "+str(self.values[k])+"\n"
        return rv

    def toXML(self):
        #raise PoplibException("AgentInstance.toXML() NOT IMPLEMENTED")
        def tostr(x):
            if type(x)==list:
                tmp=""
                for i in x:
                    if tmp:tmp+=","
                    tmp+=tostr(i)
                return "{"+tmp+"}"
            elif type(x)==dict or isinstance(x,OrderedDict):
                tmp=""
                for i in x.values():
                    if tmp:tmp+=","
                    tmp+=tostr(i)
                return "{"+tmp+"}"
            else:
                return str(x)
        if not self.instantiated:
            raise PoplibException("Not instantiated")
        rv="<xagent>\n<name>%s</name>\n"%self.agentname
        #return rv+str(self.values)+"</xagent>\n"
        for a in self.model.agents:
            if self.agentname==a.name:
                agent=a
        for von in agent.memvarorder:#self.values.keys():
            mv=agent.getMemVarByOriginalName(von)
            v=mv.name
            #v=self.values[vn]
            val=self.values[v]
            if v in ["id","region_id"]:debug( "SPECIAL VARIABLE %s:"%v,val)
            #debug("Converting:",val)
            if v=="region_id":
                if REGIONREPLACEID:
                    rv+="  <%s>%s</%s>\n"% (v,val,v)
                else:
                    rv+="  <%s>%s</%s>\n"% (v,tostr(val+1),v)
            else:    
                rv+="  <%s>%s</%s>\n"% (v,tostr(val),v)
        rv+="</xagent>\n"
        return rv
class Progress:
    """
    A modified version of progress bar to make incremental changes possible
    """
    def __init__(self,progbar,total,pop):
        self.progbar=progbar
        self.total=total
        self.current=0
        self.pop=pop
        self.text="Initializing..."
        self.start=time.time()
        self.last=time.time()
        self.etr=0
        self.alpha=0.98
        self.updateText()
    def tick(self,append=""):
        if self.pop.getCancelFlag():
            raise PoplibException("Instantiation of population is cancelled by user")
        self.current+=1
        if self.progbar!=None:
            import pygtk,gobject
            pygtk.require('2.0')
            import gtk
            while gtk.events_pending():
                gtk.main_iteration_do(False)
            frac=self.current/(self.total+0.0)
            self.progbar.set_fraction(frac)
            self.updateText(append=append)
            #print "Setting progress bar fraction:",frac
    def setText(self,txt):
        self.text=txt
        self.updateText()
    def updateText(self,append=""):
        #try:
        #    et=(time.time()-self.start)*(self.total/(self.current+0.0))
        #    tmp=datetime.timedelta(0,et)
        #    etr="(Estimated time remaining: %s sec)"%str(tmp)#.strftime("%H:%M:%S")
        #except:
        #    debug(sys.exc_info())
        etr=""
        #try:
        #    x=time.time()
        #    self.etr=self.etr*self.alpha+(x-self.last)*(1-self.alpha)
        #    td=datetime.timedelta(0,self.etr*(self.total-self.current))
        #    etr="(Estimated time remaining: %s sec)"%str(td)
        #    self.last=x
        #except:
        #    debug(sys.exc_info())
        #    etr=""
        if self.progbar!=None:
            self.progbar.set_text("%s %s %s"%(self.text,etr,append))
    def totalTime(self):
        """Return total time from start, in seconds"""
        return time.time()-self.start
class Population:
    """A population is composed of different regions
    Population class (not instances) have a version number to resolve backward compatibility.
    As new features are added to poplib the versions were incresed as follows:
      0.1.0: initial implementation with multiple regions
      0.2.0: added agent and memory referencing capability
      0.2.1: change Agent to address global dependencies
      0.2.4: Added ModelXMLRegistry instance
    """
    CURRENTVERSION="0.2.6"
    def __init__(self,name,modelXMMLFilePath,modeltype="xmml"):
        self.name=name
        self.modelxmlregistry=ModelXMLRegistry()
        self.modelfile=modelXMMLFilePath
        self.model=Model(modelXMMLFilePath,modeltype=modeltype,xmlregistry=self.modelxmlregistry,popforconstants=self)
        debug("POPULATION XML REGISTRY KEYS:")
        debug(self.modelxmlregistry.getKeys())
        self.numregions=0
        self.regions=[]
        self.state="newpop"
        self.setNumRegions(1)
        self.version=Population.CURRENTVERSION
        self.popmap={} #map from agentname to agent instances list
        self.popidmap={}
    def getModelXMLRegistry(self):
        try:
            return self.modelxmlregistry
        except:
            self.modelxmlregistry=ModelXMLRegistry()
            return self.modelxmlregistry
    def getAgentIDListGlobal(self,aname):
        retval=[]
        for r in self.regions:
            retval.extend(r.getAgentIDListRegional(aname))
        return retval
    def makeAgentID(self):
        try:
            retval=self.agentIDcounter
        except:
            self.agentIDcounter=1
            retval=self.agentIDcounter
        self.agentIDcounter+=1
        return retval
    def getCancelFlag(self):
        try:
            return self.cancel
        except:
            self.cancel=0
            return self.cancel
    
    def setCancelFlag(self):
        self.cancel=1
    def resetCancelFlag(self):
        self.cancel=0

    def getNumRegions(self):
        return self.numregions

    def setNumRegions(self,numregions):
        if numregions>self.numregions:
            for r in range(self.numregions,numregions):
                reg=PopRegion(self.modelfile,r,self)
                #reg.model.setConstants(self.model.constants)#HACK FOR CONSTANTS
                self.regions.append(reg)
        else:
            self.regions=self.regions[:numregions]
        self.numregions=numregions
        global popguinumregions
        popguinumregions=numregions
    def processMemVarDependencies(self):
        """
        Make dependency referencing checks for all memvars of all agents in all regions and store memvar initialization orders -according to most recent memvar initforms- in Agent instances
        """
        debug("CCCCCCCCCCCCCCCCCCCC   CHECKING MEMVAR DEPENDENCIES CCCCCCCCCCCCCCCCCCCCCCCCCCC")
        for r in self.regions:
            for a in r.model.agents:
                a.validateReferenceDependencies()
                a.getVarInitOrder()
        debug("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
    def getAgentByID(self,ID):
        return self.popidmap[ID].varreg
    def getIDMap(self):
        try:
            return self.popidmap
        except:
            self.popidmap={}
            return self.popidmap
    def mapAgent(self,aname,ainst):
        if not self.popmap.has_key(aname):
            self.popmap[aname]=[]
        self.popmap[aname].append(ainst)
        self.getIDMap()[ainst.ID]=ainst
    def cleanUp(self):
        """
        Clean up the references to AgentInstance's needed only for instantiation
        so that saving population will not used too much memory
        """
        self.popmap={}
        self.popidmap={}
        self.model.cleanUpConstants()
        for r in self.regions:
            r.cleanUp()
    def getNumberedRegion(self,n):
        for r in self.regions:
            if r.regionid==n:
                return r

    def getInitializationOrder(self,depmap={}):        
        #generate merged global and regional partial initialization from such dependencies in individual regions
        if not depmap:
            depmap={}
            for r in self.regions:
                depmap[r.regionid]=r.processAgentDependencies()
        debug(depmap)
        gdmap={}
        gpo=[]
        rpo={}
        initorder=[] #contains tuples (regionid,agentname)
        regionlist=depmap.keys()
        agentlist=depmap[0][0].keys()
        debug("Region list: %s"%str(regionlist))
        debug("Agent list: %s"%str(agentlist))
        def pushInitOrder(rid,a,track=[]):
            if (rid,a) in track:
                msg=""
                for i in range(1,len(track)):
                    trid,ta=track[i-1]
                    ntrid,nta=track[i]
                    msg+="Region: %d, agent %s (memvar(s) %s) to agent %s\n"%(trid+1,ta,self.regions[trid].model.getAgentByName(ta).dependencereferers[nta],nta)
                trid,ta=track[-1]
                ntrid,nta=rid,a
                msg+="Region: %d, agent %s (memvar(s) %s) to agent %s\n"%(trid+1,ta,self.regions[trid].model.getAgentByName(ta).dependencereferers[nta],nta)
                raise Exception("Cyclic dependency: \n%s " %msg)
            rd,gd=depmap[rid]
            rda=rd[a]
            gda=gd[a]
            for x in rda:
                pushInitOrder(rid,x,track=track+[(rid,a)])
            for x in gda:
                for r in regionlist:
                    pushInitOrder(r,x,track=track+[(rid,a)])
            if not (rid,a) in initorder:
                initorder.append((rid,a))
        for rid in regionlist:
            for a in agentlist:
                pushInitOrder(rid,a)
        debug("INIT ORDER:")
        for x in initorder:
            debug(str(x))
        #raw_input("ENTER:")
        return initorder
    def getInitializationOrderOLD(self,depmap):
        """
        Produce an order of which agents of which regions should be initialized
        This needs to process regional and global agent dependencies for  all regions
        so depmap is a dictionary:
          regionid: (regionaldependencies,globaldependencies) #see PopRegion processAgentDependencies() return value
        returns the order as a list of (rid,agentname)
        """
        gpo=[] #global partial initorder: ordered agentnames to account for global dependencies
        rpo={} # regional partial init orders
        initorder=[] #contains tuples (regionid,agentname)
        gdmap={} #merged global dependency map agent:[agents,...]
        def pushgdmap(f,t):
            if not gdmap.has_key(f):
                gdmap[f]=[]
            if not (t in gdmap[f]):
                gdmap[f].append(t)
        for rid in depmap.keys():
            rpo[rid]=[]
            rd,gd=depmap[rid]
            for a in gd.keys():
                d=gd[a]
                for da in d:#agent has global dependencies
                    pushgdmap(a,da)
        debug("Global merged dependency map:")
        for a in gdmap.keys():
            debug("  %s -> %s" %(a,str(gdmap[a])))
        def pushdep(f,t,track=[]):
            if t in track:
                raise PoplibException("Cyclic global agent dependency:  chain %s links to %s again " %(str(track),t))
            if gdmap.has_key(t):
                for x in gdmap[t]:
                    #newtrack=[]
                    #for z in track:
                    #    newtrack.append(z)
                    #newtrack.append(t)
                    pushdep(t,x,track=track+[t])
            if not (t in gpo):
                gpo.append(t)
        prevlen=len(gpo)
        cont=1
        while cont:
            for a in gdmap.keys():
                for d in gdmap[a]:
                    try:
                        pushdep(a,d,track=[a])
                    except:
                        debug("Error processing agent dependencies for initialization order")
                        raise
                if not (a in gpo):
                    gpo.append(a)
            if len(gpo)>prevlen:
                prevlen=len(gpo)
            else:
                cont=0
        debug("Global Partial order:%s"%(str(gpo)))
        #NOW DO THE REGIONAL ORDERS
        def pushRIO(rid,a):
            #if not (a in gpo):
            #    if not (a in rpo[rid]):
            #        rpo[rid].append(a)
            if not (a in rpo[rid]):
                rpo[rid].append(a)
        def checkCyclicDep(rid,f,t,map,gmap,track=[],info=""):
            if t in track:
                debug("%d %s %s %s %s %s %s"%(rid,f,t,map,gmap,track,info))
                raise PoplibException("Cyclic dependency: %s, chain %s links to %s again " %(info,str(track),t))
            for x in map[t]:
                checkCyclicDep(rid,t,x,map,gmap,track=track+[t],info=info)
            for x in gmap[t]:
                checkCyclicDep(rid,t,x,map,gmap,track=track+[t],info=info)
            #pushRIO(rid,t)
        for rid in depmap.keys():
            rd,gd=depmap[rid]
            for a in rd.keys():
                for d in rd[a]:
                    if d in gpo:
                        for x in gpo[:gpo.index(d)]:pushRIO(rid,x)
                        if a in gpo:
                            if gpo.index(a)<=gpo.index(d):
                                raise PoplibException("In region %d agent %s depends on agent %s. However there is a reverse global dependency. Hence the dependencies cannot be satisfied."% (rid,a,d))
                            for x in gpo[:gpo.index(a)]:pushRIO(rid,x)
                    #if a in gpo and not (d in gpo): #TODO : this is a shortcut, an ordering still can be found!
                    #    raise PoplibException("In region %d agent %s depends on agent %s. However it is a globally depended agent itself."% (rid,a,d))
                    #checkCyclicDep(rid,a,d,rd,gd,track=[a],info="Region %d"%rid)
                    pushRIO(rid,d)
                pushRIO(rid,a)
        for rid in depmap.keys():
            rd,gd=depmap[rid]
            debug("Region %d dependencies: %s %s"%(rid,rd,gd))
            for a in rd.keys():
                for d in rd[a]:
                    checkCyclicDep(rid,a,d,rd,gd,track=[a],info="region %d"%rid)
        for rid in depmap.keys():
            debug("Region %d initorder %s %s" %(rid,str(gpo),str(rpo[rid])))
        #for a in gpo:
        #    for rid in depmap.keys():
        #        initorder.append((rid,a))
        def setInitOrder(rid,a):
            debug("setInitOrder called for %s"%str((rid,a)))
            if not (rid,a) in initorder:
                initorder.append((rid,a))
            else:
                debug("setInitOrder skipped pushing %s into %s"%((rid,a),initorder))
            if a in gpo:
                for orid in depmap.keys():
                    if not (orid,a) in initorder:
                        initorder.append((orid,a))
                    else:
                        debug("setInitOrder skipped pushing %s into %s"%((orid,a),initorder))
        for rid in depmap.keys():
            for a in rpo[rid]:
                setInitOrder(rid,a)
        debug("FINAL INITORDER IS:")
        for x in initorder:
            debug("  %s"%str(x))
        #raw_input("ENTER")
        return initorder
        
    def instantiate(self,outfile,progbar=None,createEnvironment=True):
        """
        Create a population instance and return numagents
        the resulting 0.xml content will be written into outfile, which is a file descriptor
        progress is a gtk.ProgressBar instance, if desired
        """
        #for r in self.regions:
        #    r.model.constants=[]
        #    for c in self.model.constants:
        #        r.model.constants.append(c)
        self.cleanUp()
        self.agentIDcounter=1
        self.resetCancelFlag()
        self.popmap={}
        self.processMemVarDependencies()
        total=0
        depmap={}
        for r in self.regions:
            depmap[r.regionid]=r.processAgentDependencies()
            total+=3#r.getTotalNumAgents()*3 #one for creating AgentInstance, one for instantiating, one for producing xml
        initorder=self.getInitializationOrder(depmap) # list of (rid,aname)
        ########detailed initorder
        fineinitorder=[]
        delayedinit=[]
        for tp in initorder:
            rid,aname=tp
            r=self.getNumberedRegion(rid)
            a=r.model.getAgentByName(aname)
            print rid,aname,a.getFineDependencies() 
            delayedmvns=[]
            for d in a.getFineDependencies(): #a list of ONLY delayed dependencies(frommemvar,deptype,toagentname,tomemvarname,delay)
                delayedmvns.append(d[0].name)#TODO: CAN USE d[4] (delay) to order these within themselves
            for mvn in a.varinitorder:
                if not mvn in delayedmvns:
                    fineinitorder.append((rid,aname,mvn))
                else:
                    delayedinit.append((rid,aname,mvn))
        for x in delayedinit:
            print "delayedExecution:",x
            fineinitorder.append(x)#TODO THIS IS NOT TRUE ORDERING, JUST DELAYED
        #########
        total=0
        for r in self.regions:
            total+=2#r.getTotalNumAgents()*2 #one for creating AgentInstance, one for instantiating, one for producing xml
        #total+=len(fineinitorder)
        for rid,aname,mvn in fineinitorder:
            r=self.getNumberedRegion(rid)
            total+=1#r.getNumAgents(aname)
        progress=Progress(progbar,total,self)
        progress.setText("Checking dependencies ...")
        numagents=0
        global GLOBALCONSTANTS
        GLOBALCONSTANTS=self.model.constants #HACK FOR CONSTANTS
        SPECIALVARSGENERATOR.reset()
        retval="<states>\n<itno>0</itno>\n"
        if createEnvironment:
            retval+="<environment>\n"
            for c in self.model.constants:
                retval+="<%s>%s</%s>\n"%(c.name.lower(),str(c.getValue()),c.name.lower())
            retval+="</environment>\n"
        outfile.write(retval)
        regcount=0
        for r in self.regions:
            progress.tick();
            if r.getTotalNumAgents():
                regcount+=1
                progress.setText("Creating agent objects in region %d"%regcount)
                numagents+=r.recreatePop(progress=progress,init=0)
        #print "FINE INIT ORDER:"
        #for x in fineinitorder:print x
        #progratio=len(fineinitorder)/(len(initorder)+0.0)
        if 1:
            ct=0
            for rid,a,mvn in fineinitorder:
                r=self.getNumberedRegion(rid)
                #progress.setText("Instantiating memvars in region %d, agent %s memvar %30s"%(rid+1,a,mvn[:30]))
                ct+=1
                #if ct>=progratio:
                r.initializeAgents(a,progress=progress,singlememvar=mvn)
                progress.tick()
                #    ct-=progratio
                #else:
                #r.initializeAgents(a,singlememvar=mvn)
        else:
            for tp in initorder:
                rid,a=tp
                r=self.getNumberedRegion(rid)
                progress.setText("Instantiating memvars in region %d, agent %s "%(rid+1,a))
                r.initializeAgents(a,progress=progress)
        regcount=0
        for r in self.regions:
            if r.getTotalNumAgents():
                regcount+=1
                progress.setText("Converting agents in region %d to XML"%regcount)
                #retval+=r.popToXML(progress=progress)
                r.popToXML(outfile,progress=progress)
                progress.tick()
        #retval+="</states>"    
        outfile.write("</states>")
        GLOBALCONSTANTS=None
        return (numagents,progress.totalTime())
    def getAgentCount(self,aname):
        if self.model.getAgentByName(aname)==None:
            raise PoplibException("No agent with given name is found in the model: %s"%aname)
        sum=0
        for r in self.regions:
            sum+=r.getNumAgents(aname)
        return sum
        
class PopRegion:
    def __init__(self,modelfile,regionid,parentpop):
        self.model=Model(modelfile,silent=1,toplevelpop=parentpop,region=self,xmlregistry=parentpop.getModelXMLRegistry())
        self.parentpop=parentpop
        self.numAgents={} #{agentname:numagents, ...}
        self.popmap={} #{agentname:[instances...], ...}
        self.pop=[] #[AgentInstance(s),...]
        self.regionid=regionid
        self.agentinitorder=[]

    def getAgentIDListGlobal(self,aname):
        return self.parentpop.getAgentIDListGlobal(aname)
    def getAgentIDListRegional(self,aname):
        retval=[]
        if self.model.getAgentByName(aname)==None:
            raise PoplibException("Problem generating list of agent IDs: there is no such agent in the model: %s"%aname)
        if not self.popmap.has_key(aname):
            return retval
        for a in self.popmap[aname]:
            retval.append(a.getSpecialVar("id"))
        return retval
    def getNumAgents(self,agentname):
        if self.numAgents.has_key(agentname):
            return self.numAgents[agentname]
        else:
            #print "No numagents for ",agentname, ". only for",self.numAgents
            return 0

    def getTotalNumAgents(self):
        t=0
        for a in self.numAgents.keys():
           t+=self.getNumAgents(a)
        return t

    def setNumAgents(self,agentname,num):
        hasagent=0
        for a in self.model.agents:
            if agentname==a.name:
                hasagent=1
        if not hasagent:
            raise PoplibException("No agent with given name")
        else:
            self.numAgents[agentname]=num

    def readNumAgents(self):
        for a in self.model.agents:
            if self.numAgents.has_key(a.name):
                inp=raw_input("Number of agents of type '%s' [Current value %d] :"% (a.name,self.numAgents[a.name]))
                if inp:
                   self.setNumAgents(a.name,int(inp))
            else:
                self.setNumAgents(a.name,int(raw_input("Number of agents of type '%s' :"% a.name)))

    def readInitForms(self,agent="",var=""):
        if agent:
            if not agent in self.model.getAgentNames():
                print "Unknown agent: ",agent
                print "Known agents are : ",
                for a in self.model.getAgentNames():
                    print a," ",
                print
                return
        print "FOLLOWING IS THE HELP FOR INITIALIZATION FORM SYNTAX"
        print InitForm.help
        print
        print "(Press enter to accept default or current value)"
        for a in self.model.agents:
            if agent:
                if agent!=a.name:continue
            print "INITIALIZATION FORMS FOR AGENT: ",a.name
            for mv in a.memvars:
                if var:
                    if var!=mv.name:continue
                mv.initform.read(self.model.datatypes)

    def printSummary(self,includeinitforms=0):
        print self.summary(includeinitforms=includeinitforms)
    
    def summary(self,includeinitforms=0):
        rv= "POPULATION: %s\n"%self.name
        rv+="Number of each agent type:\n"
        for a in self.model.agents:
            tmp="not given"
            if self.numAgents.has_key(a.name):tmp=str(self.numAgents[a.name])
            rv+= "   %s : %s\n" %(a.name,tmp)
        if includeinitforms:
            for a in self.model.agents:
                rv+= "INITIALIZATION FORMS FOR AGENT: %s\n"%a.name
                for mv in a.memvars:
                    rv+= str(mv.initform) +"\n"
        return rv

    def processAgentDependencies(self):
        """
        This method assumes that dependency processing for agents are executed already, the population class takes care of that
        Looks at agents' dependencies (global or regional) and returns a tuple (regionaldependences,globaldependences)
        where regonal dependences is itself a dictonary
          agentname: [depended agents]
        and global dependences is also a dictionary
          agentname: [depended agents]
        """
        self.agentinitorder=None # to avoid accidents leaking from older implementation
        regmap={}
        glomap={}
        for a in self.model.agents:
            regmap[a.name]=a.depends
            glomap[a.name]=a.globaldepends
        return (regmap,glomap)
        #############
        self.agentinitorder=[]
        def pushDep(a):
            for d in a.depends:
                pushDep(self.model.getAgentByName(d))
            if not (a.name in self.agentinitorder):
                self.agentinitorder.append(a.name)
        for a in self.model.agents:
            #print a.name,a.depends
            pushDep(a)
        debug("Region %d agentinitorder: %s" %(self.regionid+1,str(self.agentinitorder)))
        #raw_input("ENTER")
        #return self.agentinitorder
        return (regmap,glomap)
                    
    def recreatePop(self,progress=None,init=1):
        """Create or re-create population"""
        self.pop=[]
        self.popmap={}
        return self.createPop(progress=progress,init=init)

    def createPop(self,progress=None,init=1):
        """Instantiate a population, and return number of agents"""
        if self.pop:
            raise PoplibException("Population already created")
        if not self.numAgents:
            raise PoplibException("Number of agents not given yet")
        c=0
        for a in self.numAgents.keys():
            self.popmap[a]=[]
            c+=self.numAgents[a]
            for i in range(self.numAgents[a]):
                instance=AgentInstance(self.model,a,self,i,self.parentpop.makeAgentID())
                #if not progress==None:
                #    progress.tick()
                self.popmap[a].append(instance)
                self.pop.append(instance)
                self.parentpop.mapAgent(a,instance)
        if init:
            for an in self.agentinitorder:
                self.initializeAgents(an,progress=progress)
            #for i in self.popmap[an]:
            #    i.instantiate(self.popmap,self.regionid)
        return c

    def cleanUp(self):
        """
        Clean up the AgentInstance references needed only for instantiation
        so that saving the population will not use too much memory
        """
        self.pop=[]
        self.popmap={}
        self.model.cleanUpConstants()
    def initializeAgents(self,agentname,progress=None,singlememvar=""):
        """
        Instantiate agents of type given in agentname. Tick a pygtk progress bar if given
        """
        #print "Initializing region %d agent %s memvar %30s" % (self.regionid+1,agentname,singlememvar)
        if not self.popmap.has_key(agentname):
            return
        c=0
        for i in self.popmap[agentname]:
            i.instantiate(self.popmap,self.regionid,singlememvar=singlememvar)
            c+=1
            #if not progress==None:
            #    progress.tick(append=str(c))

    def popToXML(self,outfile,progress=None):
        """Return XML to be put in 0.xml"""
        if not self.pop:
            raise PoplibException("Population not created yet")
        #its="<states>\n<itno>0</itno>\n"
        #its=""
        for i in self.pop:
            #progress.tick()
            #its+=i.toXML()
            outfile.write(i.toXML())
        #its+="</states>"
        #return its
