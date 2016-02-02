#!/usr/bin/env python
# -*- coding: utf-8 -*-
def sdistance(vec1,vec2):
  return (vec1[0]-vec2[0])**2+(vec1[1]-vec2[1])**2*0.4695
import os
import math
from math import cos
from math import pi
import urllib2
from BeautifulSoup import BeautifulSoup
import re
from time import sleep
def angDiff(a1,a2):
  y=abs(a1-a2)
  if y>180:
    y=360-y
  return y
def angleToNorth(x,y):
    t=math.atan2((y[1]-x[1])*0.4695,(y[0]-x[0]))*180/math.pi
    if y[1]-x[1]<0:
        t+=360
    return t

def pointLineDistance(x,y,z):
  return 0.6852211268019088*abs((z[0]-y[0])*(y[1]-x[1])-(y[0]-x[0])*(z[1]-y[1]))/math.sqrt((z[0]-y[0])**2+
(z[1]-y[1])**2*0.469528)

def dot(x,y,z):
   return (y[1]-x[1])*(z[1]-x[1])+(y[0]-x[0])*(z[0]-x[0])

def pointLineSegDistance(x,y,z):
    if dot(y,z,x)<0:
       routecheck=math.sqrt(sdistance(x,y))*111222 
    elif dot(z,x,y)<0:
       routecheck=math.sqrt(sdistance(z,x))*111222
    else:
       routecheck=pointLineDistance(x,y,z)*111222
    return routecheck

#import socket
def argmin(li):
  minv=li[0]
  minpointer=0
  for i in xrange(len(li)):
    if li[i]<minv:
      minv=li[i]
      minpointer=i
  return minpointer


class Bus(): 
    name=[]
    buses=[]
    co=[]
    header = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:16.0) Gecko/20100101 Firefox/16.0','Accept':'''text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8''','Accept-Language':'''en-us,en;q=0.5''','Connection':'''keep-alive'''} 
    @staticmethod
    def getActiveRoute():
        nameid=Bus.getRouteIDs()
        # 0:bus id? needs to be confirmed
        # 1:lattitude
        # 2:jingdu
        # 3:shapeid
        # 4:angle 0 as north
        # 5:image
        # 6:Bus name
        # 7:shape
        # 8:long name+time
        shapeidlist=[Bus.getRouteShapeID(busid) for name,busid in nameid]
        shapeid=''
        for s in shapeidlist:
          shapeid+=','+s

        req =urllib2.Request(url='''http://pullman.mapstrat.com/nextvehicle/BusLocator.axd?&ShapeIDs='''+shapeid)
        file=urllib2.urlopen(req).read()
        p=re.compile("SmiTransitVehicleLocation\(([^,]*?),(.*?),(.*?),(.*?),([^,]*?),([^,]*?),([^,]*?),([^,]*?),([^,]*?)\)")
        busdata=p.findall(file)
        return [(x[6],int(x[3])) for x in busdata]
    @staticmethod
    def getRouteShapeID(busid):
        '''get route details route'''
        req =urllib2.Request(url='''http://pullman.mapstrat.com/nextvehicle/RouteDetails.axd?Shape='''+busid)
        file=urllib2.urlopen(req).read()
        p=re.compile("SmiTransitWaypoint\(([0-9]*?),\'([^,]*?)\',([^,]*?),([^,]*?),([^,]*?),([^,]*?), ([^,]*?), \'smi_pullman\'\)")
        data=p.search(file).group()
        s=re.compile("SmiTransitShapePoint\(([0-9]*?),\'([^,]*?)\',([^,]*?),([^,]*?),([^,]*?)\)")
        shapeidlist=data[6]
        print shapeidlist
        return shapeidlist
    @staticmethod
    def getRouteIDs():
        req =urllib2.Request(url='''http://pullman.mapstrat.com/nextvehicle/Map.aspx''')#,headers = self.header)
        file=urllib2.urlopen(req).read()
        bb=BeautifulSoup(file)
        bl=bb.html.body.form.findAll(igtag="Shape")
        routelist=[(i.text,i['igdatakey']) for i in bl]
        #return empty list if none found
        print routelist
        return routelist

    def setAnglist(self):
        self.anglist=[angleToNorth(self.route[i],self.route[i+1])
                for i in xrange(len(self.route)-1)]
        return
    def getCloseCordinate(self,point,angle):
          '''return pointer in self.route, -1 if not found'''
          dis=[self.sdistance(point,xx) for xx in self.route[:-1]]
          wayp=argmin(dis)
          #wayp is not possible to be the last element (same as first)
          # -1 means the second last element
          nd=min(pointLineSegDistance(point,self.route[wayp],self.route[wayp+1]),
          pointLineSegDistance(point,self.route[wayp],self.route[:-1][wayp-1]))
          #check if off grid
          #print nd
          if nd>20:
            return -1
          if wayp in self.ol:
              points=set()
              for line in self.ol[wayp]:
                  if angDiff(self.anglist[line],angle)<30:
                      #found the line segment
                      points.add(line)
                      points.add(line+1)
              #print "available points",points,"original point",wayp
              #print "angles",[self.anglist[x] for x in points],"original point",self.anglist[wayp],self.anglist[(wayp-1)%len(self.route)],"actual angle",angle
              if len(points)!=0:
                  #return the minimum distance
                  return min(points,key=lambda
                          p:sdistance(point,self.route[p]))
          #if not in other line segments, return the original result
          return wayp

    def initRouteOutlier(self):
        self.ol=dict()
        #not look at 5 to 6 nearest neighbor
        cutoff=5
        #look for point to distance within 15 meters 
        metercutoff=15
        for i,x in enumerate(self.route):
          for j in xrange(len(self.route)-1):
            k=j+1
            if i<cutoff:
              if k>len(self.route)+i-cutoff:
                continue
            if i>len(self.route)-cutoff:
              if j<len(self.route)-i:
                continue
            if abs(i-j)<cutoff or abs(-len(self.route)+j-i)<cutoff:
              continue
            y=self.route[j];z=self.route[k];
            if pointLineSegDistance(x,y,z)<metercutoff:
                if i in self.ol:
                    #note j stands for a line segment (j,k)
                    self.ol[i].append(j)
                else:
                    self.ol[i]=[j]
        l=list(self.ol)
        l.sort()
        #print l
        return

    def __init__(self,busid=None,busoffset=89,backward=10,forward=10):
        #default to work at webster for Express 2
        self.forward=forward
        self.backward=backward
        self.filesaveflag=False
        self.busoffset=busoffset
        self.xfactor2=0.4695
        self.xfactor=0.68522
        self.home=os.path.expanduser('~/')
        #os.chdir(self.home)
        #if os.path.isfile(self.home+'busoffset.dat'):
        #  with open(self.home+'busoffset.dat') as f:
        #    self.busoffset=int(f.readline())
        #else:
        #  with open(self.home+'busoffset.dat','w') as f:
        #    f.write(str(self.busoffset))

        self.shape=[]
        if busid==None:
            self.shape=[]
            bl=Bus.getRouteIDs()
            #each route has an associate shape number
            #need to specify shape number to get route details
            for i,j in bl:
              if i.find("Express 2")!=-1:
                self.shape.append(j)
                print 'found Express 2'
                continue
              if i.find("Exp 2")!=-1:
                self.shape.append(j)
                print 'found Exp 2'
        else:
            self.shape=[str(busid)]
        #print busid
        print self.shape
        if len(self.shape)==0:
          return
            
        self.getCoordinate()
        if len(self.route)==0:
          return
        #print self.file
        xlist=[x[1] for x in self.route]
        ylist=[x[0] for x in self.route]
        self.xmin=min(xlist)
        self.ymin=min(ylist)
        self.xmax=max(xlist)
        self.ymax=max(ylist)
        self.ywidth=self.ymax-self.ymin
        self.xfactor=cos((self.ymin+self.ymax)/2.*pi/180.)
        self.xfactor2=self.xfactor**2
        self.xwidth=(self.xmax-self.xmin)/self.xfactor
        #exit(0)
        self.initRouteOutlier()
        self.setAnglist()

    def scalemapLoopupWaypoint(self,margine,w,data):
      x=data[0]
      y=data[1]
      nx=(x-margine)*self.xwidth/(w-2*margine)+self.xmin
      ny=self.ymax-(y-margine)*self.ywidth/(w-2*margine)
      return self.lookupWaypoint((ny,nx))

    def scalemapLoopupStopName(self,margine,w,data):
      x=data[0]
      y=data[1]
      nx=(x-margine)*self.xwidth/(w-2*margine)+self.xmin
      ny=self.ymax-(y-margine)*self.ywidth/(w-2*margine)
      return self.lookupStopName((ny,nx))

    def offsetToName(self,offset):
      dis=[self.sdistance(self.route[offset],xx) for xx in self.co]
      return self.name[argmin(dis)]
      
    def lookupStopName(self,x):
      dis=[self.sdistance(x,xx) for xx in self.co]
      return self.name[argmin(dis)]

    def lookupWaypoint(self,x):
      dis=[self.sdistance(x,xx) for xx in self.route]
      return argmin(dis)
    def scalemap(self,margine,w,data):
      x=data[1]
      y=data[0]
      return (margine+(w-2*margine)*(x-self.xmin)/self.xwidth,
          margine+(w-margine*2)*(self.ymax-y)/self.ywidth)
      
    def sdistance(self,vec1,vec2):
      #return square distance on small map
      return (vec1[0]-vec2[0])**2+(vec1[1]-vec2[1])**2*self.xfactor2
    #def sdistance(self,vec):
    #  #return square distance on small map
    #  return vec[0]**2+vec[1]**2*self.xfactor2

    def main(self):
        #Notify.init("new-bus-notify")
        for i in xrange(400):
          info,wayp=self.locateBus()
          print info,wayp
          sleep(8)
    def getCoordinate(self):
        '''get coordinates for express route
        set up name co waypoints waypointmap etc.
        '''
        #saved
        self.route=None
        self.waypointlist=None
        if self.filesaveflag:
          if os.path.isfile('co.dat'):
            with open('co.dat') as f:
              self.route=[[float(x) for x in ln.split()] for ln in f]
            data=None
        #data record all bus stop information
        data=[]
        for s in self.shape:
          req =urllib2.Request(url='''http://pullman.mapstrat.com/nextvehicle/RouteDetails.axd?Shape='''+s,headers = self.header)
          self.file=urllib2.urlopen(req).read()
          #print self.file
          p=re.compile("SmiTransitWaypoint\(([0-9]*?),\'([^,]*?)\',([^,]*?),([^,]*?),([^,]*?),([^,]*?), ([^,]*?), \'smi_pullman\'\)")
          tempdata=p.findall(self.file)
          data.extend(tempdata)
          if self.route==None:
            s=re.compile("SmiTransitShapePoint\(([0-9]*?),\'([^,]*?)\',([^,]*?),([^,]*?),([^,]*?)\)")
            waypoints=s.findall(self.file)
            self.route=[[float(x[2]),float(x[3])] for x in waypoints]
            if self.filesaveflag:
              with open('co.dat','w') as f:
                f.writelines([x[2]+' '+x[3]+'\n' for x in waypoints])
        data=list(set(data)) #remove duplicates
        self.name=[x[1].strip() if x[1].find('Please')==-1 else x[1][:x[1].find('Please')-1].strip() for x in data]
        self.co=[((float(x[2]),float(x[3]))) for x in data]
        #shape id is used to get bus information instead of route information
        shapeidlist=set([x[6] for x in data])
        self.shapeid=''
        for s in shapeidlist:
          self.shapeid+=','+s
        if self.filesaveflag:
          if os.path.isfile('waypoints.dat'):
            with open('waypoints.dat') as f:
              wl=f.read().splitlines()
            wl=[x.split(',') for x in wl]
            self.waypointlist=[[x[0],int(x[1])] for x in wl]
            self.waypointmap=dict(self.waypointlist)
            for i in self.name:
              if i not in self.waypointmap:
                #waypoints are updated, we need to update the file
                self.waypointlist=None
        if self.waypointlist==None:
          #set the stop value at the closest one in the route
          self.waypointlist=[[self.name[i],argmin([self.sdistance(self.co[i],xx) for xx in self.route])] for i in xrange(len(self.co))]
          self.waypointlist.sort(key=lambda s:s[1])
          if self.filesaveflag:
            with open('waypoints.dat','w') as f:
              f.writelines([x[0]+','+str(x[1])+'\n' for x in self.waypointlist])
          self.waypointmap=dict(self.waypointlist)
        #print self.name
        return 1

    def locateBus(self):
        req =urllib2.Request(url='''http://pullman.mapstrat.com/nextvehicle/BusLocator.axd?&ShapeIDs='''+self.shapeid,headers = self.header)
        self.file=urllib2.urlopen(req).read()
        # 0:bus id? needs to be confirmed
        # 1:lattitude
        # 2:jingdu
        # 3:shapeid
        # 4:angle 0 as north
        # 5:image
        # 6:Bus name
        # 7:shape
        # 8:long name+time
        p=re.compile("SmiTransitVehicleLocation\(([^,]*?),(.*?),(.*?),(.*?),([^,]*?),([^,]*?),([^,]*?),([^,]*?),([^,]*?)\)")
        self.busdata=p.findall(self.file)
        self.buses=[(float(x[1]),float(x[2]),float(x[4])) for x in self.busdata]
        info=[x[6]+(BeautifulSoup(x[-1]).span.nextSibling) for x in self.busdata]
        #print self.busdata
        label=''
        retinfo=[]
        debuginfo=[]
        for i in xrange(len(self.busdata)):
          x=self.buses[i][:2];
          ang=float(self.busdata[i][4])
          wayp=self.getCloseCordinate(x,ang)
          if wayp!=-1:
            location=self.lookupStopName(x)
            info[i]+=location
            wp=self.waypointmap[location]
            #brute force approach
            #dis=[self.sdistance(x,xx) for xx in self.route]
            #ayp=argmin(dis)
            ##Merman and valley to Merman and Terre View
            #if (189<wayp and wayp<200) or (51<wayp and wayp<65):
            #  ang=float(self.busdata[i][4])
            #  #going up right
            #  if (0<ang and ang<90):
            #    #numpy
            #    dis=[self.sdistance(x,xx) for xx in (self.route)[189:]]
            #    wayp=argmin(dis)+189
            #  else:
            #    dis=[self.sdistance(x,xx) for xx in (self.route)[52:66]]
            #    wayp=argmin(dis)+52
            #elif (172<wayp and wayp<177) or (99<wayp and wayp<105):
            #  ang=float(self.busdata[i][4])
            #  #going down right
            #  if (90<ang and ang<180):
            #    dis=[self.sdistance(x,xx) for xx in (self.route)[99:105]]
            #    wayp=argmin(dis)+99
            #  else:
            #    dis=[self.sdistance(x,xx) for xx in (self.route)[172:177]]
            #    wayp=argmin(dis)+172
            ##print "%d\t" %wayp,
            nwayp=wayp-self.busoffset
            #normalize between -100 to 100
            length=len(self.route)
            if nwayp>length/2:
              nwayp-=length
            if nwayp<-length/2:
              nwayp+=length
            #wayp=-wayp
            retinfo.append(nwayp)
            debuginfo.append(wayp)
          else:
            info[i]+="offgrid"
            retinfo.append(100)
            debuginfo.append(wayp)
        #print debuginfo
        return (tuple(info),tuple(retinfo))

if __name__ == "__main__":
    indicator = Bus()
    indicator.main()
