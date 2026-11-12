"""y=0 sections of both v19 pumps (sliced from the v19 assembly STEPs) + floating-ring detail."""
import numpy as np, cadquery as cq
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import Rectangle
names=["body","cartridge","endcap","lip_seal","brg1","brg2","brg3","circlip","spacer","wave_spring","locknut","shaft","impeller",
       "inducer","pin1","pin2","nose_nut","dowel1","dowel2","carrier","ring"]
col={"body":"#c3c6cc","cartridge":"#aeb2b9","endcap":"#aeb2b9","lip_seal":"#e6d34f","brg1":"#7fa6d8","brg2":"#7fa6d8","brg3":"#7fa6d8",
     "circlip":"#555","spacer":"#9a9a9a","wave_spring":"#79b97c","locknut":"#777","shaft":"#8e939b","impeller":"#4a6fb5","inducer":"#2e8fd0",
     "pin1":"#c0392b","pin2":"#c0392b","nose_nut":"#c8963c","dowel1":"#c0392b","dowel2":"#c0392b","carrier":"#6f7580","ring":"#f1d27a"}
def sec(shape, plane_angle=0.0):
    rot=shape.rotate((0,0,0),(0,0,1),-plane_angle).rotate((0,0,0),(1,0,0),90)
    try: faces=cq.Workplane().add(rot).section(0.0).faces().vals()
    except Exception: return [],[]
    T,S=[],[]
    for f in faces:
        v,t=f.tessellate(0.01,0.1); P=[(p.x,-p.y) for p in v]; T+=[[P[a],P[b],P[c]] for a,b,c in t]
        for e in f.Edges(): S.append([(p.x,-p.y) for p in (e.positionAt(u) for u in np.linspace(0,1,30))])
    return T,S
data={}
for V in ("HTP","IPA"):
    sol=cq.importers.importStep(f"pump_assembly_{V}_v19.step").solids().vals()
    assert len(sol)==len(names), len(sol)
    data[V]={n:sec(s) for n,s in zip(names,sol)}
    data[V+"_dow"]={n:sec(s,110.0) for n,s in zip(names,sol) if n in ("body","cartridge","dowel1")}   # plane through dowel 1
fig=plt.figure(figsize=(18,10.5))
axs=[fig.add_axes([0.03,0.08,0.27,0.84]),fig.add_axes([0.32,0.08,0.27,0.84]),fig.add_axes([0.62,0.40,0.36,0.52]),fig.add_axes([0.62,0.08,0.17,0.26])]
def draw(ax,d,lw):
    for n,(T,S) in d.items():
        z=3 if n in ("ring","carrier","dowel1","dowel2") else 2
        if T: ax.add_collection(PolyCollection(T,facecolors=col[n],edgecolors=col[n],linewidths=0.2,zorder=z))
        if S: ax.add_collection(LineCollection(S,colors="k",linewidths=lw,zorder=z+0.5))
for ax,V in zip(axs[:2],("HTP","IPA")):
    draw(ax,data[V],0.35); ax.set_aspect("equal"); ax.set_xlim(-42,42); ax.set_ylim(-86,29); ax.axvline(0,color="k",lw=0.4,ls="--")
    ax.set_title(f"{V} pump v19, y = 0 section",fontsize=11); ax.set_xlabel("x (mm)")
    ax.add_patch(Rectangle((-14,-11),28,12,fill=False,ec="#c0392b",lw=1.1,ls="--",zorder=6))
axs[0].set_ylabel("z (mm), +z = inlet")
axs[0].text(-41,24,"HTP: inducer Ø15 (3 blades),\ndiffuser throats Ø1.95, 1/4\" stubs",fontsize=8.5)
axs[1].text(-41,24,"IPA: inducer Ø12 (2 blades),\ndiffuser throats Ø1.16, 3/16\" stubs",fontsize=8.5)
ax=axs[2]; draw(ax,data["HTP"],0.8); ax.set_aspect("equal"); ax.set_xlim(-14,14); ax.set_ylim(-11,1.2); ax.axvline(0,color="k",lw=0.4,ls="--")
ax.set_title("Detail (both variants): floating ring seal",fontsize=10)
A=dict(fontsize=8.5,arrowprops=dict(arrowstyle="-",lw=0.6),zorder=7,bbox=dict(fc="white",ec="none",alpha=0.85,pad=1))
ax.annotate("PCTFE ring Ø16.0, bore Ø10.050 cold\nnose r 5.50–5.90 on seat",(-6.5,-4.4),(-13.6,-2.0),**A)
ax.annotate("316L carrier, press-fit Ø26 n6\nbore Ø16.2 (float ±0.1), Ø10.6 hole,\nfloor = lapped seat",(-10.5,-5.0),(-13.6,-7.6),**A)
ax.annotate("Varilip 10×24×7",(-9,-10),(-13.6,-10.1),**A)
ax.annotate("fins capture ring (1.5 play)",(7,-1.2),(6.0,-1.2),**A)
ax.annotate("bleed groove → Ø1.8 → tank",(9.5,-7.3),(7.8,-7.4),**A)
ax=axs[3]; draw(ax,data["HTP_dow"],0.7); ax.set_aspect("equal"); ax.set_xlim(20,36); ax.set_ylim(-9,5)
ax.set_title("Section through dowel at 110°",fontsize=9); ax.set_xlabel("r (mm)")
ax.annotate("Ø3 m6 dowel locates body\non cartridge (r 28)",(28,-2),(20.5,3.4),**A)
fig.text(0.81,0.30,"v19 changes vs v18",fontsize=10,weight="bold")
fig.text(0.81,0.08,("1. 2× Ø3 dowels at r 28 (110° round,\n   290° radial slot) locate body on\n   cartridge: inducer tip 0.10 now held\n"
 "2. Floating ring seal replaces bushing\n   (±0.1 float, nose on seat)\n3. Ports: bleed Ø1.8 inside its groove;\n   weep and bleed M5 on bosses\n\n"
 "Checked: no interference (thread and\nface contacts only); inducer 0.10,\nfront 0.386, back 0.30, ring 0.025."),fontsize=8.5,family="monospace")
plt.savefig("pump_v19_sections.png",dpi=140); print("ok")
