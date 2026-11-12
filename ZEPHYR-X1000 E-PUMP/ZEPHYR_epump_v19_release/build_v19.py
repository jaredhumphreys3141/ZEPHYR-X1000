"""ZEPHYR e-pump v19 release builder (HTP + IPA). v19 = v18 casing + v17 rotor with:
 1. body-cartridge radial location: 2x Ø3 m6 dowels at r 28, 110 deg (round hole) and 290 deg (slot in body, radial),
    reamed in the same setups as the shroud bore (body) and the bearing bores (cartridge)
 2. floating ring seal replaces the PCTFE throttle bushing: one-piece PCTFE ring in a 316L carrier, float ±0.1,
    nose r 5.50-5.90 over a Ø10.6 hole, no stakes (impeller fins capture the ring)
 4. inducers: R0.4 blade-root fillets (inducer_cad_fillet.py), LE root bulge trimmed flush with the nut seat
 3. ports: bleed Ø1.8 kept inside the 2.0 bleed groove (ring<->lip seal); weep M5 moved out to r 13-19 on a boss
Frame: +Z toward inlet, impeller back plate z=0."""
import sys, json, math, itertools, cadquery as cq
V=sys.argv[1]; REL="/home/claude/rel/CAD/"
rev=lambda pts: cq.Workplane("XZ").polyline(pts).close().revolve(360,(0,0,0),(0,1,0)).val()
cyl=lambda r,z0,z1,x=0,y=0: cq.Workplane("XY").workplane(offset=z0).center(x,y).circle(r).extrude(z1-z0).val()
names=["body","cartridge","endcap","bushing_v18","lip_seal_10x24x7","brg_708_front1","brg_708_front2","brg_708_rear",
       "circlip_DIN472-22","spacer_25","wave_spring","locknut_M8x0.75","shaft","impeller","inducer","pin_1","pin_2","nose_nut"]
sol=cq.importers.importStep(REL+f"casing_v18/pump_assembly_{V}_v18.step").solids().vals()
assert len(sol)==18
P=dict(zip(names,sol)); del P["bushing_v18"]
P["inducer"]=cq.importers.importStep(f"inducer_{V}_{15 if V=='HTP' else 12}mm_v19.step").val()   # v19: R0.4 blade-root fillets
P["circlip_DIN472-22"]=rev([(10.4,-33.0),(11.5,-33.0),(11.5,-32.0),(10.4,-32.0)])   # v18 envelope was 0.1 oversize into its groove
DOW=[(110,"round"),(290,"slot")]
pos=lambda a,r=28.0:(r*math.cos(math.radians(a)), r*math.sin(math.radians(a)))
body=P["body"]; cart=P["cartridge"]
for a,kind in DOW:
    x,y=pos(a)
    if kind=="round": body=body.cut(cyl(1.5,-2.31,1.7,x,y))
    else:   # radial slot: 3.0 wide, 3.6 long along the radius
        sl=cq.Workplane("XY").workplane(offset=-2.31).center(x,y).slot2D(3.6,3.0,a).extrude(4.01).val(); body=body.cut(sl)
a=math.radians(50); dx,dy=math.cos(a),math.sin(a)
import sys as _s; _s.path.insert(0,"."); from cartridge_v19b import build as _cart; cart=_cart()   # v19b cartridge: corrected bleed/weep ports + dowel holes
P["body"]=body.clean(); P["cartridge"]=cart.clean()
for i,(a_,k) in enumerate(DOW):
    x,y=pos(a_); P[f"dowel_{i+1}_3x8"]=cyl(1.5,-6.3,1.7,x,y)
FLOAT=0.1; HOLE_R=5.3; N0,N1=5.5,5.9
P["frs_carrier_316L"]=rev([(HOLE_R,-6.3),(13.0,-6.3),(13.0,-2.3),(8.0+FLOAT,-2.3),(8.0+FLOAT,-5.5),(HOLE_R,-5.5)])
P["frs_ring_PCTFE"]=rev([(5.025,-5.3),(8.0,-5.3),(8.0,-3.5),(5.025,-3.5)]).fuse(rev([(N0,-5.5),(N1,-5.5),(N1,-5.3),(N0,-5.3)])).clean()
# ---------------- checks ----------------
rep={"variant":V}
ov=[]
for (a1,s1),(a2,s2) in itertools.combinations(P.items(),2):
    v=s1.intersect(s2).Volume()
    if v>1e-4: ov.append((a1,a2,round(v,4)))
rep["overlaps_mm3"]=ov
g=lambda a,b: round(P[a].distance(P[b]),4)
rep["gaps"]={"inducer tip-body":g("inducer","body"),"impeller front-body":g("impeller","body"),
             "impeller back-cartridge":g("impeller","cartridge"),"ring bore-shaft":g("frs_ring_PCTFE","shaft"),
             "ring nose-carrier seat":g("frs_ring_PCTFE","frs_carrier_316L"),"carrier-impeller":g("frs_carrier_316L","impeller"),
             "nut-body":g("nose_nut","body"),"shaft-carrier hole":g("shaft","frs_carrier_316L")}
r=P["frs_ring_PCTFE"]; c=P["frs_carrier_316L"]
rep["ring_float_clear"]=all(r.translate(v).intersect(c).Volume()<1e-6 for v in ((FLOAT-0.001,0,0),(0,-(FLOAT-0.001),0),(0.07,0.07,0)))
lift=r.translate((0,0,1.5)); rep["ring_lift_1.5: gap_to_impeller, bottom_z"]=(round(lift.distance(P["impeller"]),3), round(lift.BoundingBox().zmin,2))
rep["nose_on_seat_margin_at_full_float_mm"]=round(N0-FLOAT-HOLE_R,3)
rep["masses_g"]={k:round(s.Volume()*d*1e-3,1) for k,s,d in [("body",P["body"],8.0),("cartridge",P["cartridge"],8.0),("carrier",c,8.0),("ring",r,2.13)]}
print(json.dumps(rep,indent=1))
json.dump(rep,open(f"check_v19_{V}.json","w"),indent=1)
cols={"body":(0.76,0.78,0.80),"cartridge":(0.69,0.71,0.73),"endcap":(0.69,0.71,0.73),"shaft":(0.56,0.58,0.61),"impeller":(0.29,0.44,0.71),
      "inducer":(0.18,0.56,0.85),"nose_nut":(0.78,0.59,0.24),"frs_ring_PCTFE":(0.95,0.85,0.55),"frs_carrier_316L":(0.49,0.51,0.55),
      "lip_seal_10x24x7":(0.90,0.83,0.31)}
asm=cq.Assembly(name=f"ZEPHYR_pump_{V}_v19")
for k,s in P.items():
    asm.add(s,name=k,color=cq.Color(*cols.get(k,(0.5,0.65,0.85) if "brg" in k else (0.75,0.3,0.25) if ("pin" in k or "dowel" in k) else (0.6,0.6,0.6))))
asm.save(f"pump_assembly_{V}_v19.step")
for k in ("body","cartridge","frs_carrier_316L","frs_ring_PCTFE"):
    fn = f"pump_body_{V}_v19.step" if k=="body" else f"{k}_v19.step" if k!="cartridge" else "cartridge_v19.step"
    cq.exporters.export(cq.Workplane().add(P[k]),fn)
