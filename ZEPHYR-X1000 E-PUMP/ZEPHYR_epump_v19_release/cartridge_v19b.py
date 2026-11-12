"""Cartridge v19b (bleed boss added under the flange): v18 cartridge rebuilt from case_v18.py geometry with corrected ports + v19 dowel holes.
 bleed (to tank, 50 deg, z -7.3): Ø1.8 drilling r 11.5 -> 27 stays inside the 2.0 bleed groove (z -8.2..-6.4);
        M5 port in the flange r 27..32 (unchanged)
 weep  (overboard, 230 deg, z -16.6): Ø2.0 drilling from the weep cavity (r 9) to r 13, then M5 x 6 deep in a
        Ø8 boss r 13..19, so the thread no longer cuts the lip-seal bore (r 12) or the bearing seat (r 11)
 dowels: Ø3 H7 x 4 deep at r 28, 110 and 290 deg"""
import math, cadquery as cq
z_bw=-2.3; E=5.5; R_OUT,R_C1,R_C2=32.0,16.0,15.0
rev=lambda pts: cq.Workplane("XZ").polyline(pts).close().revolve(360,(0,0,0),(0,1,0)).val()
cyl=lambda r,z0,z1,x=0,y=0: cq.Workplane("XY").workplane(offset=z0).center(x,y).circle(r).extrude(z1-z0).val()
def radial(z,ang,r0,r1,d):
    a=math.radians(ang); dx,dy=math.cos(a),math.sin(a)
    return cq.Solid.makeCylinder(d/2,r1-r0,pnt=cq.Vector(r0*dx,r0*dy,z),dir=cq.Vector(dx,dy,0))
def build():
    prof=[(13.0,z_bw),(R_OUT,z_bw),(R_OUT,z_bw-6.0),(R_C1,z_bw-6.0),(R_C1,-20.0),(R_C2,-20.0),(R_C2,-60.5-E),(11.0,-60.5-E),
          (11.0,-18.0),(9.0,-18.0),(9.0,-15.3),(12.0,-15.3),(12.0,-6.3),(13.0,-6.3)]
    c=rev(prof)
    c=c.fuse(radial(-16.6,230,14.0,19.0,8.0))                                              # weep boss Ø8 to r 19
    c=c.fuse(radial(-7.3,50,20.0,32.0,8.0))                                                # bleed boss Ø8 under the flange (M5 no longer breaks out at z -8.3)
    c=c.cut(cq.Workplane("XY").workplane(offset=z_bw-1.15).circle(23.5).circle(21.5).extrude(1.2).val())   # O-ring 44x1.5
    c=c.cut(cq.Workplane("XY").workplane(offset=-33.1).circle(11.5).circle(10.9).extrude(1.2).val())        # DIN 472-22
    for a in (-10,30,70,170,210,250):
        c=c.cut(cyl(1.65,z_bw-9.0,z_bw+0.1,28*math.cos(math.radians(a)),28*math.sin(math.radians(a))))       # M4 tap drills
    c=c.cut(radial(-7.3,50,11.5,27.5,1.8)).cut(radial(-7.3,50,27.0,R_OUT+1,4.2))          # bleed Ø1.8 + M5 (r 27-32)
    c=c.cut(radial(-16.6,230,8.5,13.5,2.0)).cut(radial(-16.6,230,13.0,19.5,4.2))          # weep Ø2.0 + M5 x 6 (r 13-19)
    for k in range(4):
        a=math.radians(45+90*k); c=c.cut(cyl(0.8,-60.5-E-0.1,-60.5-E+5,13.1*math.cos(a),13.1*math.sin(a)))  # M2 end-cap
    for a in (110,290):
        c=c.cut(cyl(1.5,-6.3,-2.3+0.01,28*math.cos(math.radians(a)),28*math.sin(math.radians(a))))       # dowel holes
    return c.clean()
if __name__=="__main__":
    c=build(); print("valid",c.isValid(),"mass %.0f g"%(c.Volume()*8e-3))
    def runs(ang,r,z0=-20,z1=-2.4):
        z=[z0+k*0.05 for k in range(int((z1-z0)/0.05))]
        v=[not c.isInside(cq.Vector(r*math.cos(math.radians(ang)),r*math.sin(math.radians(ang)),zz)) for zz in z]
        out=[];s=None
        for zz,b in zip(z,v):
            if b and s is None: s=zz
            if not b and s is not None: out.append((round(s,2),round(zz,2))); s=None
        return out
    zb=[-9.4+k*0.05 for k in range(20)]
    print("bleed M5 enclosed below flange:", all(c.isInside(cq.Vector(29.5*math.cos(math.radians(50))+dx, 29.5*math.sin(math.radians(50))+dy, z)) for z in (-9.6,-9.8) for dx,dy in ((0,0),)))
    for ang,r,lab in ((50,29.5,"bleed M5 (r 27-32)"),(50,12.5,"bleed drilling"),(230,12.0,"weep at seal-bore radius"),(230,11.2,"weep at bearing-seat radius"),(230,14,"weep M5")):
        print(f"{lab:28s} ang {ang} r {r}: void z {runs(ang,r)}")
    cq.exporters.export(cq.Workplane().add(c),"cartridge_v19.step")
