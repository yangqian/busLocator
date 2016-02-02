#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bus import Bus
from PySide import QtCore, QtGui
import signal
import bustray_rc
import math
#import threading

class Window(QtGui.QWidget):
    def drawBus(self,nx,ny,angle,qp):
      ang=angle/180.*math.pi
      angd=15
      line=8
      headx=+math.sin(ang)*line+nx
      heady=-math.cos(ang)*line+ny
      tailx=-math.sin(ang)*line+nx
      taily=+math.cos(ang)*line+ny
      wing1x=-math.sin(ang+angd+math.pi)*line+headx
      wing1y=+math.cos(ang+angd+math.pi)*line+heady
      wing2x=-math.sin(ang-angd+math.pi)*line+headx
      wing2y=+math.cos(ang-angd+math.pi)*line+heady
      qp.drawLine(headx,heady,tailx,taily)
      qp.drawLine(headx,heady,wing1x,wing1y)
      qp.drawLine(headx,heady,wing2x,wing2y)

    def backChange(self,setvalue):
      if self.bus!=None:
        self.bus.backward=setvalue
        self.update()
    def forwardChange(self,setvalue):
      if self.bus!=None:
        self.bus.forward=setvalue
        self.update()
    def showSettingWindow(self):
      self.settingwindow.show()
    def quitApplication(self):
      self.closeSaving()
      QtGui.qApp.quit()
    def closeSaving(self):
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())
        self.settings.setValue('setsize', self.settingwindow.size())
        self.settings.setValue('setpos', self.settingwindow.pos())
        if self.bus!=None:
          self.settings.setValue('bus', self.busname)
          self.settings.setValue('offset', self.bus.busoffset)
          self.settings.setValue('backward', self.bus.backward)
          self.settings.setValue('forward', self.bus.forward)
    def closeEvent(self, e):
        self.closeSaving()
        e.accept()
    def changeOffset(self,index):
      self.bus.busoffset=self.bus.waypointlist[index][1]
      self.offset=self.bus.busoffset
      #self.showMessage("Monitoring "+self.busname+".\n Alert near "+self.bus.offsetToName(self.bus.busoffset))
      self.update()
    def changeShape(self,index):
        print "changeShape"
        tempoffset=self.offset
        self.settings.shape=self.nameid[index][1]
        self.bus=Bus(self.settings.shape,self.offset,self.backsb.value(),self.forwardsb.value())
        self.busname=self.nameid[index][0]
        self.showMessage("Monitoring "+self.busname+".\n Alert near "+self.bus.offsetToName(self.bus.busoffset))
        self.update()
        self.stopcb.clear()
        for n in self.bus.waypointlist:
            self.stopcb.addItem(n[0])
        stopnamelist=[x[0] for x in self.bus.waypointlist]
        self.stopcb.setCurrentIndex(stopnamelist.index(self.bus.offsetToName(tempoffset)))
    def __init__(self):
        self.bus=None
        self.count=0
        super(Window, self).__init__()
        #need to catch timeout exceptions etc...
        self.settings = QtCore.QSettings('busSettings.ini', QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)    # File only, no fallback to registry or or.
        # Initial window size/pos last saved if available
        #self.resize(400, 300)
        #self.setGeometry(200, 200,500*self.bus.xfactor,500)
        self.resize(self.settings.value('size', QtCore.QSize(350, 500)))
        self.move(self.settings.value('pos', QtCore.QPoint(200, 200)))
        self.offset=int(self.settings.value('offset',89))
        self.busname=(self.settings.value('bus',None))
        self.setWindowTitle(u"busLocator map")
        self.show()
#-------------------basic menu item------------------
        self.settingAction = QtGui.QAction(u"setting", self,
                triggered=self.showSettingWindow)
        self.minimizeAction = QtGui.QAction(u"hide", self,
                triggered=self.hide)
        self.restoreAction = QtGui.QAction(u"show", self,
                triggered=self.showNormal)
        self.quitAction = QtGui.QAction(u"exit", self,
                triggered=self.quitApplication)
        #add menu
        self.trayIconMenu = QtGui.QMenu(self)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.settingAction)
        self.trayIconMenu.addAction(self.quitAction)
        #self.trayIconMenu.clear()
        #self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
#-------------------basic menu end------------------
#-------------------icon------------------
        self.icon=QtGui.QIcon(":/images/bus.ico")
        self.trayIcon.setIcon(self.icon)
        #tooltip do not work on both ubuntu and win
        #self.trayIcon.setToolTip("tooltip")
        self.trayIcon.show()
        self.trayIcon.activated.connect(
            self.iconActivated)

        self.nameid=Bus.getRouteIDs()
        #self.nameid=Bus.getActiveRoute()
        self.names=[x[0] for x in self.nameid]
        self.nametoid=dict(self.nameid)
        #print self.busname
        #print self.nameid
        self.backsb=QtGui.QSpinBox()
        self.backsb.setRange(0,25)
        self.backsb.valueChanged[int].connect(self.backChange)
        self.backsb.setValue(int(self.settings.value('backward',10)))
        self.forwardsb=QtGui.QSpinBox()
        self.forwardsb.setRange(0,25)
        self.forwardsb.valueChanged[int].connect(self.forwardChange)
        self.forwardsb.setValue(int(self.settings.value('forward',10)))
        self.sbGroup=QtGui.QWidget()
        self.sblayout=QtGui.QHBoxLayout()
        self.sblayout.setSpacing(0)
        self.sblayout.addWidget(QtGui.QLabel("backward:"))
        self.sblayout.addWidget(self.backsb)
        self.sblayout.addWidget(QtGui.QLabel("forward:"))
        self.sblayout.addWidget(self.forwardsb)
        self.sbGroup.setLayout(self.sblayout)

        self.settingwindow=QtGui.QWidget()
        cb=QtGui.QComboBox()
        self.stopcb=QtGui.QComboBox()
        self.stopcb.currentIndexChanged.connect(self.changeOffset)
        for n in self.names:
          cb.addItem(n)
        cb.currentIndexChanged.connect(self.changeShape)
        if self.busname in self.nametoid:
          ind=self.names.index(self.busname)
          cb.setCurrentIndex(ind)
          self.changeShape(ind)


        toprow=QtGui.QGroupBox("Please select route")
        toplayout=QtGui.QFormLayout()
        toplayout.addRow(QtGui.QLabel("Route:"),cb)
        toprow.setLayout(toplayout)
        botrow=QtGui.QGroupBox("Route detail:")
        botlayout=QtGui.QFormLayout()
        botlayout.addRow(QtGui.QLabel("Stop to be alert:"),self.stopcb)
        botlayout.addRow(QtGui.QLabel("Fine adjustment:"),self.sbGroup)
        #botlayout.addRow([QtGui.QLabel("backward:"),self.backsb,QtGui.QLabel("forward:"),self.forwardsb])
        botrow.setLayout(botlayout)
        slayout=QtGui.QVBoxLayout()
        slayout.addWidget(toprow)
        slayout.addWidget(botrow)
        self.settingwindow.setLayout(slayout)
        self.settingwindow.setWindowTitle(u"busLocator Setting")
        self.settingwindow.resize(self.settings.value('setsize',
          QtCore.QSize(288,134)))
        self.settingwindow.move(self.settings.value('setpos', QtCore.QPoint(566, 202)))
        if self.busname not in self.nametoid:
          self.settingwindow.show()
          self.settingwindow.setFocus()
          cb.setCurrentIndex(0)
          self.changeShape(0)
        else:
          #self.bus=Bus(self.nametoid[self.busname],self.offset,self.backsb.value(),self.forwardsb.value())
          #self.showMessage("Monitoring "+self.busname+".\n Alert near "+self.bus.offsetToName(self.bus.busoffset))
        #if self.busname in self.nametoid:
          stopnamelist=[x[0] for x in self.bus.waypointlist]
          self.stopcb.setCurrentIndex(stopnamelist.index(self.bus.offsetToName(self.bus.busoffset)))
    

        
        if len(self.bus.shape)!=0:
          self.bus.locateBus()
        self.mouse=None


        self.timer=QtCore.QTimer()
        self.timer.timeout.connect(self.doWork)
        self.timer.start(8000)

    def showMessage(self,message):
        icon = QtGui.QSystemTrayIcon.MessageIcon()
        #icon=QtGui.QSystemTrayIcon.Information
        self.trayIcon.showMessage(
            u'bus coming',message, icon,2000)
    def mousePressEvent(self, event):
      self.mouse=event.pos()
      self.update()
    def paintEvent(self,event):
      qp=QtGui.QPainter()
      qp.begin(self)
      self.drawDetails(event,qp)
      qp.end()
    def drawDetails(self,event,qp):
      if len(self.bus.shape)==0:
        return
      size=self.size()
      w=size.width()
      h=size.height()
      wid=min(h,w/self.bus.xfactor)
      margine=int(wid*0.05)
      if self.mouse!=None:
        t=self.mouse.toTuple()
        qp.setPen(QtGui.QColor(168,34,3))
        qp.setFont(QtGui.QFont('Decorative', 10))
        qp.drawText(event.rect(), QtCore.Qt.AlignTop, "Offset: %s. Stop: %s"% (str(self.bus.scalemapLoopupWaypoint(margine,wid,t)),self.bus.scalemapLoopupStopName(margine,wid,t)))
      monitorl=self.bus.busoffset-self.bus.backward
      if monitorl<0:
        monitorl+=len(self.bus.route)
      monitorr=self.bus.busoffset+self.bus.forward
      if monitorr>len(self.bus.route):
        monitorr-=len(self.bus.route)
      pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine)
      qp.setPen(pen)
      for i in range(len(self.bus.route)-1):
        if i>=monitorl and i<monitorr:
          continue
        if (i>=monitorl or i<monitorr ) and monitorl>monitorr:
          continue
        cordi=self.bus.route[i]
        nx,ny=self.bus.scalemap(margine,wid,cordi)
        cordi2=self.bus.route[i+1]
        nx2,ny2=self.bus.scalemap(margine,wid,cordi2)
        qp.drawLine(nx,ny,nx2,ny2)
        #print nx,ny,nx2,ny2
      pen = QtGui.QPen(QtCore.Qt.green, 2, QtCore.Qt.SolidLine)
      qp.setPen(pen)
      if monitorl<monitorr:
        for i in range(monitorl,monitorr):
          cordi=self.bus.route[i]
          nx,ny=self.bus.scalemap(margine,wid,cordi)
          cordi2=self.bus.route[i+1]
          nx2,ny2=self.bus.scalemap(margine,wid,cordi2)
          qp.drawLine(nx,ny,nx2,ny2)
      else:
        for i in range(0,monitorr):
          cordi=self.bus.route[i]
          nx,ny=self.bus.scalemap(margine,wid,cordi)
          cordi2=self.bus.route[i+1]
          nx2,ny2=self.bus.scalemap(margine,wid,cordi2)
          qp.drawLine(nx,ny,nx2,ny2)
        for i in range(monitorl,len(self.bus.route)-1):
          cordi=self.bus.route[i]
          nx,ny=self.bus.scalemap(margine,wid,cordi)
          cordi2=self.bus.route[i+1]
          nx2,ny2=self.bus.scalemap(margine,wid,cordi2)
          qp.drawLine(nx,ny,nx2,ny2)
        #print nx,ny,nx2,ny2
      #dotpen = QtGui.QPen(QtCore.Qt.magenta, 5, QtCore.Qt.SolidLine)
      #qp.setPen(dotpen)
      #for cordi in self.bus.ol:
      #  nx,ny=self.bus.scalemap(margine,wid,self.bus.route[cordi])
      #  qp.drawPoint(nx,ny)

      dotpen = QtGui.QPen(QtCore.Qt.blue, 6, QtCore.Qt.SolidLine)
      qp.setPen(dotpen)
      for cordi in self.bus.co:
        nx,ny=self.bus.scalemap(margine,wid,cordi)
        qp.drawPoint(nx,ny)
      dotpen = QtGui.QPen(QtCore.Qt.red, 4, QtCore.Qt.SolidLine)
      qp.setPen(dotpen)
      for cordi in self.bus.buses:
        #print nx,ny
        nx,ny=self.bus.scalemap(margine,wid,cordi[:2])
        self.drawBus(nx,ny,cordi[2],qp)
        #qp.drawPoint(nx,ny)
      
    def doWork(self):
      if len(self.bus.shape)==0:
        return
      self.count+=1
      info,wayp=self.bus.locateBus()
      numbus=len(wayp)
      self.menu=[]
      self.trayIconMenu.clear()
      for i in range(numbus):
        menuitem= QtGui.QAction(info[i]+":"+str(wayp[i]), self)
        self.trayIconMenu.addAction(menuitem)
        if -self.bus.backward<wayp[i] and wayp[i]<self.bus.forward:
          self.showMessage(str(wayp))
      self.trayIconMenu.addAction(self.restoreAction)
      self.trayIconMenu.addAction(self.minimizeAction)
      self.trayIconMenu.addAction(self.settingAction)
      self.trayIconMenu.addAction(self.quitAction)
      self.update()
      if self.count>3600/8:
        self.quitApplication()

    def iconActivated(self, reason):
        if reason in (QtGui.QSystemTrayIcon.Trigger,
                      QtGui.QSystemTrayIcon.DoubleClick):
          if self.isHidden():
            self.showNormal()
          else:
            self.hide()
            
if __name__ == '__main__':

    import sys
    signal.signal(signal.SIGINT,signal.SIG_DFL)
    app = QtGui.QApplication.instance()
    standalone=app is None
    if standalone:
      app=QtGui.QApplication(sys.argv)
    QtGui.QApplication.setQuitOnLastWindowClosed(False)

    window = Window()

    if standalone:
      sys.exit(app.exec_())
