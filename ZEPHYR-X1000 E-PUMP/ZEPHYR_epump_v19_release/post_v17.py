"""Post-process a raw generator inducer exactly as build_v17.py does (pump frame, Ø5 bore, half-holes, chamfers)."""
import sys, json, math, cadquery as cq
V,raw,out=sys.argv[1],sys.argv[2],sys.argv[3]
cyl=lambda d,z0,z1,x=0,y=0: cq.Workplane("XY").workplane(offset=z0).center(x,y).circle(d/2).extrude(z1-z0).val()
PIN_R,PIN_ANG,HOLE_D,IND_HOLE=2.5,(0.0,180.0),1.02,3.5
d={x["name"]:x for x in json.load(open("/home/claude/rel/data/inducer_designs_v16.json"))}[V]; L=d["axial_length_mm"]
ind=cq.importers.importStep(raw).val().rotate(cq.Vector(0,0,0),cq.Vector(1,0,0),180).translate(cq.Vector(0,0,7.15+L+1.0))
zf=7.15+L+1.5
hh=None
for a in PIN_ANG:
    x,y=PIN_R*math.cos(math.radians(a)),PIN_R*math.sin(math.radians(a)); c=cyl(HOLE_D,6.0,7.15+IND_HOLE,x,y); hh=c if hh is None else hh.fuse(c)
ind=ind.cut(cyl(5.0,6.0,zf+1)).cut(hh)
for a in PIN_ANG:
    x,y=PIN_R*math.cos(math.radians(a)),PIN_R*math.sin(math.radians(a))
    ind=ind.cut(cq.Solid.makeCone(HOLE_D/2,0,HOLE_D/2/math.tan(math.radians(59)),pnt=cq.Vector(x,y,7.15+IND_HOLE),dir=cq.Vector(0,0,1)))
for z,s in ((7.14,1),(zf+0.01,-1)):
    ind=ind.cut(cq.Solid.makeCone(2.8,2.5,0.3,pnt=cq.Vector(0,0,z),dir=cq.Vector(0,0,s)))
ind=ind.cut(cq.Workplane("XY").workplane(offset=zf).rect(40,40).extrude(5).val())   # trim LE root-fillet bulge flush with the nut seat face
print(V,"valid",ind.isValid(),"solids",len(ind.Solids()),"mass %.3f g"%(ind.Volume()*7.8e-3))
cq.exporters.export(cq.Workplane().add(ind),out)
