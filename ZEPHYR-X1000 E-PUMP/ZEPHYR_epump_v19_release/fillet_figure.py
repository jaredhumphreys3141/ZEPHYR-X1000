import numpy as np, cadquery as cq, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
def sec(shape,z):
    T=[]
    for f in cq.Workplane().add(shape).section(z).faces().vals():
        v,t=f.tessellate(0.002,0.05); P=[(p.x,p.y) for p in v]; T+=[[P[a],P[b],P[c]] for a,b,c in t]
    return T
fig,axs=plt.subplots(1,2,figsize=(15,7.4))
for ax,(V,D,z) in zip(axs,(("HTP",15,11.0),("IPA",12,11.0))):
    a=cq.importers.importStep(f"/home/claude/rel/CAD/rotor_v17/inducer_{V}_{D}mm_v17.step").val()
    b=cq.importers.importStep(f"inducer_{V}_{D}mm_v19.step").val()
    ax.add_collection(PolyCollection(sec(b,z),facecolors="#e07b39",edgecolors="#e07b39",lw=0.2,label="v19 (R0.4 root fillets)"))
    ax.add_collection(PolyCollection(sec(a,z),facecolors="#2e8fd0",edgecolors="#2e8fd0",lw=0.2,alpha=0.9,label="v17 (sharp root)"))
    ax.set_aspect("equal"); r=D/2+0.3; ax.set_xlim(-r,r); ax.set_ylim(-r,r)
    ax.set_title(f"{V} inducer, section at z = {z} (orange = added fillet)",fontsize=10); ax.legend(loc="lower left",fontsize=8)
    ax.set_xlabel("x (mm)")
fig.text(0.04,0.015,"The z-plane cuts the low-angle blades obliquely, so each R0.4 fillet looks stretched along the hub (~1/sin β, 3-4x).\nMeasured normal to the blade, thickness matches a true R0.4 arc to 0.001 mm from 0.1 mm above the hub.",fontsize=9)
plt.tight_layout(rect=(0,0.07,1,0.97)); plt.savefig("inducer_v19_root_fillets.png",dpi=140); print("ok")
