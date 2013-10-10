#!/usr/bin/python
"""
    Experiment manager Library for EURACE
    
    Author: Mehmet Gencer, mgencer@cs.bilgi.edu.tr
            Bulent Ozel, bulent.ozel@gmail.com, Reykjavik University
"""

import sys, os, os.path, pickle, textwrap, traceback, copy, getopt, thread
from poplib import *
#from pygtk import *
import pygtk,gobject
pygtk.require('2.0')
import gtk
try:
    import signal
    HASSIGNAL=1
except:
    debug("No 'signal' module")
    HASSIGNAL=0
VERSION="0.7.14"
global VERSIONCHECKING
VERSIONCHECKING=1
EVALUATOR=0
USERHOME=os.path.expanduser("~")
CONFIGPATH="%s/euracepopgui.config"%USERHOME
CONFIG={
    "GUIHOME":os.path.expanduser("~"),
    "LASTMODELDIR":os.path.expanduser("~"),
    "LASTPOPDIR":os.path.expanduser("~"),
    "LASTXMLDIR":os.path.expanduser("~"),
    "CONSOLEBUFFERLEN":1500
    #"MVEDITLABELSIZE":30
}
INITFORMHELP=MemVar.help
ABOUT="EURACE Population GUI Version %s\nCreated by TUBITAK-UEKAE Team, 2008:\nContact: Mehmet Gencer, mgencer@cs.bilgi.edu.tr"%VERSION
if os.path.exists(CONFIGPATH):
    newc=pickle.load(open(CONFIGPATH,"rb"))
    for k in CONFIG.keys():
        if not newc.has_key(k):
            newc[k]=CONFIG[k]
    CONFIG=newc

def saveConfig():
    pickle.dump(CONFIG,open(CONFIGPATH,"wb"))

class PopGUI:
    def __init__(self):
        self.state="init"
        self.window=gtk.Window()
        self.window.set_title("PopGUI v%s"%VERSION)
        self.window.set_default_size(300,200)
        self.window.connect("destroy", self.quit)
        self.window.connect("delete-event",self.preQuit)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_default_size(400,300)
        self.window.set_icon_from_file("euracelogo.ico")
        self.modified=0
        self.widgets={}
        self.toolbuttoncount=0

    def addToolButton(self,id,label,method):
        self.widgets[id]=gtk.Button(label)
        self.widgets[id].connect("clicked",method)
        self.widgets[id].show()
        self.toolbar.pack_start(self.widgets[id],expand=False,fill=False)

    def start(self,fname=""):
        self.table=gtk.Table(rows=3, columns=1, homogeneous=False)
        self.toolbar=gtk.HBox()
        self.table.attach(self.toolbar, 0, 1, 1, 2,yoptions=0)
        self.menuitems=(
            ("/_File",         None,         None, 0, "<Branch>" ),
            ("/File/_New Population",     "<control>N", self.newPop, 0, None ),
            ("/File/_Open Population",     "<control>O", self.openPop, 0, None ),
            ("/File/_Save Population",     "<control>S", self.savePop, 0, None ),
            ("/File/_Save Population As",     "<control>A", self.savePopAs, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ("/File/_Quit",     "<control>Q", self.quitManual, 0, None ),
            ("/Tools",          None,         None, 0, "<Branch>"),
            ("/Tools/_Export to LaTeX",               None,        self.exportToLatex,0,None),
            ("/Help",          None,         None, 0, "<Branch>"),
            ("/Help/_Contents",               None,        self.help,0,None),
            ("/Help/_About",               None,        self.about,0,None),
            )
        accel_group = gtk.AccelGroup()
        item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", accel_group)
        item_factory.create_items(self.menuitems)
        self.window.add_accel_group(accel_group)
        #self.menubarhbox=gtk.HBox()
        #self.menubarhbox.pack_start(item_factory.get_widget("<main>"),expand=False,fill=False)
        self.table.attach(item_factory.get_widget("<main>"),0,1,0,1,yoptions=0)
        #self.table.attach(self.menubarhbox,0,1,0,1,xoptions=0,yoptions=0)
        self.addToolButton("modelsummary","Model Summary",self.showSummary)
        self.addToolButton("genpropbut","1 - Properties",self.setPopProp)
        self.addToolButton("regbut","2 - Edit Regions",self.editRegions)
        self.addToolButton("constbut","3 - Edit Constants",self.editConstants)
        self.addToolButton("mvbut","4 - Edit Memory Variables",self.editMemVars)
        self.addToolButton("insbut","5 - Instantiate population (0.xml)",self.instantiate)
        self.textscroll=gtk.ScrolledWindow()
        self.textscroll.show()
        self.textview = gtk.TextView()
        self.textview.set_size_request(350,250)
        #textscrollbar = gtk.VScrollbar(self.textview.get_vadjustment())
        self.textview.set_editable(0)
        self.textview.set_cursor_visible(0)
        self.textview.set_wrap_mode(gtk.WRAP_CHAR)
        self.textview.show()
        self.textscroll.add(self.textview)
        self.table.attach(self.textscroll,0,1,2,3)
        self.progbar=gtk.ProgressBar()
        self.progbar.hide()
        self.progbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self.cancelpop=gtk.Button("CANCEL")
        self.cancelpop.connect("clicked",self.cancelPopulationCreation)
        self.cancelpop.hide()
        self.window.add(self.table)
        self.window.show_all()
        self.message("PopGUI version %s started."%VERSION)
        if fname:
            if fname[-5:]==".xmml" or fname[-4:]==".xml":
                self.newPopFromFile(fname)
            else:
                self.openPop(fname=fname)
        gtk.main()
    def exportToLatex(self,*args,**kwargs):
        try:
            print self.population.name
        except:
            self.dialogMessage("No population is created or opened yet!")
            return
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
        filec=gtk.FileChooserDialog(title="Choose file to save memory variable list",parent=self.window,action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        #filec.set_current_folder(CONFIG["LASTXMLDIR"])
        filter = gtk.FileFilter()
        #filter.add_pattern("*.tex")
        #filter.set_name(".xml")
        #filec.add_filter(filter)
        filterall=gtk.FileFilter()
        filterall.add_pattern("*")
        filterall.set_name("All files")
        filec.add_filter(filterall)
        response=filec.run()
        if response == gtk.RESPONSE_OK:
            texfile= filec.get_filename()
        else:
            texfile=""
        filec.destroy()
        if texfile:
            outputfile=open(texfile,"w")
            memory(self.population)
            self.dialogMessage("Export finished!")
    def cancelPopulationCreation(self,*args,**kwargs):
        #print "CANCEL BUTTON PRESSED"
        self.population.setCancelFlag()
        #raise PoplibException("Population instantiation is cancelled")
    def preQuit(self,*args,**kwargs):
        "Returns true to avoid destroying, if necessary"
        if self.modified:
            if not self.askYesNo("Modifications to current population are not saved. Quit anyway?"):
                return True
        return False
        
    def quit(self,*args,**kwargs):
        #if self.modified:
        #    if not self.askYesNo("Modifications to current population is not saved. Proceed?"):
        #        return
        #self.quitManual()
        sys.exit(0)

    def quitManual(self,*args,**kwargs):
        debug("Making checks before quit")
        if self.modified:
            if not self.askYesNo("Modifications to current population are not saved. Quit anyway?"):
                return
        sys.exit(0)

    def about(self,*args,**kwargs):
        self.dialogMessage(ABOUT)

    def help(self,*args,**kwargs):
        if os.path.exists("UserGuide.txt"):
            HELP=open("UserGuide.txt","r").read()
        else:
            HELP="Please see the User Guide distributed with PopGUI."
        self.longDisplay("Using PopGUI",HELP)

    def message(self,*args,**kwargs):
        b=self.textview.get_buffer()
        msg=""
        for a in args:
            msg+=str(a)+"\n"
        for k in kwargs.keys():
            mag+=str(k)+":"+str(kwargs[k])
        rmsg=b.get_text(b.get_start_iter(),b.get_end_iter())+"\n"+msg
        rmsg=rmsg[-CONFIG["CONSOLEBUFFERLEN"]:]
        b.set_text(rmsg)

    def dialogMessage(self,msg):
        dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,msg)
        self.message(msg)
        dialog.run()
        dialog.destroy()
        
    def longDisplay(self,title,text,wtype="modal"):
        if wtype=="modal":
            popwindow = gtk.Dialog(title,self.window,gtk.DIALOG_MODAL)
        elif wtype=="dwp":
            popwindow = gtk.Dialog(title,self.window,gtk.DIALOG_DESTROY_WITH_PARENT)
        else:
            raise Exception("Unknown window type")
        popwindow.set_default_size(400,500)
        popwindow.set_title(title)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        popwindow.vbox.pack_start(scrolled_window, True, True, 0)
        scrolled_window.show()
        textview = gtk.TextView()
        textview.set_editable(0)
        textview.set_cursor_visible(0)
        textview.set_wrap_mode(gtk.WRAP_CHAR)
        textview.show()
        textview.get_buffer().set_text(text)
        scrolled_window.add_with_viewport(textview)
        popwindow.run()
        popwindow.destroy()

    def askYesNo(self,msg):
        dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK_CANCEL,msg)
        response=dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            return 1
        return 0

    def invalidStateWarning(self,msg=""):
        if msg:
            self.dialogMessage(msg)
        else:
            self.dialogMessage("Invalid state for operation (e.g. no population is created or loaded yet)")

    def newPopFromFile(self,modelfile):
        popfile=modelfile
        try:
            self.population=Population("",popfile)
            CONFIG["LASTMODELDIR"]=os.path.dirname(popfile)
            #self.message(reprMultiDictAsTXT(self.population.model.info["domdic"]))
            self.message("Model file '%s' is read successfully"%popfile)
            self.state="newpop"
            self.modified=1
            self.savefile=""
            self.setPopProp()
        except:
            self.dialogMessage("Cannot create population"+str(sys.exc_info()))
            i=sys.exc_info()
            print i
            print traceback.print_tb(i[2])
        saveConfig()

    def newPop(self,*args,**kwargs):
        if self.modified:
            if not self.askYesNo("Modifications to current population are not saved. Proceed?"):
                return
        filec=gtk.FileChooserDialog(title="Choose Model XMML file",parent=self.window,action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        filec.set_current_folder(CONFIG["LASTMODELDIR"])
        filter = gtk.FileFilter()
        filter.add_pattern("*.xml")
        filter.set_name(".xml")
        filec.add_filter(filter)
        filterall=gtk.FileFilter()
        filterall.add_pattern("*")
        filterall.set_name("All files")
        filec.add_filter(filterall)
        response=filec.run()
        if response == gtk.RESPONSE_OK:
            popfile= filec.get_filename()
        else:
            popfile=""
        filec.destroy()
        if not popfile:return
        try:
            self.population=Population("",popfile)
            CONFIG["LASTMODELDIR"]=os.path.dirname(popfile)
            #self.message(reprMultiDictAsTXT(self.population.model.info["domdic"]))
            self.message("Model file '%s' is read successfully"%popfile)
            self.state="newpop"
            self.modified=1
            self.savefile=""
            self.setPopProp()
        except:
            self.dialogMessage("Cannot create population due to following error:\n(%s)\n%s"%(str(sys.exc_info()[0]),str(sys.exc_info()[1])))
            i=sys.exc_info()
            print i
            print traceback.print_tb(i[2])
        saveConfig()

    def openPop(self,*args,**kwargs):
        if self.modified:
            if not self.askYesNo("Modifications to current population is not saved. Proceed?"):
                return
        if kwargs.has_key("fname"):
            popfile=kwargs["fname"]
        else:
            filec=gtk.FileChooserDialog(title="Choose population to load",parent=self.window,action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
            filec.set_current_folder(CONFIG["LASTPOPDIR"])
            filter = gtk.FileFilter()
            filter.add_pattern("*.pop")
            filter.set_name(".pop")
            filec.add_filter(filter)
            filterall=gtk.FileFilter()
            filterall.add_pattern("*")
            filterall.set_name("All files")
            filec.add_filter(filterall)
            response=filec.run()
            if response == gtk.RESPONSE_OK:
                popfile= filec.get_filename()
            else:
                popfile=""
            filec.destroy()
        if not popfile:return
        tmppop=pickle.load(open(popfile,"rb"))
        try:
            tmppopver=tmppop.version
        except:
            tmppopver="None"
        if VERSIONCHECKING:
            if tmppopver!=Population.CURRENTVERSION:
                self.dialogMessage("Version of the population (%s) is different from what the program currently supports(%s)"%(tmppopver,Population.CURRENTVERSION))
                return
        self.population=tmppop
        self.state=self.population.state
        self.savefile=popfile
        CONFIG["LASTPOPDIR"]=os.path.dirname(popfile)
        self.modified=0
        globalSetNumRegions(self.population.numregions)
        self.message("Population '%s' is read successfully"%popfile)

    def savePopAs(self,*args,**kwargs):
        self.savePop(saveas=1)

    def savePop(self,*args,**kwargs):
        if kwargs.has_key("saveas"):
            saveas=kwargs["saveas"]
        else:
            saveas=0
        if self.state=="init":
            self.invalidStateWarning()
            return
        if self.savefile and (not saveas):
            popfile=self.savefile
        else:
            filec=gtk.FileChooserDialog(title="Choose file to save population",parent=self.window,action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
            filec.set_current_folder(CONFIG["LASTPOPDIR"])
            filter = gtk.FileFilter()
            filter.add_pattern("*.pop")
            filter.set_name(".pop")
            filec.add_filter(filter)
            filterall=gtk.FileFilter()
            filterall.add_pattern("*")
            filterall.set_name("All files")
            filec.add_filter(filterall)
            response=filec.run()
            if response == gtk.RESPONSE_OK:
                popfile= filec.get_filename()
                if os.path.exists(popfile):
                    if not self.askYesNo("The file '%s' already exists. Overwrite?"%popfile):return
            else:
                popfile=""
            filec.destroy()
        if not popfile:return
        if popfile.lower()[-4:]!=".pop":
            popfile+=".pop"
        #if saveas and os.path.exists(popfile):
        #    if not self.askYesNo("The file '%s' already exists. Overwrite?"%popfile):return
        CONFIG["LASTPOPDIR"]=os.path.dirname(popfile)
        saveConfig()
        try:
            self.population.cleanUp()
            pickle.dump(self.population,open(popfile,"wb"))
            self.savefile=popfile
            self.message("Population is saved successfully into '%s'"%popfile)
            self.modified=0
        except:
            dialogMessage("Cannot save population"+str(sys.exc_info()))

    def showSummary(self,*args,**kwarg):
        if self.state=="init":
            self.invalidStateWarning("No population is created or loaded yet!")
            return
        self.longDisplay("Model Summary",(str(self.population.model)))

    def setPopProp(self,*args,**kwargs):
        if self.state=="init":
            self.invalidStateWarning("No population is created or loaded yet!")
            return
        PopPropDialog(self)

    def editRegions(self,*args,**kwargs):
        if self.state=="init":
            self.invalidStateWarning("No population is created or loaded yet!")
            return
        if self.population.numregions==0:
            self.invalidStateWarning("No Regions defined!")
            return
        EditRegionsDialog(self)

    def editConstants(self,*args,**kwargs):
        if self.state=="init":
            self.invalidStateWarning("No population is created or loaded yet!")
            return
        EditConstantsDialog(self)

    def editMemVars(self,*args,**kwargs):
        if self.state=="init":
            self.invalidStateWarning("No population is created or loaded yet!")
            return
        if self.population.numregions==0:
            self.invalidStateWarning("No Regions defined!")
            return
        EditMemVarsDialog(self)

    def instantiate(self,*args,**kwargs):
        if self.state=="init":
            self.invalidStateWarning("No population is created or loaded yet!")
            return
        if self.population.numregions==0:
            self.invalidStateWarning("No Regions defined!")
            return
        filec=gtk.FileChooserDialog(title="Choose file to save population instance (0.xml)",parent=self.window,action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        filec.set_current_folder(CONFIG["LASTXMLDIR"])
        filter = gtk.FileFilter()
        filter.add_pattern("*.xml")
        filter.set_name(".xml")
        filec.add_filter(filter)
        filterall=gtk.FileFilter()
        filterall.add_pattern("*")
        filterall.set_name("All files")
        filec.add_filter(filterall)
        response=filec.run()
        if response == gtk.RESPONSE_OK:
            popfile= filec.get_filename()
        else:
            popfile=""
        filec.destroy()
        if not popfile:return
        if popfile.lower()[-4:]!=".xml":
            popfile+=".xml"
        if os.path.exists(popfile):
            if not self.askYesNo("The file '%s' already exists. Overwrite?"%popfile):return
        CONFIG["LASTXMLDIR"]=os.path.dirname(popfile)
        saveConfig()
        self.message("Creating 0.xml ...")
        self.progbar.show()
        self.progbar.set_text("Instantiating ...")
        self.progbar.pulse()
        self.progbar.set_fraction(0)
        self.cancelpop.show()
        self.table.resize(5,1)
        try:
            self.table.attach(self.progbar,0,1,3,4)
        except:pass #perhaps second attempt!
        try:
            self.table.attach(self.cancelpop,0,1,4,5)
        except:pass #perhaps second attempt!
        #thread.start_new_thread(progwin.run,())
        #progwin.run()
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        resetGlobalMsg()
        outfile=open(popfile,"w")
        try:
            numagents,totaltime=self.population.instantiate(outfile,progbar=self.progbar)
        except PoplibException:
            msg="There was a problem while instantiating population:\n"+str(sys.exc_info()[1])
            try:
                msg+="\n"
                msg+=getGlobalMsg()
            except:
                pass
            self.dialogMessage(msg)
            i=sys.exc_info()
            print i
            print traceback.print_tb(i[2])
            self.progbar.hide()
            self.cancelpop.hide()
            self.table.resize(3,1)
            gtk.main_iteration_do(False)
            return
        except:
            msg="There was an unexpected problem while instantiating population:\n"+str(sys.exc_info()[1])
            try:
                msg+="\n"
                msg+=getGlobalMsg()
            except:
                pass
            self.dialogMessage(msg)
            i=sys.exc_info()
            print i
            print traceback.print_tb(i[2])
            self.progbar.hide()
            self.cancelpop.hide()
            self.table.resize(3,1)
            gtk.main_iteration_do(False)
            return
        finally:
            self.population.cleanUp()
            outfile.close()
        self.message("Successful. Number of agents created %d." % numagents)
        #open(popfile,"w").write(zeroxml)
        self.message("Population instance saved in %s." % popfile)
        self.cancelpop.hide()
        self.progbar.hide()
        self.table.resize(3,1)
        if numagents==0:
            self.dialogMessage("Congratulations. You have a useless population with no agents in %s."%popfile)
        else:
            self.dialogMessage("Congratulations. Population instance is saved in %s, with %d agents in it (in %d seconds)."%(popfile,numagents,totaltime))
        gtk.main_iteration_do(False)
class BasePopDialog:
    def __init__(self,title,parent,width=400,height=500,swexpand=True,swfill=True):
        #self.parent=parent
        #popwindow = gtk.Dialog(title,parent,gtk.DIALOG_MODAL)
        popwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #popwindow.set_transient_for(parent.window.window)
        popwindow.set_decorated(True)
        popwindow.set_parent_window(parent.window)
        popwindow.set_modal(True)
        popwindow.set_default_size(width,height)
        self.window=popwindow
        popwindow.connect("destroy", self.destroy)
        popwindow.set_title(title)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        #popwindow.vbox.pack_start(scrolled_window, True, True, 0)
        wbox=gtk.VBox(False, 0)
        mbox=gtk.HBox(False,0)
        bbox=gtk.HBox(False,0)
        self.wbox=wbox
        self.mbox=mbox
        self.bbox=bbox
        popwindow.add(wbox)
        mbox.pack_end(scrolled_window, swexpand, swfill, 0)
        wbox.pack_start(mbox, True, True, 0)
        wbox.pack_end(bbox, False, False, 0)
        scrolled_window.show()
        self.scrolled=scrolled_window
        cbutton = gtk.Button("Cancel")
        cbutton.connect_object("clicked", self.destroy, popwindow)
        cbutton.set_flags(gtk.CAN_DEFAULT)
        #popwindow.action_area.pack_end(cbutton, True, True, 0)
        bbox.pack_end(cbutton, False, False, 0)
        cbutton.grab_default()
        cbutton.show()
        scbutton=gtk.Button("Update and close")
        self.scbutton=scbutton
        scbutton.connect("clicked",self.saveclose)
        #popwindow.action_area.pack_start(scbutton)
        bbox.pack_end(scbutton, False, False, 0)
        scbutton.show()
        bbox.show()
        mbox.show()
        wbox.show()
        popwindow.set_decorated(True)
        popwindow.show()
        self.vadj=self.scrolled.get_vadjustment()
        self.hadj=self.scrolled.get_hadjustment()

    def focus_in(self,widget, event):
        vadj=self.vadj
        hadj=self.hadj
        alloc = widget.get_allocation()        
        if alloc.y < vadj.value:
            vadj.set_value(alloc.y)
        elif alloc.y > (vadj.value + vadj.page_size-20):
            vadj.set_value(vadj.upper-vadj.page_size+40)
            #vadj.set_value(min(alloc.y, vadj.upper-vadj.page_size))
        if alloc.x < hadj.value or alloc.x > (hadj.value + hadj.page_size-20):
            hadj.set_value(min(alloc.x, hadj.upper-hadj.page_size))

    def askYesNo(self,msg):
        dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK_CANCEL,msg)
        response=dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            return 1
        return 0

    def dialogMessage(self,msg):
        dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,msg)
        #self.message(msg)
        dialog.run()
        dialog.destroy()

    def destroy(self,*args,**kwargs):
        self.window.destroy()

    def saveclose(self,*args,**kwargs):
        pass

class PopPropDialog_ImportSubModel(BasePopDialog):
    def __init__(self,parentobj,parentpopprop,newpop,newmod,popfile):
        title="Import Population"
        self.parentobj=parentobj
        self.parentpopprop=parentpopprop
        self.newpop=newpop
        self.newmod=newmod
        self.popfile=popfile
        self.proceed=0
        BasePopDialog.__init__(self,title,parentpopprop.window)
        self.window.set_transient_for(parentpopprop.window)
        self.scbutton.hide()
        donebutton=gtk.Button("Proceed with import")
        donebutton.connect("clicked",self.done)
        donebutton.show()
        self.bbox.pack_end(donebutton, False, False, 0)#table.attach(importbutton,0,1,3,4,xoptions=0,yoptions=0)
        table = gtk.Table(4, 2, False)
        self.scrolled.add_with_viewport(table)
        table.show()
        lname=gtk.Label("The model of population imported has more than one nested model. Choose the whole population, or parts corresponding to a nested model.")
        lname.set_line_wrap(True)
        lname.show()
        table.attach(lname,0,2,0,1)
        self.checkAll=gtk.CheckButton(label="Use whole population")
        self.checkAll.connect("clicked",self.checkAllClick)
        self.checkAll.show()
        table.attach(self.checkAll,1,2,1,2)
        self.chooseLabel=gtk.Label("Choose nested-model:")
        self.chooseLabel.show()
        table.attach(self.chooseLabel,0,1,2,3)
        self.choose=gtk.combo_box_new_text() 
        self.choose.show()
        self.revmodmap={}
        for sm in self.newmod.submodels.keys():
            lab=sm
            if self.newmod.submodels[sm]:
                lab=self.newmod.submodels[sm]
            self.revmodmap[lab]=sm
            self.choose.append_text(lab)
        self.choose.set_active(0)
        table.attach(self.choose,1,2,2,3)
        
    def checkAllClick(self,*args,**kw):
        if self.checkAll.get_property("active"):
            self.choose.hide()
            self.chooseLabel.hide()
        else:
            self.choose.show()
            self.chooseLabel.show()
    def done(self,*args,**kw):
        if self.checkAll.get_property("active"):
            self.parentpopprop.doImport(self.newpop,self.popfile)
        else:
            i=self.choose.get_active_iter()
            s=self.choose.get_model().get_value(i,0)
            submodelfile=self.revmodmap[s]
            self.parentpopprop.doImport(self.newpop,self.popfile,submodelfile=submodelfile)
        self.window.destroy()
        

class PopPropDialog(BasePopDialog):
    def __init__(self,parentobj):
        title="Population properties"
        self.parentobj=parentobj
        BasePopDialog.__init__(self,title,parentobj.window)
        table = gtk.Table(4, 2, False)
        self.scrolled.add_with_viewport(table)
        table.show()
        lname=gtk.Label("Name of population")
        table.attach(lname,0,1,0,1)
        tname=gtk.Entry(max=50)
        table.attach(tname,1,2,0,1)
        lname.show()
        tname.show()
        lnumreg=gtk.Label("Number of regions")
        table.attach(lnumreg,0,1,1,2)
        tnumreg=gtk.Entry(max=5)
        table.attach(tnumreg,1,2,1,2)
        lnumreg.show()
        tnumreg.show()
        tname.set_text(parentobj.population.name)
        tnumreg.set_text(str(parentobj.population.numregions))
        lmodelfile=gtk.Label("Model file")
        lmodelfile.show()
        table.attach(lmodelfile,0,1,2,3)
        lmodelfilename=gtk.Label(parentobj.population.modelfile)
        lmodelfilename.show()
        table.attach(lmodelfilename,1,2,2,3)
        importbutton=gtk.Button("Import ...")
        importbutton.connect("clicked",self.importPop)
        importbutton.show()
        self.bbox.pack_end(importbutton, False, False, 0)#table.attach(importbutton,0,1,3,4,xoptions=0,yoptions=0)
        self.table=table
        self.tnumreg=tnumreg
        self.tname=tname

    def importPop(self,*args,**kw):
        filec=gtk.FileChooserDialog(title="Choose population to import from",parent=self.window,action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        filec.set_current_folder(CONFIG["LASTPOPDIR"])
        filter = gtk.FileFilter()
        filter.add_pattern("*.pop")
        filter.set_name(".pop")
        filec.add_filter(filter)
        filterall=gtk.FileFilter()
        filterall.add_pattern("*")
        filterall.set_name("All files")
        filec.add_filter(filterall)
        response=filec.run()
        if response == gtk.RESPONSE_OK:
            popfile= filec.get_filename()
        else:
            popfile=""
        filec.destroy()
        if not popfile:return
        pop=pickle.load(open(popfile,"rb"))
        debug("Population is read")
        #Now re-read the model to see if it is nested
        try:
            mod=pop.model#Model(pop.modelfile,xmlregistry=pop.getModelXMLRegistry())
        except IOError:
            self.parentobj.dialogMessage("Error when trying to access the model file (of the population to be imported from): %s"%pop.modelfile)
            return
        if mod.submodels:
            print mod.submodels
            PopPropDialog_ImportSubModel(self.parentobj,self,pop,mod,popfile)
            return
        else:
            print "No submodels. Importing directly"
            self.doImport(pop,popfile)
            self.parentobj.dialogMessage("Import successful")
    def doImport(self,pop,popfile,submodelfile=""):
        if pop.getNumRegions()!=self.parentobj.population.getNumRegions():
            self.dialogMessage("Number of regions (%d) is different from current population's (%d)"%(pop.getNumRegions(),self.parentobj.population.getNumRegions()))
            return
        debug("Number of regions match. Continuing import")
        if submodelfile:
            mod=Model(submodelfile,xmlregistry=pop.getModelXMLRegistry())
        else:
            mod=pop.model#self.parentobj.population.model
        for r in range(0,self.parentobj.population.numregions):
            regfrom=pop.regions[r]
            regto=self.parentobj.population.regions[r]
            for a in mod.agents:#self.parentobj.population.model.agents:
                ato=regto.model.getAgentByName(a.name)
                afrom=regfrom.model.getAgentByName(a.name)
                if ato==None:
                    debug("Agent named %s is missing in the current population, skipping."% a.name)
                    continue  
                if not submodelfile:#do region setting only when global import is being done
                    regto.setNumAgents(a.name,regfrom.getNumAgents(a.name))
                for mvto in ato.memvars:
                    mvcheck=a.getMemVarByName(mvto.name)
                    if mvcheck==None:continue
                    mvfrom=afrom.getMemVarByName(mvto.name)
                    if mvfrom==None:
                        debug("Memvar %s->%s is missing in imported population, skipping" %(a.name,mvto.name))
                        continue
                    self._copyMemVar(mvfrom,mvto)
        for c in self.parentobj.population.model.constants:
            x=mod.getConstantByName(c.name)#pop.model.getConstantByName(c.name)
            if x==None:
                debug("Constant %s is missing in the imported population"%c.name)
            else:
                self.parentobj.population.model.setConstant(c.name,str(x.getExpression()))
        self.dialogMessage("Population specifications are imported successfully")
        submsg=""
        if submodelfile:
            submsg=" (for nested-model %s only)"%submodelfile
        self.parentobj.message("Population specifications are imported from %s%s successfully"%(popfile,submsg))
    def doImportBAK(self,pop,popfile,submodelfile=""):
        if pop.getNumRegions()!=self.parentobj.population.getNumRegions():
            self.dialogMessage("Number of regions (%d) is different from current population's (%d)"%(pop.getNumRegions(),self.parentobj.population.getNumRegions()))
            return
        debug("Number of regions match. Continuing import")
        for r in range(0,self.parentobj.population.numregions):
            regfrom=pop.regions[r]
            regto=self.parentobj.population.regions[r]
            for a in self.parentobj.population.model.agents:
                ato=regto.model.getAgentByName(a.name)
                afrom=regfrom.model.getAgentByName(a.name)
                if afrom==None:
                    debug("Agent named %s is missing in the imported population, skipping."% a.name)
                    continue  
                regto.setNumAgents(a.name,regfrom.getNumAgents(a.name))
                for mvto in ato.memvars:
                    mvfrom=afrom.getMemVarByName(mvto.name)
                    if mvfrom==None:
                        debug("Memvar %s->%s is missing in imported population, skipping" %(a.name,mvto.name))
                        continue
                    self._copyMemVar(mvfrom,mvto)
        for c in self.parentobj.population.model.constants:
            x=pop.model.getConstantByName(c.name)
            if x==None:
                debug("Constant %s is missing in the imported population"%c.name)
            else:
                self.parentobj.population.model.setConstant(c.name,x.getValue())
        self.dialogMessage("Population specifications are imported successfully")
        self.parentobj.message("Population specifications are imported from %s successfully"%popfile)
        
    def _copyMemVar(self,mvfrom,mvto):
        for k in mvfrom.getKeys():
            vname,vtype=k
            fromform=mvfrom.getForm(vname)
            try:
                toform=mvto.getForm(vname)
            except:
                debug("Problem copying initform %s. Possibly missing from the current model."%vname)
                continue
            if isinstance(fromform,MemVar):#Will need to recurse into this var!
                self._copyMemVar(fromform,toform)
            else:
                try:
                    toform.setFormStr(fromform.getFormStr())
                except:
                    debug("Problem when copying initform %s"%vname)
                    i=sys.exc_info()
                    print i
                    print traceback.print_tb(i[2])
                    

    def saveclose(self,*args,**kwargs):
        try:
            numreg=int(self.tnumreg.get_text())
        except:
            self.dialogMessage("Invalid number for regions")
            return
        self.parentobj.population.name=self.tname.get_text()
        self.parentobj.population.setNumRegions(numreg)
        self.window.destroy()
        self.parentobj.modified=1

class EditRegionsDialog(BasePopDialog):
    def __init__(self,parentobj):
        title="Regions"
        self.parentobj=parentobj
        BasePopDialog.__init__(self,title,parentobj.window,width=800,height=600)
        table = gtk.Table(len(self.parentobj.population.model.agents)+1, self.parentobj.population.numregions+1, False)
        self.scrolled.add_with_viewport(table)
        table.show()
        l=gtk.Label("NUMBER OF AGENT\nIN EACH REGION:")
        l.show()
        table.attach(l,0,1,0,1)
        for r in range(0,self.parentobj.population.numregions):
            l=gtk.Label("Region %d"%(r+1))
            #l.set_alignment(0,0)
            l.show()
            table.attach(l,r+1,r+2,0,1)
        for a in range(len(self.parentobj.population.model.agents)):
            aname=self.parentobj.population.model.agents[a].name
            l=gtk.Label(aname)
            #l.set_alignment(0,0)
            l.show()
            table.attach(l,0,1,a+1,a+2)
        editwidgets={}
        for r in range(0,self.parentobj.population.numregions):
            for a in range(len(self.parentobj.population.model.agents)):
                aname=self.parentobj.population.model.agents[a].name
                reg=self.parentobj.population.regions[r]
                t=gtk.Entry(max=10)
                t.set_width_chars(5)
                #t.set_alignment(0,0)
                table.attach(t,r+1,r+2,a+1,a+2)
                t.show()
                t.set_text(str(reg.getNumAgents(aname)))
                t.connect('focus_in_event', self.focus_in)
                editwidgets[(r,aname)]=t
        self.editwidgets=editwidgets
        self.table=table
        dupbutton=gtk.Button("Replicate 1st region")
        dupbutton.connect("clicked",self.duplicate)
        self.bbox.pack_end(dupbutton,False,False,0)
        dupbutton.show()
    def duplicate(self,*args,**kwargs):
        for a in range(len(self.parentobj.population.model.agents)):
            aname=self.parentobj.population.model.agents[a].name
            numa=int(self.editwidgets[(0,aname)].get_text())
            for r in range(1,self.parentobj.population.numregions):
                self.editwidgets[(r,aname)].set_text(str(numa))
    def saveclose(self,*args,**kwargs):
        nums={}
        for k in self.editwidgets.keys():
            r,aname=k
            reg=self.parentobj.population.regions[r]
            try:
                #print "WIDGET CONTENT:*%s*",self.editwidgets[k].get_text()
                nums[k]=int(self.editwidgets[k].get_text())
                if nums[k]<0:
                    self.dialogMessage("Entry for agent '%s' at region %d is a negative number"%(aname,(r+1)))
                    return
            except:
                self.dialogMessage("Entry for agent '%s' at region %d is not a number"%(aname,(r+1)))
                return
        for k in self.editwidgets.keys():
            r,aname=k
            self.parentobj.population.regions[r].setNumAgents(aname,nums[k])
            #print "SET NUM AGENTS :",r,aname,nums[k]
        self.window.destroy()
        self.parentobj.modified=1

class RegionCopyDialog(BasePopDialog):
    def __init__(self,parentobj,numregions):
        title="Copy region"
        self.parentobj=parentobj
        self.numregions=numregions
        BasePopDialog.__init__(self,title,parentobj.window,height=40,swexpand=True,swfill=True)
        table = gtk.Table(1, 2, False)
        self.scrolled.add_with_viewport(table)
        table.show()
        lf=gtk.Label("Copy from region  ")
        lf.show()
        table.attach(lf,0,1,0,1)
        tf=gtk.combo_box_entry_new_text()#gtk.Entry(max=5)
        tf.show()
        table.attach(tf,1,2,0,1)
        tf.set_active(0)
        lt=gtk.Label("Copy To region  ")
        lt.show()
        table.attach(lt,0,1,1,2)
        tt=gtk.combo_box_entry_new_text()#gtk.Entry(max=5)
        tt.show()
        tt.set_active(0)
        table.attach(tt,1,2,1,2)
        for r in range(numregions):
            tf.append_text(str(r+1))
            tt.append_text(str(r+1))
        tt.append_text("All")
        self.table=table
        self.tt=tt
        self.tf=tf
        self.scbutton.set_label("Copy Region")

    def saveclose(self,*args,**kwargs):
        targets=[]
        try:
            tf=int(self.tf.get_active_text())
            if tf>self.numregions:
                self.dialogMessage("Invalid choice for source region")
                return
            if self.tt.get_active_text()=="All":
                for i in range(self.numregions):
                    if i!=tf-1:
                        targets.append(i)
            else:
                tt=int(self.tt.get_active_text())
                if tf==tt or tt>self.numregions:
                    self.dialogMessage("Invalid choice for target region")
                    return
                targets.append(tt-1)
        except:
            i=sys.exc_info()
            print i
            print traceback.print_tb(i[2])
            self.dialogMessage("Invalid choice")
            return
        #if tf==tt or tt>self.numregions or tf>self.numregions:
        #    self.dialogMessage("Invalid choice")
        #    return
        self.window.destroy()
        for t in targets:
            self.parentobj.duplicateRegion(tf-1,t)

class EditMemVarsDialog(BasePopDialog):
    def __init__(self,parentobj):
        self.parentobj=parentobj
        title="Memory Variables"
        BasePopDialog.__init__(self,title,parentobj.window,width=800,height=600)
        #Create validate button
        valbutton=gtk.Button("Validate")
        valbutton.connect("clicked",self.validate)
        self.bbox.pack_end(valbutton,False,False,0)
        valbutton.show()
        pop=self.parentobj.population
        #create tree view
        types=[str,str,str]
        for r in range(0,pop.numregions):
            types.append(str)
            types.append(bool)
        treestore=apply(gtk.TreeStore,types)
        #create tree store information
        treeagentnodes={}
        for a in pop.model.agents:
            r=self._emptyrow(a.name)
            treeagentnodes[a.name]=treestore.append(None,r)
        #Done
        treeview = gtk.TreeView(treestore)
        agentcell = gtk.CellRendererText()
        agentcolumn=gtk.TreeViewColumn("Agent/Variable")
        agentcolumn.set_sort_column_id(0)
        agentcolumn.set_sort_order(gtk.SORT_ASCENDING)
        treeview.append_column(agentcolumn)
        agentcolumn.pack_start(agentcell,True)
        agentcolumn.add_attribute(agentcell,"text",0)
        if False: #For debug purposes
            mvcell = gtk.CellRendererText()
            mvcolumn=gtk.TreeViewColumn("Var Field")
            treeview.append_column(mvcolumn)
            mvcolumn.pack_start(mvcell,True)
            mvcolumn.add_attribute(mvcell,"text",1)
        svcell = gtk.CellRendererText()
        svcolumn=gtk.TreeViewColumn("Var Type")
        treeview.append_column(svcolumn)
        svcolumn.pack_start(svcell,True)
        svcolumn.add_attribute(svcell,"text",2)
        treeview.show()
        skip=3
        self.skip=skip
        self.treestore=treestore
        self.treeview=treeview
        #self.mbox.pack_start(treeview,False,False,0)
        viewport=gtk.Viewport()
        viewport.add(treeview)
        #self.mbox.pack_end(treeview)
        viewport.show()
        self.viewport=viewport
        self.scrolled.add(viewport)
        for rn in range(0,pop.numregions):
            rcell = gtk.CellRendererText()
            rcolumn=gtk.TreeViewColumn("Region %d"%(rn+1))
            treeview.append_column(rcolumn)
            rcolumn.pack_start(rcell,True)
            rcolumn.add_attribute(rcell,"text",(rn*2+skip))
            rcolumn.add_attribute(rcell,"editable",(rn*2+skip+1))
            rcell.connect('edited', self.edited_cb, (treestore, rn*2+skip))
            #rcolumn.set_attributes(cell-background=1)
        editrows={}
        self.editrows=editrows
        self.memvarmatrix={}
        for a in pop.model.agents:
            editrows[a.name]={}
            #for mvo in a.memvarorder:
            #    mv=a.getMemVarByOriginalName(mvo)
            for mv in a.memvars:
                editrows[a.name][mv.name]={}
                parentrow=treeagentnodes[a.name]
                rows=self.addVar(mv,a,parentrow)
                for rk in rows:
                    editrows[a.name][mv.name][rk]=rows[rk]
        for col in treeview.get_columns():
            col.set_resizable(True)
        #treestore.set_sort_column_id(2,gtk.SORT_ASCENDING)
        #treestore.set_sort_column_id(1,gtk.SORT_ASCENDING)
        treeview.connect("row-activated",self.rowShow,"row-activated")
        treeview.connect("cursor-changed",self.rowShow,"cursor-changed")
        treeview.set_enable_tree_lines(True)
        treeview.set_enable_search(False)
        expandbutton=gtk.Button("Expand All")
        expandbutton.connect("clicked",self.expandAll)
        self.bbox.pack_end(expandbutton,False,False,0)
        expandbutton.show()
        self.expandbutton=expandbutton
        self.expanded=False
        rcopybutton=gtk.Button("Region copy")
        rcopybutton.connect("clicked",self.regionCopy)
        self.bbox.pack_end(rcopybutton,False,False,0)
        rcopybutton.show()
        helpbutton=gtk.Button("Syntax help")
        helpbutton.connect("clicked",self.help)
        self.bbox.pack_end(helpbutton,False,False,0)
        helpbutton.show()
        if EVALUATOR:
            expbutton=gtk.Button("Evaluate expression")
            expbutton.connect("clicked",self.evaluate)
            self.bbox.pack_end(expbutton,False,False,0)
            expbutton.show()
            teext=gtk.Entry(max=250)
            teext.set_width_chars(40)
            self.bbox.pack_end(teext,False,False,0)
            teext.show()
            self.teext=teext
            teaname=gtk.Entry(max=50)
            teaname.set_width_chars(10)
            self.bbox.pack_end(teaname,False,False,0)
            #teaname.show()
            self.teaname=teaname
            teaname.set_text(pop.model.agents[0].name)
    def evaluate(self,*args,**kwargs):
        try:
            exp=self.teext.get_text()
            aname=self.teaname.get_text()
            pop=self.parentobj.population
            a=pop.model.getAgentByName(self.teaname.get_text())
            ai=AgentInstance(pop.model,a.name,pop.regions[0],0,1)
            f=BaseForm("double",parent=a.memvars[-1])#parent=DummyMemVar())#,
            f.setFormStr(exp)
            mv=MemVarRegistry(a,ai)
            for x in a.memvars:
                mv.valmap[x.name]=DummyMemVar()
            rv=f._instantiate(f.form,fixtype=0,globalmsgreg=0,usealternatethis=1,alternatethis=mv)
            self.dialogMessage("Evaluated to:\n"+str(rv))
        except:
            i=sys.exc_info()
            traceback.print_tb(i[2])
            self.dialogMessage("Error in evaluation:\n"+str(i))
            
    def help(self,*args,**kwargs):
        self.parentobj.longDisplay("Help for memory initialization entry format",INITFORMHELP,wtype="dwp")

    def rowShow(self,*args,**kwargs):#treeview, path, view_column,*args,**kwargs):
        debug( "Scrolling",args,kwargs)
        #path=self.treeview.get_selection().get_selected()[1]
        #print path
        #tp=self.treestore.get_path(path)
        curs=self.treeview.get_cursor()
        rect=self.treeview.get_background_area(curs[0],curs[1])
        wc=self.treeview.widget_to_tree_coords(rect.x, rect.y)
        #debug(curs,(rect.x,rect.x,rect.width,rect.height),wc)
        #self.treeview.scroll_to_cell(tp)

        vadj=self.vadj
        hadj=self.hadj
        x,y = wc
        if y < vadj.value:
            vadj.set_value(y)
        elif y > (vadj.value + vadj.page_size-40):
            vadj.set_value(vadj.upper-vadj.page_size+40)
            #vadj.set_value(min(alloc.y, vadj.upper-vadj.page_size))
        if x < hadj.value or x > (hadj.value + hadj.page_size-20):
            hadj.set_value(min(x, hadj.upper-hadj.page_size))
        
        #self.focus_in(self.treeview.get_selection().get_selected()[0],None)
        #self.treeview.scroll_to_cell(path)

    def regionCopy(self,*args,**kwargs):
        RegionCopyDialog(self,self.parentobj.population.numregions)

    def _duplicateRecurse(self,tf,tt,what):
        if type(what)==dict:
            for w in what.values():
                self._duplicateRecurse(tf,tt,w)
        else:
            path=self.treestore.get_path(what)
            src=self.treestore[path][tf*2+self.skip]                    
            self.treestore[path][tt*2+self.skip]=str(src)
            debug( "COPYING",what,src)

    def duplicateRegion(self,tf,tt):
        for a in self.editrows.values():
            for m in a.values():
                self._duplicateRecurse(tf,tt,m)
        debug("Copy region finished")

    def _emptyrow(self,aname,recurse=""):
        row=[aname,str(recurse),""]
        for r in range(self.parentobj.population.numregions):
            row.append("")
            row.append(False)#editable property
        return row

    def addVar(self,mv,a,parentr,recurse=[]):
        pop=self.parentobj.population
        skip=self.skip
        parentrow=parentr
        rows={}
        if not mv.isSimple():
            row=self._emptyrow(mv.originalname,recurse=recurse)
            row[2]=mv.originaltype
            parentrow=self.treestore.append(parentrow,row)
        for k in mv.getKeys():
            vname,vtype=k
            initform=mv.getForm(vname)
            if isinstance(initform,MemVar):#Will need to recurse into this var!
                #row=[]
                rows[vname]=self.addVar(initform,a,parentrow,recurse=recurse+[mv.originalname])
                #editable=0
            else:#NO NEED TO RECURSE 
                row=self._emptyrow(a.name,recurse=recurse)
                for rn in range(0,pop.numregions):
                    reg=pop.regions[rn]
                    row[0]=vname#no need to repeat agent name?
                    row[2]=vtype
                    editable=1
                    if mv.isSpecial():
                        row[2]+="(SPECIAL)"
                        editable=0
                    else:
                        if not mv.isSimple() and vname=="array length":#HACK to make ARRAY LENGTH more visible
                            row[0]=row[0].upper()
                        ra=reg.model.getAgentByName(a.name)
                        #debug("SEEKING ANAME",a.name," MVNAME",mv.name," VNAME ",vname,"WITH REC ",recurse, "##VARNAMES",a.getMemVarNames())
                        #debug("AddVar attempting",recurse,a.name,mv.name,vname)
                        if not recurse:
                            rmv=ra.getMemVarByName(mv.name)
                            content=rmv.getForm(vname).getFormStr()
                        else:
                            rmv=ra.getMemVarByOriginalName(recurse[0])
                            for rec in recurse[1:]:
                                rmv=rmv.getForm(rec)
                            if(rmv):
                                content=rmv.getForm(mv.originalname).getForm(vname).getFormStr()
                            else:
                                raise Exception("Memory variable cannot be found:%s %s %s"%(mv.originalname,vname,str(recurse)))#content = ""
                        row[rn*2+skip]=content
                        row[rn*2+skip+1]=True
                        if mv.static and vname=="array length":
                            if isinstance(mv.static,Constant):
                                row[2]="%s(CONSTANT)"%(vtype)
                                row[rn*2+skip]=mv.static.getValue()
                            else:
                                row[2]="%s(STATIC)"%(vtype)
                                row[rn*2+skip]=str(mv.static)
                            row[rn*2+skip+1]=False
                            editable=0
                trow=self.treestore.append(parentrow,row)
                if editable:
                    rows[vname]=trow
                    self.memvarmatrix[(a.name,mv.name,mv.originalname,tuple(recurse),vname)]=trow
        return rows
        
    def expandAll(self,*args,**kwargs):
        if not self.expanded:
            self.treeview.expand_all()
            self.expanded=True
            self.expandbutton.set_label("Collapse All")
        else:
            self.treeview.collapse_all()
            self.expanded=False
            self.expandbutton.set_label("Expand All")

    def edited_cb(self,cell, path, new_text, user_data):
        liststore, column = user_data
        #print path
        liststore[path][column] = new_text
        return

    def validateOLD(self,*args,**kwargs):
        for k in self.memvarmatrix.keys():
            aname,mvname,mvoname,recurse,vname=k
            trow=self.memvarmatrix[k]
            regionforms={}
            for r in range(len(self.parentobj.population.regions)):
                txt=self.treestore[trow][r*2+3]
                regionforms[r]=txt
                #debug("SAVENEW [%s]"%(str(k)),aname,"%s(%s)"%(mvname,mvoname),recurse,vname,regionforms)
                reg=self.parentobj.population.regions[r]
                ra=reg.model.getAgentByName(aname)
                if recurse:
                    mv=ra.getMemVarByOriginalName(recurse[0])
                    for rec in recurse[1:]:
                        mv=mv.getForm(rec)
                    try:
                        mv=mv.getForm(mvoname)
                    except Exception,e:
                        print "Key error",aname,"%s(%s)"%(mvname,mvoname),recurse,vname
                        print mv.initform.info.keys()
                        raise e
                else:
                    mv=ra.getMemVarByName(mvname)
                try:
                    mv.validateForm(vname, txt)
                except:
                    i=sys.exc_info()
                    print i
                    print traceback.print_tb(i[2])
                    self.dialogMessage("VALIDATION ERROR: %s\n%s"%(i,traceback.print_tb(i[2])))
                    return
        self.dialogMessage("Validated")

    def validate(self,*args,**kwargs):
        for k in self.memvarmatrix.keys():
            aname,mvname,mvoname,recurse,vname=k
            trow=self.memvarmatrix[k]
            regionforms={}
            for r in range(len(self.parentobj.population.regions)):
                txt=self.treestore[trow][r*2+3]
                regionforms[r]=txt
                #debug("SAVENEW [%s]"%(str(k)),aname,"%s(%s)"%(mvname,mvoname),recurse,vname,regionforms)
                reg=self.parentobj.population.regions[r]
                ra=reg.model.getAgentByName(aname)
                if recurse:
                    mv=ra.getMemVarByOriginalName(recurse[0])
                    for rec in recurse[1:]:
                        mv=mv.getForm(rec)
                    try:
                        mv=mv.getForm(mvoname)
                    except Exception,e:
                        print "Key error",aname,"%s(%s)"%(mvname,mvoname),recurse,vname
                        print mv.initform.info.keys()
                        raise e
                else:
                    mv=ra.getMemVarByName(mvname)
                mv.setCandidate(vname,txt)
        for r in self.parentobj.population.regions:
            for a in r.model.agents:
                try:
                    a.validateReferenceDependencies(use="candidates")
                except:
                    i=sys.exc_info()
                    print i
                    print traceback.print_tb(i[2])
                    #self.dialogMessage("VALIDATION ERROR in agent %s: %s\n%s"%(a.name,i,traceback.print_tb(i[2])))
                    self.dialogMessage("VALIDATION ERROR in agent %s: \n %s"%(a.name,i[1]))
                    return
        for r in self.parentobj.population.regions:
            for a in r.model.agents:
                debug("Dependencies of agent %s : %s"%(a.name,str(a.depends)))
            debug("Agent init order for region %d : %s" %(r.regionid+1,str(r.agentinitorder)))
        self.dialogMessage("Validated")
        
    def saveclose(self,*args,**kwargs):
        for k in self.memvarmatrix.keys():
            aname,mvname,mvoname,recurse,vname=k
            trow=self.memvarmatrix[k]
            regionforms={}
            for r in range(len(self.parentobj.population.regions)):
                txt=self.treestore[trow][r*2+3]
                regionforms[r]=txt
                debug("SAVENEW [%s]"%(str(k)),aname,"%s(%s)"%(mvname,mvoname),recurse,vname,regionforms)
                reg=self.parentobj.population.regions[r]
                ra=reg.model.getAgentByName(aname)
                if recurse:
                    mv=ra.getMemVarByOriginalName(recurse[0])
                    for rec in recurse[1:]:
                        mv=mv.getForm(rec)
                    try:
                        mv=mv.getForm(mvoname)
                    except Exception,e:
                        print "Key error",aname,"%s(%s)"%(mvname,mvoname),recurse,vname
                        print mv.initform.info.keys()
                        raise e
                else:
                    mv=ra.getMemVarByName(mvname)
                mv.setForm(vname, txt)
        self.window.destroy()
        self.parentobj.modified=1

class EditConstantsDialog(BasePopDialog):
    def __init__(self,parentobj):
        self.parentobj=parentobj
        title="Environment Constants"
        BasePopDialog.__init__(self,title,parentobj.window,width=800,height=600)
        #Create validate button
        valbutton=gtk.Button("Validate")
        valbutton.connect("clicked",self.validate)
        self.bbox.pack_end(valbutton,False,False,0)
        valbutton.show()
        pop=self.parentobj.population
        treestore=gtk.TreeStore(str,str,bool)
        cmap={}
        for c in pop.model.constants:
            r=[c.name,c.getExpression(),True]
            cmap[c.name]=treestore.append(None,r)
        treeview = gtk.TreeView(treestore)
        cnamescell = gtk.CellRendererText()
        cnamescolumn=gtk.TreeViewColumn("Constant")
        treeview.append_column(cnamescolumn)
        cnamescolumn.pack_start(cnamescell,True)
        cnamescolumn.add_attribute(cnamescell,"text",0)
        cvalscell = gtk.CellRendererText()
        cvalscolumn=gtk.TreeViewColumn("Value")
        treeview.append_column(cvalscolumn)
        cvalscolumn.pack_start(cvalscell,True)
        cvalscolumn.add_attribute(cvalscell,"text",1)
        cvalscolumn.add_attribute(cvalscell,"editable",2)
        cvalscell.connect('edited', self.edited_cb, (treestore, 1))
        viewport=gtk.Viewport()
        viewport.add(treeview)
        viewport.show()
        treeview.show()
        self.viewport=viewport
        self.scrolled.add(viewport)
        self.treeview=treeview
        self.treestore=treestore
        self.cmap=cmap

    def edited_cb(self,cell, path, new_text, user_data):
        liststore, column = user_data
        liststore[path][column] = new_text
        return

    def validate(self,*args,**kwargs):
        pop=self.parentobj.population
        for c in self.cmap.keys():
            path=self.treestore.get_path(self.cmap[c])
            txt=self.treestore[path][1]
            def getAgentCountGlobal(aname):
                if not type(aname)==str:raise Exception("Agent name must be a string in getAgentCount()")
                return 0
            try:
                pop.model.getConstantByName(c).getValue(alternate=txt)
            except:
                self.dialogMessage("Error in constant %s : %s\n%s"%(c,txt,sys.exc_info()[1]))
                return
        self.dialogMessage("Validated")

    def saveclose(self,*args,**kwargs):
        pop=self.parentobj.population
        for c in self.cmap.keys():
            path=self.treestore.get_path(self.cmap[c])
            txt=self.treestore[path][1]
            try:
                v=txt#eval(txt)
                pop.model.setConstant(c,v)
            except Exception,e:
                self.dialogMessage("Error in constant %s : %s"%(c,txt))
                print e
                print traceback.print_exc()
                return
        self.window.destroy()
        self.parentobj.modified=1

USAGE="""Usage:
  %s [-dh] [<population.pop>]
Options:
  -d : turn on debugging output
  -h : print usage help
  -i : disable version checking when opening populations
  -v : print program version

<population.pop>: load the population when program starts
"""%sys.argv[0]
def handler(signum, frame):
    print 'Signal handler called with signal', signum
    raise IOError, "Couldn't open device!"

# Set the signal handler and a 5-second alarm
if __name__=="__main__":
    gui=PopGUI()
    optlist, args = getopt.getopt(sys.argv[1:],"dhive")
    #print optlist
    #print args
    global DEBUG
    setDebug(0)
    EVALUATOR=1
    for o in optlist:
        o,v=o
        if o=="-d":
            print "Debugging output is turned on"
            setDebug(1)
        if o=="-h":
            print USAGE
            sys.exit(0)
        if o=="-v":
            print VERSION
            sys.exit(0)
        if o=="-i":
            VERSIONCHECKING=0
        if o=="-e":
            EVALUATOR=1
    fname=""
    if len(args)>0:
        fname=os.path.expanduser(args[0])
    if HASSIGNAL:
        signal.signal(signal.SIGTERM, gui.quit)
        debug("Signal is set")
    gui.start(fname=fname)

